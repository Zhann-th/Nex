#!/usr/bin/env python3
"""
NEX CORE DETECTION ENGINE v3.0
Hybrid SIFT-RANSAC + YOLO-World Detection
Works for ANY enrolled object — no hardcoding, no device assumptions.
"""

import cv2
import numpy as np
import time
from datetime import datetime
from pathlib import Path
from collections import deque
from threading import Lock
import json

try:
    import torch
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE QUALITY SCORER
# ─────────────────────────────────────────────────────────────────────────────

class ImageQualityScorer:
    """Scores frames to pick the sharpest from a burst."""

    @staticmethod
    def calculate_sharpness(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    @staticmethod
    def calculate_brightness(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return np.mean(gray)

    @staticmethod
    def calculate_contrast(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return np.std(gray)

    @staticmethod
    def score_image(image):
        sharpness  = ImageQualityScorer.calculate_sharpness(image)
        brightness = ImageQualityScorer.calculate_brightness(image)
        contrast   = ImageQualityScorer.calculate_contrast(image)

        sharpness_score  = min(sharpness / 1000.0 * 100, 100)
        brightness_score = max(0, min(100, 100 - abs(brightness - 125) / 1.25))
        contrast_score   = min(contrast / 80.0 * 100, 100)

        total = (sharpness_score * 0.5 + brightness_score * 0.25 + contrast_score * 0.25)
        return {
            'total': total,
            'sharpness': sharpness_score,
            'brightness': brightness_score,
            'contrast': contrast_score,
            'raw_values': {
                'sharpness': sharpness,
                'brightness': brightness,
                'contrast': contrast,
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# BURST CAPTURE BUFFER
# ─────────────────────────────────────────────────────────────────────────────

class BurstCapture:
    """Keeps a rolling buffer of recent frames for burst analysis."""

    def __init__(self, buffer_size=15, fps=20):
        self.buffer_size   = buffer_size
        self.fps           = fps
        self.frame_interval = 1.0 / fps
        self.burst_buffer  = deque(maxlen=buffer_size)
        self.is_capturing  = False
        self.lock          = Lock()

    def start_burst(self):
        with self.lock:
            self.is_capturing = True
            self.burst_buffer.clear()

    def add_frame(self, frame):
        with self.lock:
            if self.is_capturing:
                self.burst_buffer.append({'frame': frame.copy(), 'timestamp': time.time()})

    def stop_burst(self):
        with self.lock:
            self.is_capturing = False
            if not self.burst_buffer:
                return None
            scored = []
            for item in self.burst_buffer:
                score = ImageQualityScorer.score_image(item['frame'])
                scored.append({'frame': item['frame'], 'timestamp': item['timestamp'], 'score': score})
            scored.sort(key=lambda x: x['score']['total'], reverse=True)
            best = scored[0]
            return {'frame': best['frame'], 'timestamp': best['timestamp'],
                    'score': best['score'], 'total_captures': len(scored)}

    def get_best_frames(self, top_n=3):
        with self.lock:
            if not self.burst_buffer:
                return []
            scored = []
            for item in self.burst_buffer:
                score = ImageQualityScorer.score_image(item['frame'])
                scored.append({'frame': item['frame'], 'timestamp': item['timestamp'], 'score': score})
            scored.sort(key=lambda x: x['score']['total'], reverse=True)
            return scored[:top_n]


# ─────────────────────────────────────────────────────────────────────────────
# HYBRID OBJECT DETECTOR
# ─────────────────────────────────────────────────────────────────────────────

class HybridObjectDetector:
    """
    Two-stage object detector:
      Stage 1 — YOLO-World open-vocabulary neural detection (enrolled names as classes).
      Stage 2 — SIFT+RANSAC template verification on every YOLO candidate crop.

    Rules:
      • No hardcoded class names — works for whatever the user enrolls.
      • Body parts (hand/palm/finger) are NEVER treated as competing distractors;
        humans naturally hold objects in their hands.
      • Distractor suppression only fires for conflicting physical objects
        (thermos, cup, smartwatch, box, …) that could be mistaken for an enrolled item.
      • SIFT verification is a *gate*, not a scoring hack: if SIFT passes, we trust neural.
      • If the neural engine is unavailable, pure SIFT-RANSAC runs standalone.
    """

    # ── constants ──────────────────────────────────────────────────────────────
    # Physical-object categories that could be confused with an enrolled product.
    # Anatomical / clothing classes deliberately excluded so held items aren't penalised.
    PHYSICAL_DISTRACTORS = {
        'thermos', 'tumbler', 'travel mug',
        'cup', 'mug', 'coffee mug', 'tea cup',
        'bottle', 'water bottle', 'beverage can', 'can',
        'smartwatch', 'watch', 'watch band',
        'ring', 'finger ring', 'bracelet', 'wristband',
        'cardboard box', 'box', 'paper bag', 'paper',
    }

    # Soft-context classes — added to the YOLO vocab so the model uses capacity
    # on them (reducing false positives) but they never fire as a detection.
    CONTEXT_CLASSES = {
        'hand', 'fist', 'finger', 'palm', 'wrist', 'arm',
        'sleeve', 'cuff', 'jacket', 'hoodie', 'shirt', 'clothing',
        'pillow', 'cushion', 'chair', 'couch',
    }

    def __init__(self, templates_dir='./object_database', min_confidence=0.55, use_neural=True):
        base_dir = Path(__file__).resolve().parent
        p = Path(templates_dir)
        self.templates_dir = p if p.is_absolute() else (base_dir / p)
        self.templates_dir.mkdir(exist_ok=True)

        self.min_confidence = min_confidence

        # ── SIFT feature matching engine ───────────────────────────────────
        self.sift  = cv2.SIFT_create(nfeatures=2500, contrastThreshold=0.02, edgeThreshold=12)
        self.flann = cv2.FlannBasedMatcher({'algorithm': 1, 'trees': 5}, {'checks': 100})

        # Template stores — keyed by enrolled object name
        self.object_templates   = {}   # name → [BGR images]
        self.template_features  = {}   # name → [{'kp', 'des', 'shape', 'img'}]
        self.template_hists     = {}   # name → [HSV histograms]
        self.template_edges     = {}   # name → [edge maps 128×128]

        # YOLO vocab helpers
        self.vocabulary_mapping      = {}   # yolo-class-str → enrolled name
        self.object_distractor_classes = set()   # active physical distractors in vocab

        # ── Neural engine (YOLO-World) ─────────────────────────────────────
        self.neural_enabled = False
        self.yolo_model     = None
        self.device         = 'cpu'

        if use_neural and HAS_YOLO:
            try:
                if torch.backends.mps.is_available():
                    self.device = 'mps'
                elif torch.cuda.is_available():
                    self.device = 'cuda'

                for candidate in ['yolov8s-worldv2.pt', 'yolov8n.pt']:
                    model_file = base_dir / candidate
                    if model_file.exists():
                        break
                else:
                    model_file = Path('yolov8s-worldv2.pt')

                print(f"🧠 Loading Neural Vision Engine ({model_file.name} on {self.device.upper()})...")
                self.yolo_model = YOLO(str(model_file))
                _ = self.yolo_model(np.zeros((480, 640, 3), dtype=np.uint8),
                                    device=self.device, verbose=False)
                self.neural_enabled = True
                print(f"✓ Neural Engine Ready (Hardware Accelerated: {self.device.upper()})")
            except Exception as e:
                print(f"⚠️  Neural engine unavailable: {e} — using SIFT only")

        # ── Pose engine (wrist / elbow keypoints for hand-zone masking) ───
        self.pose_model   = None
        self.pose_enabled = False
        if HAS_YOLO:
            try:
                pose_file = base_dir / 'yolov8n-pose.pt'
                if pose_file.exists():
                    self.pose_model = YOLO(str(pose_file))
                    _ = self.pose_model(np.zeros((480, 640, 3), dtype=np.uint8),
                                        device=self.device, verbose=False)
                    self.pose_enabled = True
                    print(f"✓ Hand & Limb Centric Engine Active ({self.device.upper()})")
            except Exception as e:
                print(f"⚠️  Pose engine unavailable: {e}")

        # ── Face detector ──────────────────────────────────────────────────
        self.face_cascade = None
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            print("✓ Customer Face Biometrics Engine Active (Haar Cascade)")
        except Exception as e:
            print(f"⚠️  Face engine error: {e}")

        # ── QR scanner ────────────────────────────────────────────────────
        self.qr_detector = None
        try:
            self.qr_detector = cv2.QRCodeDetector()
            print("✓ Optical QR Code Product Scanner Active")
        except Exception as e:
            print(f"⚠️  QR engine error: {e}")

        self.load_all_templates()
        self.update_neural_vocabulary()

    # ══════════════════════════════════════════════════════════════════════════
    # VOCABULARY & TEMPLATE MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════════

    def update_neural_vocabulary(self):
        """
        Build the YOLO-World class list dynamically from enrolled objects.
        Enrolled names become target classes; physical distractors and context
        classes are appended so the model's attention is spread properly.
        """
        if not self.neural_enabled or self.yolo_model is None:
            return
        try:
            # Bilingual English & Russian synonym mapping
            SYNONYMS = {
                'телефон': ['phone', 'smartphone', 'mobile phone', 'cell phone'],
                'phone':   ['phone', 'smartphone', 'mobile phone', 'cell phone'],
                'мышь':    ['mouse', 'computer mouse', 'magic mouse', 'wireless mouse', 'apple mouse'],
                'mouse':   ['mouse', 'computer mouse', 'magic mouse', 'wireless mouse', 'apple mouse'],
                'часы':    ['watch', 'wristwatch', 'smartwatch'],
                'watch':   ['watch', 'wristwatch', 'smartwatch'],
                'кольцо':  ['ring', 'finger ring'],
                'ring':    ['ring', 'finger ring'],
                'ручка':   ['pen', 'ballpoint pen'],
                'pen':     ['pen', 'ballpoint pen'],
                'бутылка': ['bottle', 'water bottle'],
                'bottle':  ['bottle', 'water bottle'],
                'термос':  ['thermos', 'tumbler', 'travel mug'],
                'thermos': ['thermos', 'tumbler', 'travel mug'],
                'кружка':  ['cup', 'mug', 'coffee cup', 'tea cup'],
                'cup':     ['cup', 'mug', 'coffee cup', 'tea cup'],
                'чашка':   ['cup', 'mug', 'coffee cup', 'tea cup'],
                'ключи':   ['keys', 'keychain'],
                'keys':    ['keys', 'keychain'],
                'наушники':['headphones', 'earphones', 'earbuds'],
                'headphones': ['headphones', 'earphones', 'earbuds'],
                'кошелек': ['wallet', 'purse'],
                'wallet':  ['wallet', 'purse'],
                'очки':    ['glasses', 'sunglasses'],
                'glasses': ['glasses', 'sunglasses'],
                'книга':   ['book'],
                'book':    ['book'],
                'ноутбук': ['laptop', 'notebook'],
                'laptop':  ['laptop', 'notebook'],
            }

            self.vocabulary_mapping = {}
            active_classes = []

            for name in self.object_templates:
                clean = name.lower().strip()
                if clean not in active_classes:
                    active_classes.append(clean)
                    self.vocabulary_mapping[clean] = name
                for key, syns in SYNONYMS.items():
                    if key == clean or f" {key} " in f" {clean} ":
                        for s in syns:
                            if s not in active_classes:
                                active_classes.append(s)
                                self.vocabulary_mapping[s] = name

            # Physical distractors — only those NOT already mapped to a target
            self.object_distractor_classes = set()
            for d in self.PHYSICAL_DISTRACTORS:
                if d not in self.vocabulary_mapping:
                    active_classes.append(d)
                    self.object_distractor_classes.add(d)

            # Context / body classes
            for d in self.CONTEXT_CLASSES:
                if d not in self.vocabulary_mapping and d not in self.object_distractor_classes:
                    active_classes.append(d)

            if not active_classes:
                active_classes = ['standby_target']

            if hasattr(self.yolo_model, 'set_classes'):
                self.yolo_model.set_classes(active_classes)
                n_target = len(self.vocabulary_mapping)
                n_dist   = len(self.object_distractor_classes)
                print(f"✓ Neural Open Vocabulary active "
                      f"({len(active_classes)} total classes: "
                      f"{n_target} target, {n_dist} distractors)")
        except Exception as e:
            print(f"⚠️  Vocabulary update error: {e}")

    # ── Template helpers ───────────────────────────────────────────────────

    @staticmethod
    def _skin_mask(img):
        """Returns a binary mask where skin pixels = 255."""
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        return cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))

    @staticmethod
    def _object_mask(img):
        """Mask that excludes skin, keeping object pixels (or None if >92% skin)."""
        if img is None or img.size == 0 or len(img.shape) != 3:
            return None
        skin = HybridObjectDetector._skin_mask(img)
        if (skin > 0).mean() > 0.92:
            return None
        m = cv2.bitwise_not(skin)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        return cv2.morphologyEx(m, cv2.MORPH_OPEN, k)

    def _extract_sift_features(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        mask = self._object_mask(img)
        kp, des = self.sift.detectAndCompute(gray, mask=mask)
        if des is None or len(des) < 6:
            kp, des = self.sift.detectAndCompute(gray, None)
        h, w = gray.shape[:2]
        return {'kp': kp, 'des': des, 'shape': (w, h), 'img': img}

    @staticmethod
    def _hsv_hist(img):
        if img is None or img.size == 0 or img.shape[0] < 8 or img.shape[1] < 8:
            return None
        r = cv2.resize(img, (64, 64))
        hsv = cv2.cvtColor(r, cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0, 1], None, [12, 12], [0, 180, 0, 256])
        cv2.normalize(h, h)
        return h

    @staticmethod
    def _edge_map(img):
        if img is None or img.size == 0 or img.shape[0] < 8 or img.shape[1] < 8:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        return cv2.Canny(cv2.resize(gray, (128, 128)), 50, 150)

    # ── Template CRUD ──────────────────────────────────────────────────────

    def load_all_templates(self):
        for obj_dir in self.templates_dir.iterdir():
            if not obj_dir.is_dir():
                continue
            templates, features, hists, edges = [], [], [], []
            for f in sorted(obj_dir.glob('*.jpg')) + sorted(obj_dir.glob('*.png')):
                img = cv2.imread(str(f))
                if img is None:
                    continue
                templates.append(img)
                feat = self._extract_sift_features(img)
                if feat['des'] is not None and len(feat['kp']) >= 8:
                    features.append(feat)
                h = self._hsv_hist(img)
                if h is not None:
                    hists.append(h)
                e = self._edge_map(img)
                if e is not None:
                    edges.append(e)
            if templates:
                name = obj_dir.name
                self.object_templates[name]  = templates
                self.template_features[name] = features
                self.template_hists[name]    = hists
                self.template_edges[name]    = edges
                total_kp = sum(len(f['kp']) for f in features)
                print(f"✓ Loaded '{name}' ({len(templates)} templates, {total_kp} invariant keypoints)")

    def add_object_burst(self, name: str, frames: list):
        """
        Problem 1 Fix: Multi-frame Burst Enrollment.
        Accepts 8-15 frames captured from diverse angles, selects the top 5
        most diverse and sharpest frames, and registers multi-angle templates.
        """
        if not frames:
            return False

        obj_dir = self.templates_dir / name
        obj_dir.mkdir(exist_ok=True)

        # Score frames by Laplacian sharpness and SIFT feature richness
        scored_frames = []
        for idx, f in enumerate(frames):
            if f is None or f.size == 0:
                continue
            gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) if len(f.shape) == 3 else f
            lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            kp, _ = self.sift.detectAndCompute(gray, None)
            kp_count = len(kp) if kp else 0
            score = lap_var * 0.5 + kp_count * 1.5
            scored_frames.append((score, idx, f))

        scored_frames.sort(key=lambda x: x[0], reverse=True)
        # Select up to 5 best diverse frames
        best_frames = [item[2] for item in scored_frames[:5]]
        if not best_frames:
            best_frames = [frames[0]]

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        for i, frame in enumerate(best_frames):
            frame_path = obj_dir / f"{name}_{ts}_{i+1}.jpg"
            cv2.imwrite(str(frame_path), frame)
            
            self.object_templates.setdefault(name, []).append(frame)
            self.template_hists.setdefault(name, [])
            self.template_edges.setdefault(name, [])
            self.template_features.setdefault(name, [])

            feat = self._extract_sift_features(frame)
            if feat['des'] is not None:
                self.template_features[name].append(feat)
            h = self._hsv_hist(frame)
            if h is not None:
                self.template_hists[name].append(h)
            e = self._edge_map(frame)
            if e is not None:
                self.template_edges[name].append(e)

        # Update neural vocabulary ONCE after all burst templates are enrolled
        self.update_neural_vocabulary()
        total_kp = sum(len(f['kp']) for f in self.template_features.get(name, []))
        print(f"✓ Burst-enrolled '{name}' with {len(best_frames)} multi-angle templates ({total_kp} invariant keypoints)")
        return True

    def add_object(self, name, image_path_or_array, auto_rebuild_vocab=True):
        img = (cv2.imread(image_path_or_array)
               if isinstance(image_path_or_array, str)
               else image_path_or_array)
        if img is None:
            return False
        obj_dir = self.templates_dir / name
        obj_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        cv2.imwrite(str(obj_dir / f'{name}_{ts}.jpg'), img)

        self.object_templates.setdefault(name, []).append(img)
        self.template_hists.setdefault(name, [])
        self.template_edges.setdefault(name, [])
        self.template_features.setdefault(name, [])

        feat = self._extract_sift_features(img)
        if feat['des'] is not None:
            self.template_features[name].append(feat)
        h = self._hsv_hist(img)
        if h is not None:
            self.template_hists[name].append(h)
        e = self._edge_map(img)
        if e is not None:
            self.template_edges[name].append(e)

        self.update_neural_vocabulary()
        print(f"✓ Added '{name}' ({len(feat['kp'])} keypoints)")
        return True

    def delete_object(self, name):
        import shutil
        obj_dir = self.templates_dir / name
        if obj_dir.exists():
            shutil.rmtree(obj_dir)
        for store in [self.object_templates, self.template_features,
                      self.template_hists, self.template_edges]:
            store.pop(name, None)
        self.update_neural_vocabulary()
        print(f"🗑️  Deleted '{name}'")
        return True

    def delete_template(self, name, filename):
        f = self.templates_dir / name / filename
        if f.exists():
            f.unlink()
            self.reload_object(name)
            return True
        return False

    def reload_object(self, name):
        for store in [self.object_templates, self.template_features,
                      self.template_hists, self.template_edges]:
            store.pop(name, None)
        obj_dir = self.templates_dir / name
        if obj_dir.exists():
            templates, features, hists, edges = [], [], [], []
            for f in sorted(obj_dir.glob('*.jpg')) + sorted(obj_dir.glob('*.png')):
                img = cv2.imread(str(f))
                if img is None:
                    continue
                templates.append(img)
                feat = self._extract_sift_features(img)
                if feat['des'] is not None and len(feat['kp']) >= 8:
                    features.append(feat)
                h = self._hsv_hist(img)
                if h is not None:
                    hists.append(h)
                e = self._edge_map(img)
                if e is not None:
                    edges.append(e)
            if templates:
                self.object_templates[name]  = templates
                self.template_features[name] = features
                self.template_hists[name]    = hists
                self.template_edges[name]    = edges
        self.update_neural_vocabulary()

    def clear_all_objects(self):
        import shutil
        if self.templates_dir.exists():
            for item in self.templates_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                elif item.is_file() and item.suffix in ('.jpg', '.png'):
                    item.unlink()
        for store in [self.object_templates, self.template_features,
                      self.template_hists, self.template_edges]:
            store.clear()
        self.update_neural_vocabulary()
        print("🗑️  All objects cleared")
        return True

    def get_objects_summary(self):
        summary = []
        if not self.templates_dir.exists():
            return summary
        for obj_dir in sorted(self.templates_dir.iterdir()):
            if not obj_dir.is_dir() or obj_dir.name.startswith('.'):
                continue
            name = obj_dir.name
            files = []
            total_sz = 0
            for f in sorted(obj_dir.glob('*.jpg')) + sorted(obj_dir.glob('*.png')):
                st = f.stat()
                total_sz += st.st_size
                files.append({'filename': f.name, 'path': str(f),
                               'size_kb': round(st.st_size / 1024, 1),
                               'modified': datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')})
            feats  = self.template_features.get(name, [])
            total_kp = sum(len(f['kp']) for f in feats)
            summary.append({'name': name, 'template_count': len(files),
                             'total_keypoints': total_kp, 'templates': files,
                             'total_size_kb': round(total_sz / 1024, 1),
                             'yolo_active': self.neural_enabled})
        return summary

    # ══════════════════════════════════════════════════════════════════════════
    # AUXILIARY DETECTORS (face, QR, hand presence)
    # ══════════════════════════════════════════════════════════════════════════

    def detect_faces(self, frame):
        if self.face_cascade is None or self.face_cascade.empty():
            return []
        try:
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.12,
                                                       minNeighbors=5, minSize=(50, 50),
                                                       flags=cv2.CASCADE_SCALE_IMAGE)
            return [{'bbox': [int(x), int(y), int(w), int(h)],
                     'confidence': 0.98, 'object': 'Customer Face', 'type': 'face'}
                    for (x, y, w, h) in faces]
        except Exception:
            return []

    def detect_qr(self, frame):
        if self.qr_detector is None:
            return None
        try:
            val, pts, _ = self.qr_detector.detectAndDecode(frame)
            if val and val.strip():
                raw = val.strip()
                item = raw
                for pfx in ('NEX_SHELF_ITEM:', 'NEX_ITEM:'):
                    if raw.startswith(pfx):
                        item = raw[len(pfx):].strip()
                        break
                return {'raw': raw, 'item': item,
                        'points': pts.tolist() if pts is not None else None}
        except Exception:
            pass
        return None

    def check_hand_presence(self, frame):
        if not self.pose_enabled or self.pose_model is None:
            return False, None
        try:
            res = self.pose_model(frame, device=self.device, conf=0.15, verbose=False)[0]
            if res.keypoints is not None and len(res.keypoints) > 0:
                kpts  = res.keypoints.xy.cpu().numpy()[0]
                confs = (res.keypoints.conf.cpu().numpy()[0]
                         if res.keypoints.conf is not None else np.ones(len(kpts)))
                h, w  = frame.shape[:2]
                for w_idx in [9, 10]:
                    if len(confs) > w_idx and confs[w_idx] >= 0.15:
                        wx, wy = kpts[w_idx]
                        if 15 < wx < w - 15 and 15 < wy < h - 15:
                            return True, (int(wx), int(wy))
        except Exception:
            pass
        return False, None

    # ══════════════════════════════════════════════════════════════════════════
    # HAND-ZONE MASK  (used to restrict SIFT to the interaction area)
    # ══════════════════════════════════════════════════════════════════════════

    def extract_hand_limb_mask(self, frame):
        """
        Returns (mask, hand_boxes).
        mask     — 8-bit image, 255 where the detector should look.
        hand_boxes — list of [x, y, w, h] regions around detected wrists.

        If pose is unavailable or no wrists are detected with confidence,
        the full frame stays open (mask = all-255).
        """
        fh, fw = frame.shape[:2]
        full_mask = np.full((fh, fw), 255, dtype=np.uint8)

        if not self.pose_enabled or self.pose_model is None:
            return full_mask, []

        mask      = np.zeros((fh, fw), dtype=np.uint8)
        hand_boxes = []
        try:
            res = self.pose_model(frame, device=self.device, conf=0.15, verbose=False)[0]
            has_limbs = False

            if res.keypoints is not None and len(res.keypoints) > 0:
                kpts  = res.keypoints.xy.cpu().numpy()[0]
                confs = (res.keypoints.conf.cpu().numpy()[0]
                         if res.keypoints.conf is not None else np.ones(len(kpts)))

                # Keypoints 7/8=elbow L/R, 9/10=wrist L/R
                for e_idx, w_idx in [(7, 9), (8, 10)]:
                    wx, wy = kpts[w_idx]
                    ex, ey = kpts[e_idx]
                    wc = confs[w_idx]
                    ec = confs[e_idx]

                    if wc >= 0.18 and 4 < wx < fw - 4 and 4 < wy < fh - 4:
                        # Draw forearm segment
                        if ec >= 0.12 and ex > 0 and ey > 0:
                            cv2.line(mask, (int(ex), int(ey)), (int(wx), int(wy)), 255, 110)
                        # Draw hand region around wrist
                        cv2.circle(mask, (int(wx), int(wy)), 140, 255, -1)
                        bx = max(0, int(wx - 110))
                        by = max(0, int(wy - 110))
                        bw = min(fw - bx, 220)
                        bh = min(fh - by, 220)
                        hand_boxes.append([bx, by, bw, bh])
                        has_limbs = True

                        # Extend toward fingertips
                        if ec >= 0.12 and ex > 0 and ey > 0:
                            dx, dy = wx - ex, wy - ey
                            arm_len = np.hypot(dx, dy)
                            if arm_len > 15:
                                hx = int(wx + 0.85 * dx)
                                hy = int(wy + 0.85 * dy)
                                cv2.line(mask, (int(wx), int(wy)), (hx, hy), 255, 120)
                                cv2.circle(mask, (hx, hy), 120, 255, -1)
                                hand_boxes.append([max(0, hx - 110), max(0, hy - 110), 220, 220])

            if not has_limbs:
                return full_mask, []
        except Exception:
            return full_mask, []

        return mask, hand_boxes

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 1 — SIFT + RANSAC TEMPLATE MATCHING
    # ══════════════════════════════════════════════════════════════════════════

    def _sift_match_score(self, gray_frame, frame_w, frame_h, limb_mask=None):
        """
        Returns a list of raw SIFT detections.
        Each dict: {object, confidence, bbox[x,y,w,h], quad, inliers, source}
        """
        detections = []
        kp_f, des_f = self.sift.detectAndCompute(gray_frame, None)
        if des_f is None or len(des_f) < 8:
            return detections

        # Restrict keypoints to the hand-interaction zone (with full-frame fallback)
        if limb_mask is not None and limb_mask.any():
            valid = [i for i, kp in enumerate(kp_f)
                     if limb_mask[min(frame_h-1, int(kp.pt[1])),
                                  min(frame_w-1, int(kp.pt[0]))] > 0]
            if len(valid) >= 8:
                kp_f  = [kp_f[i] for i in valid]
                des_f = des_f[valid]
            # When pose keypoints are sparse (< 8), DO NOT exit!
            # Gracefully fallback to searching across the frame.

        frame_area = frame_w * frame_h

        for obj_name, feat_list in self.template_features.items():
            best = None
            for feat in feat_list:
                des_t = feat['des']
                kp_t  = feat['kp']
                tw, th = feat['shape']
                if des_t is None or len(des_t) < 8:
                    continue

                matches = self.flann.knnMatch(des_t, des_f, k=2)
                good    = [m for m, n in matches if m.distance < 0.78 * n.distance]
                if len(good) < 6:
                    continue

                pts_t = np.float32([kp_t[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                pts_f = np.float32([kp_f[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                H, mask = cv2.findHomography(pts_t, pts_f, cv2.RANSAC, 5.0)
                if mask is None:
                    continue

                inliers      = int(mask.ravel().sum())
                inlier_ratio = inliers / max(1, len(good))
                if inliers < 6:
                    continue

                # Unique inlier check — prevents duplicate-descriptor stacking
                in_pts_f = pts_f[mask.ravel() == 1].reshape(-1, 2)
                in_pts_t = pts_t[mask.ravel() == 1].reshape(-1, 2)
                uniq_f = len({(round(float(p[0]), 1), round(float(p[1]), 1)) for p in in_pts_f})
                uniq_t = len({(round(float(p[0]), 1), round(float(p[1]), 1)) for p in in_pts_t})
                if min(uniq_f, uniq_t) < 5:
                    continue

                # Pathway A: planar homography quad
                quad = None
                if inliers >= 7 and inlier_ratio >= 0.35:
                    corners = np.float32([[0,0],[tw,0],[tw,th],[0,th]]).reshape(-1, 1, 2)
                    try:
                        proj = cv2.perspectiveTransform(corners, H).reshape(-1, 2)
                        if cv2.isContourConvex(proj.astype(np.int32)):
                            area = cv2.contourArea(proj)
                            if 200 < area < frame_area * 0.22:
                                rect = cv2.minAreaRect(proj.astype(np.float32))
                                rw, rh = rect[1]
                                rmin, rmax = min(rw, rh), max(rw, rh)
                                if rmin >= 6 and rmax >= 18 and rmax / max(1.0, rmin) <= 12.0:
                                    quad = proj
                    except Exception:
                        pass

                # Pathway B: compact cluster
                in_pts = pts_f[mask.ravel() == 1].reshape(-1, 2)
                std_x, std_y = float(np.std(in_pts[:, 0])), float(np.std(in_pts[:, 1]))
                mn_x, mx_x  = float(np.min(in_pts[:, 0])), float(np.max(in_pts[:, 0]))
                mn_y, mx_y  = float(np.min(in_pts[:, 1])), float(np.max(in_pts[:, 1]))
                bw_raw, bh_raw = mx_x - mn_x, mx_y - mn_y

                # Pathway B: Adaptive cluster (supports large and close-up products)
                cluster_ok = (
                    min(uniq_f, uniq_t) >= 5 and
                    inlier_ratio >= 0.20 and
                    bw_raw * bh_raw < frame_area * 0.75 and
                    bw_raw >= 12 and bh_raw >= 12
                )

                if quad is not None:
                    x_mn = int(np.clip(np.min(quad[:, 0]), 0, frame_w - 1))
                    x_mx = int(np.clip(np.max(quad[:, 0]), 0, frame_w - 1))
                    y_mn = int(np.clip(np.min(quad[:, 1]), 0, frame_h - 1))
                    y_mx = int(np.clip(np.max(quad[:, 1]), 0, frame_h - 1))
                    bw, bh = x_mx - x_mn, y_mx - y_mn
                    conf   = min(0.99, max(0.65, inliers / 15.0))
                elif cluster_ok:
                    pad  = 16
                    x_mn = max(0, int(mn_x - pad))
                    y_mn = max(0, int(mn_y - pad))
                    x_mx = min(frame_w, int(mx_x + pad))
                    y_mx = min(frame_h, int(mx_y + pad))
                    bw, bh = x_mx - x_mn, y_mx - y_mn
                    conf   = min(0.95, max(0.65, 0.65 + (min(uniq_f, uniq_t) - 6) * 0.04))
                else:
                    continue

                min_dim = min(bw, bh)
                if min_dim < 6 or max(bw, bh) < 18 or bw * bh < 160:
                    continue

                on_border = (x_mn <= 8 or x_mn + bw >= frame_w - 8 or
                             y_mn <= 8 or y_mn + bh >= frame_h - 8)
                if on_border and (min_dim < 60 or
                                  (x_mn <= 4 and y_mn <= 4) or
                                  (x_mn + bw >= frame_w - 4 and y_mn + bh >= frame_h - 4)):
                    continue

                candidate = {
                    'object':     obj_name,
                    'confidence': float(conf),
                    'bbox':       [x_mn, y_mn, bw, bh],
                    'quad':       quad.astype(np.int32).tolist() if quad is not None else None,
                    'inliers':    inliers,
                    'source':     'sift_ransac',
                }
                if best is None or inliers > best['inliers']:
                    best = candidate
            if best is not None:
                detections.append(best)

        return detections

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2 — SIFT CROP VERIFICATION  (gate on neural candidates)
    # ══════════════════════════════════════════════════════════════════════════

    def _verify_crop(self, crop, obj_name, has_competing_distractor=False):
        """
        Verifies that a candidate crop actually looks like `obj_name` by running
        SIFT matching, edge correlation, and colour histogram against stored templates.

        Returns (verified_name, score) where score ∈ [0, 1].
        Returns (None, 0.0) if the crop fails verification.
        """
        if crop is None or crop.size == 0 or crop.shape[0] < 8 or crop.shape[1] < 8:
            return None, 0.0
        if not self.object_templates:
            return obj_name, 0.5

        # Pick the target — DO NOT guess or fall back to an unrelated object
        if obj_name not in self.object_templates:
            return None, 0.0
        target = obj_name

        templates = self.object_templates.get(target, [])
        if not templates:
            return obj_name, 0.45

        # Aspect-ratio sanity (derived from enrolled templates, not hardcoded)
        ch, cw = crop.shape[:2]
        c_ar   = max(cw, ch) / max(1.0, min(cw, ch))
        t_ars  = [max(t.shape[0], t.shape[1]) / max(1.0, min(t.shape[0], t.shape[1]))
                  for t in templates if t is not None]
        if t_ars and (c_ar < min(t_ars) * 0.30 or c_ar > max(t_ars) * 3.0):
            return None, 0.0

        crop_gray    = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        kp_c, des_c  = self.sift.detectAndCompute(crop_gray, None)
        c_edge        = self._edge_map(crop)

        max_inliers  = 0
        max_good     = 0
        max_edge_corr = 0.0

        feats      = self.template_features.get(target, [])
        edge_list  = self.template_edges.get(target, [])

        for idx, t in enumerate(templates):
            # Edge correlation
            if idx < len(edge_list) and edge_list[idx] is not None and c_edge is not None:
                try:
                    corr = cv2.matchTemplate(c_edge, edge_list[idx], cv2.TM_CCOEFF_NORMED)[0][0]
                    if corr > max_edge_corr:
                        max_edge_corr = float(corr)
                except Exception:
                    pass

            # SIFT inlier count
            if idx < len(feats):
                feat = feats[idx]
                des_t, kp_t = feat['des'], feat['kp']
                if (des_t is not None and des_c is not None and
                        len(des_t) >= 6 and len(des_c) >= 4):
                    try:
                        matches = self.flann.knnMatch(des_t, des_c, k=2)
                        good    = [m for m, n in matches
                                   if len(matches) > 1 and m.distance < 0.78 * n.distance]
                        if len(good) > max_good:
                            max_good = len(good)
                        if len(good) >= 4:
                            pts_t_ = np.float32([kp_t[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                            pts_c_ = np.float32([kp_c[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                            _, mask = cv2.findHomography(pts_t_, pts_c_, cv2.RANSAC, 5.0)
                            if mask is not None:
                                n_in = int(mask.ravel().sum())
                                if n_in > max_inliers:
                                    max_inliers = n_in
                    except Exception:
                        pass

        # HSV colour histogram
        c_hist = self._hsv_hist(crop)
        h_list = self.template_hists.get(target, [])
        max_hsv = 0.0
        if c_hist is not None and h_list:
            sims    = [cv2.compareHist(c_hist, th, cv2.HISTCMP_CORREL) for th in h_list]
            max_hsv = max(sims) if sims else 0.0

        # ── Decision ──────────────────────────────────────────────────────
        # Strict mode: when a physical distractor overlaps, require stronger evidence
        if has_competing_distractor:
            if max_inliers >= 8 and max_good >= 15:
                return target, min(0.98, 0.70 + max_inliers * 0.03)
            return None, 0.0

        # Count total enrolled template keypoints for this target
        total_t_kp = sum(len(f.get('kp', [])) for f in feats) if feats else 0
        is_low_texture = (total_t_kp < 150)

        # Normal mode: SIFT inliers OR good match count
        if max_inliers >= 4 or max_good >= 8:
            score = min(0.98, max(0.65, 0.50 + max_inliers * 0.04))
            return target, float(score)

        # For smooth / low-texture items (e.g. Magic Mouse, minimal accessories):
        if is_low_texture:
            if max_hsv >= 0.52:
                # Strong color consistency with enrolled object
                return target, float(min(0.95, max(0.62, 0.50 + max_hsv * 0.45)))
            if max_inliers >= 2 or max_good >= 3:
                return target, 0.65
            if max_edge_corr >= 0.15:
                return target, 0.62

        # Edge structure match
        if max_edge_corr >= 0.18:
            return target, min(0.90, 0.52 + max_edge_corr * 0.40)

        # Colour + weak SIFT
        if max_hsv >= 0.42 and (max_inliers >= 2 or max_good >= 4):
            return target, 0.52

        return None, 0.0

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 1b — NEURAL DETECTION (YOLO-World)
    # ══════════════════════════════════════════════════════════════════════════

    def _neural_detect(self, frame, frame_w, frame_h, hand_boxes=None):
        """
        Run YOLO-World, filter by:
          1. Size constraints (not a giant or tiny box)
          2. Class must map to an enrolled object
          3. Must be in a hand-interaction zone (if pose detected hands)
          4. Crop-level SIFT verification (_verify_crop)
          5. NMS per object category

        Returns list of detection dicts.
        """
        detections = []
        if not self.neural_enabled or self.yolo_model is None or not self.object_templates:
            return detections

        try:
            results    = self.yolo_model(frame, device=self.device, conf=0.06, verbose=False)
            frame_area = frame_w * frame_h
            raw_boxes  = []

            for r in results:
                for b in r.boxes:
                    cls_id   = int(b.cls[0])
                    raw_cls  = self.yolo_model.names[cls_id].lower()
                    raw_conf = float(b.conf[0])
                    xywh     = b.xywh[0].cpu().numpy()

                    bw = int(xywh[2]); bh = int(xywh[3])
                    bx = int(xywh[0] - bw / 2)
                    by = int(xywh[1] - bh / 2)
                    mn = min(bw, bh); mx = max(bw, bh)

                    # Drop edge slivers
                    on_edge = (bx <= 8 or bx + bw >= frame_w - 8 or
                               by <= 8 or by + bh >= frame_h - 8)
                    if on_edge and (mn < 60 or mx < 120 or
                                    (bx <= 4 and by <= 4) or
                                    (bx + bw >= frame_w - 4 and by + bh >= frame_h - 4)):
                        continue

                    # Drop giant / tiny boxes
                    if bw * bh > frame_area * 0.30 or bw > 420 or bh > 420 or mn < 6 or mx < 16:
                        continue

                    is_phys_dist = raw_cls in self.object_distractor_classes
                    matched_obj  = None
                    if not is_phys_dist:
                        matched_obj = self.vocabulary_mapping.get(raw_cls)
                        if not matched_obj:
                            for vk, en in self.vocabulary_mapping.items():
                                if vk == raw_cls or f" {vk} " in f" {raw_cls} " or f" {raw_cls} " in f" {vk} ":
                                    matched_obj = en
                                    break
                        if not matched_obj:
                            for tn in self.object_templates:
                                if tn.lower() in raw_cls or raw_cls in tn.lower():
                                    matched_obj = tn
                                    break

                    raw_boxes.append({
                        'cls': raw_cls, 'conf': raw_conf,
                        'bbox': [bx, by, bw, bh],
                        'is_phys_dist': is_phys_dist,
                        'matched_obj': matched_obj,
                    })

            # ── Filter and verify ──────────────────────────────────────────
            candidates = []
            for cand in raw_boxes:
                if cand['is_phys_dist'] or not cand['matched_obj']:
                    continue

                matched_obj = cand['matched_obj']
                bx, by, bw, bh = cand['bbox']

                # Hand-zone constraint: only skip if pose DID detect hands
                # and this box is clearly outside all hand regions.
                if hand_boxes:
                    cx, cy = bx + bw / 2.0, by + bh / 2.0
                    in_zone = any(
                        (hx - 65 <= cx <= hx + hw + 65) and (hy - 65 <= cy <= hy + hh + 65)
                        for hx, hy, hw, hh in hand_boxes
                    )
                    if not in_zone:
                        continue

                # Competing PHYSICAL distractor check
                # (body parts / clothing intentionally excluded)
                competing = any(
                    d['cls'] in self.object_distractor_classes and
                    d['conf'] >= 0.20 and
                    self._iou([bx, by, bw, bh], d['bbox']) > 0.30
                    for d in raw_boxes
                )

                crop = frame[max(0, by):min(frame_h, by + bh),
                             max(0, bx):min(frame_w, bx + bw)]
                v_name, v_score = self._verify_crop(crop, matched_obj, competing)
                if v_name is None:
                    continue

                # Calibrated confidence: blend YOLO score + verification score
                cal_conf = float(np.clip(cand['conf'] * 0.55 + v_score * 0.45,
                                         0.20, 0.98))
                candidates.append({
                    'object':     matched_obj,
                    'confidence': cal_conf,
                    'bbox':       [max(0, bx), max(0, by), bw, bh],
                    'quad':       None,
                    'source':     'yolo_neural',
                })

            # NMS per object class
            candidates.sort(key=lambda c: c['confidence'], reverse=True)
            for cand in candidates:
                keep = all(
                    self._iou(cand['bbox'], kept['bbox']) <= 0.30
                    for kept in detections
                    if kept['object'].lower() == cand['object'].lower()
                )
                if keep:
                    detections.append(cand)

        except Exception as e:
            print(f"Neural detection error: {e}")

        return detections

    # ══════════════════════════════════════════════════════════════════════════
    # IoU HELPER
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _iou(box1, box2):
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        ix = max(0, min(x1+w1, x2+w2) - max(x1, x2))
        iy = max(0, min(y1+h1, y2+h2) - max(y1, y2))
        inter = ix * iy
        union = w1*h1 + w2*h2 - inter
        return inter / union if union > 0 else 0.0

    # backward-compat alias used elsewhere in the codebase
    @staticmethod
    def _compute_iou(box1, box2):
        return HybridObjectDetector._iou(box1, box2)

    # ══════════════════════════════════════════════════════════════════════════
    # MAIN DETECTION ENTRY POINT
    # ══════════════════════════════════════════════════════════════════════════

    def detect_all_objects(self, frame):
        """
        Full hybrid detection cycle.

        Pipeline:
          1. Pose → hand-zone mask (restricts SIFT to interaction area).
          2. SIFT+RANSAC → precise template matches.
          3. YOLO-World  → open-vocab neural candidates, filtered + verified.
          4. IoU fusion  → merge SIFT and neural if they agree; boost confidence.
          5. Standalone SIFT accepted at high threshold (≥11 inliers, planar quad).
          6. Single-dominant-object pruning — highest confidence class wins.

        Returns:
          (detections, elapsed_ms)
          detections: list of dicts with keys:
            object, confidence, bbox [x,y,w,h], quad (or None), source
        """
        t0 = time.time()
        fh, fw = frame.shape[:2]
        gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ── 1. Hand-zone mask ──────────────────────────────────────────────
        limb_mask, hand_boxes = self.extract_hand_limb_mask(frame)

        # ── 2. SIFT+RANSAC ─────────────────────────────────────────────────
        sift_dets = self._sift_match_score(gray, fw, fh, limb_mask=limb_mask)

        # ── 3. Neural detection ────────────────────────────────────────────
        # Pass hand_boxes only when pose actually found hands; otherwise
        # the zone filter would block everything.
        neural_dets = self._neural_detect(frame, fw, fh,
                                          hand_boxes=hand_boxes if hand_boxes else None)

        # ── 4. Fuse SIFT + Neural ──────────────────────────────────────────
        fused       = []
        used_sift   = set()

        for nd in neural_dets:
            merged = False
            for si, sd in enumerate(sift_dets):
                if si in used_sift:
                    continue
                if nd['object'].lower() != sd['object'].lower():
                    continue
                iou  = self._iou(nd['bbox'], sd['bbox'])
                ncx  = nd['bbox'][0] + nd['bbox'][2] / 2
                ncy  = nd['bbox'][1] + nd['bbox'][3] / 2
                scx  = sd['bbox'][0] + sd['bbox'][2] / 2
                scy  = sd['bbox'][1] + sd['bbox'][3] / 2
                dist = np.hypot(ncx - scx, ncy - scy)
                mdim = max(nd['bbox'][2], nd['bbox'][3], sd['bbox'][2], sd['bbox'][3])

                if iou > 0.15 or dist < mdim * 0.80:
                    fused.append({
                        'object':     f"{nd['object']} [VERIFIED]",
                        'confidence': float(min(0.99,
                            max(nd['confidence'], sd['confidence']) + 0.10)),
                        'bbox':  nd['bbox'],
                        'quad':  sd.get('quad'),
                        'source': 'fused',
                    })
                    used_sift.add(si)
                    merged = True
                    break

            if not merged and nd['confidence'] >= self.min_confidence:
                fused.append({
                    'object':     f"{nd['object']} [AI]",
                    'confidence': float(nd['confidence']),
                    'bbox':  nd['bbox'],
                    'quad':  None,
                    'source': 'yolo_neural',
                })

        # ── 5. Standalone SIFT (high-confidence planar only) ───────────────
        for si, sd in enumerate(sift_dets):
            if si in used_sift:
                continue
            if sd.get('quad') is not None and sd.get('inliers', 0) >= 11 and sd.get('confidence', 0) >= 0.75:
                fused.append({
                    'object':     f"{sd['object']} [SIFT]",
                    'confidence': float(sd['confidence']),
                    'bbox':  sd['bbox'],
                    'quad':  sd.get('quad'),
                    'source': 'sift_ransac',
                })

        # ── 5b. Smooth / Low-Texture Object Pathway ────────────────────────
        # For textureless items (e.g. white Magic Mouse) where neural/SIFT feature points are sparse:
        if not fused:
            for obj_name, t_list in self.object_templates.items():
                feats = self.template_features.get(obj_name, [])
                total_t_kp = sum(len(f.get('kp', [])) for f in feats) if feats else 0
                if total_t_kp >= 180:
                    continue  # Object has plenty of texture (e.g. Phone), handles via SIFT/YOLO
                
                h_list = self.template_hists.get(obj_name, [])
                if not h_list:
                    continue

                ycrcb_f = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
                skin_f  = cv2.inRange(ycrcb_f, np.array([0, 133, 77]), np.array([255, 173, 127]))
                non_skin_f = cv2.bitwise_not(skin_f)

                mean_v = float(np.mean([cv2.cvtColor(t, cv2.COLOR_BGR2GRAY).mean() for t in t_list]))
                if mean_v > 135:
                    _, cand_bin = cv2.threshold(gray, int(mean_v * 0.72), 255, cv2.THRESH_BINARY)
                else:
                    cand_bin = np.full((fh, fw), 255, dtype=np.uint8)

                cand_mask = cv2.bitwise_and(cand_bin, non_skin_f)
                k_m = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                cand_mask = cv2.morphologyEx(cand_mask, cv2.MORPH_OPEN, k_m)

                cnts, _ = cv2.findContours(cand_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                best_cand = None
                for cnt in cnts:
                    area = cv2.contourArea(cnt)
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    min_d = min(bw, bh)
                    if 450 < area < (fh * fw * 0.25) and min_d >= 24 and max(bw, bh) >= 36:
                        if bx <= 4 or by <= 4 or (bx + bw) >= fw - 4 or (by + bh) >= fh - 4:
                            continue
                        roi = frame[by:by+bh, bx:bx+bw]
                        hsv_r = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                        hist_r = cv2.calcHist([hsv_r], [0, 1], None, [12, 12], [0, 180, 0, 256])
                        cv2.normalize(hist_r, hist_r)

                        sims = [cv2.compareHist(th, hist_r, cv2.HISTCMP_CORREL) for th in h_list]
                        max_sim = max(sims) if sims else 0.0
                        if max_sim >= 0.65:
                            if best_cand is None or max_sim > best_cand[0]:
                                best_cand = (max_sim, [bx, by, bw, bh])

                if best_cand and best_cand[0] >= 0.65:
                    fused.append({
                        'object':     f"{obj_name} [VERIFIED]",
                        'confidence': float(min(0.96, best_cand[0])),
                        'bbox':       best_cand[1],
                        'quad':       None,
                        'source':     'color_contour',
                    })
                    break

        # ── 6. Single-dominant-object pruning ─────────────────────────────
        # Sort by confidence desc; highest-confidence detection wins.
        # Competing classes are suppressed unless very distant AND very confident.
        fused.sort(key=lambda d: d['confidence'], reverse=True)
        final = []
        if fused:
            top     = fused[0]
            top_cls = top['object'].split()[0].lower()
            final.append(top)
            tcx = top['bbox'][0] + top['bbox'][2] / 2
            tcy = top['bbox'][1] + top['bbox'][3] / 2

            for det in fused[1:]:
                det_cls = det['object'].split()[0].lower()
                iou     = self._iou(det['bbox'], top['bbox'])
                if det_cls == top_cls:
                    if iou <= 0.30:
                        final.append(det)
                else:
                    dcx = det['bbox'][0] + det['bbox'][2] / 2
                    dcy = det['bbox'][1] + det['bbox'][3] / 2
                    dist = np.hypot(dcx - tcx, dcy - tcy)
                    if dist > 260 and det['confidence'] >= 0.94 and top['confidence'] < 0.96:
                        final.append(det)

        return final, (time.time() - t0) * 1000

    # ══════════════════════════════════════════════════════════════════════════
    # LEGACY ALIASES  (used by nex_server.py and other callers)
    # ══════════════════════════════════════════════════════════════════════════

    def detect_sift_objects(self, gray_frame, frame_w, frame_h, limb_mask=None):
        return self._sift_match_score(gray_frame, frame_w, frame_h, limb_mask=limb_mask)

    def detect_neural_objects(self, frame, frame_w, frame_h, hand_boxes=None):
        return self._neural_detect(frame, frame_w, frame_h, hand_boxes=hand_boxes)

    def verify_crop_appearance(self, crop, fallback_class=None, has_competing_obj_distractor=False):
        return self._verify_crop(crop, fallback_class, has_competing_obj_distractor)


# Backward-compatible alias
CustomObjectDetector = HybridObjectDetector


# ─────────────────────────────────────────────────────────────────────────────
# NEX CORE DETECTOR  (wraps HybridObjectDetector with burst capture + UI)
# ─────────────────────────────────────────────────────────────────────────────

class NexCoreDetector:
    """
    Top-level detection system: burst capture → quality selection → detection → save.
    """

    def __init__(self, config_path='nex_config.json'):
        print("=" * 70)
        print("NEX CORE DETECTION ENGINE v3.0")
        print("Burst Capture + Hybrid SIFT / YOLO Detection")
        print("=" * 70)

        self.config = self._load_config(config_path)
        self.object_detector = HybridObjectDetector(
            min_confidence=self.config.get('min_confidence', 0.55))
        self.burst_capture   = BurstCapture(
            buffer_size=self.config['burst_buffer_size'],
            fps=self.config['burst_fps'])

        base_dir = Path(__file__).resolve().parent
        out_p    = Path(self.config['output_dir'])
        self.output_dir = out_p if out_p.is_absolute() else (base_dir / out_p)
        self.output_dir.mkdir(exist_ok=True)
        self.objects_dir = self.output_dir / 'detected_objects'; self.objects_dir.mkdir(exist_ok=True)
        self.faces_dir   = self.output_dir / 'detected_faces';   self.faces_dir.mkdir(exist_ok=True)
        self.burst_dir   = self.output_dir / 'burst_comparison'; self.burst_dir.mkdir(exist_ok=True)

        self.auto_motion_trigger = False
        self.motion_detected     = False
        self.last_motion_time    = 0
        self.motion_cooldown     = self.config['motion_cooldown']
        self.status_message      = "READY: PRESS [SPACE] OR [B] FOR BURST & DETECT"
        self.detection_times     = []
        self.total_detections    = 0
        self.active_detections   = []
        self.active_detection_time = 0

    def _load_config(self, config_path):
        defaults = {
            'camera_id': 0,
            'resolution': [640, 480],
            'burst_buffer_size': 15,
            'burst_fps': 20,
            'motion_cooldown': 2.0,
            'motion_threshold': 2500,
            'output_dir': './nex_output',
            'save_burst_comparison': True,
        }
        base_dir = Path(__file__).resolve().parent
        cfg_path = Path(config_path) if Path(config_path).is_absolute() else (base_dir / config_path)
        if cfg_path.exists():
            with open(cfg_path) as f:
                defaults.update(json.load(f))
        return defaults

    # Kept for backward compat
    def load_config(self, config_path):
        return self._load_config(config_path)

    def detect_motion(self, frame1, frame2):
        g1   = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        g2   = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(g1, g2)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        return np.sum(thresh) / 255 > self.config['motion_threshold']

    @staticmethod
    def draw_object_outline(frame, bbox, label="OBJECT", confidence=None,
                            color=(0, 255, 128), trace_contour=True, quad=None):
        x, y, w, h = bbox
        hf, wf = frame.shape[:2]
        x = max(0, min(x, wf - 1))
        y = max(0, min(y, hf - 1))
        w = max(1, min(w, wf - x))
        h = max(1, min(h, hf - y))

        # Perspective quad
        if quad is not None:
            try:
                poly = np.array(quad, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [poly], True,
                              tuple(c // 3 for c in color), 6)
                cv2.polylines(frame, [poly], True, color, 2)
            except Exception:
                pass

        # Contour trace
        if trace_contour and 16 < w < wf * 0.55 and 16 < h < hf * 0.55:
            try:
                roi    = frame[y:y+h, x:x+w]
                gray   = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                edges  = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 60, 160)
                dil    = cv2.dilate(edges, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
                cnts, _ = cv2.findContours(dil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in sorted(cnts, key=cv2.contourArea, reverse=True)[:3]:
                    if cv2.contourArea(cnt) > w * h * 0.08:
                        cv2.drawContours(roi, [cnt], -1, tuple(c // 3 for c in color), 4)
                        cv2.drawContours(roi, [cnt], -1, color, 2)
            except Exception:
                pass

        # Glow border
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x+w, y+h), color, 1)
        if x >= 2 and y >= 2 and x+w+2 <= wf and y+h+2 <= hf:
            cv2.rectangle(overlay, (x-2, y-2), (x+w+2, y+h+2), color, 2)
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

        # Corner brackets
        cl = max(8, min(24, min(w, h) // 4))
        tk = 3
        for cx_, cy_, dx, dy in [(x, y, 1, 1), (x+w, y, -1, 1),
                                  (x, y+h, 1, -1), (x+w, y+h, -1, -1)]:
            cv2.line(frame, (cx_, cy_), (cx_ + dx*cl, cy_), color, tk)
            cv2.line(frame, (cx_, cy_), (cx_, cy_ + dy*cl), color, tk)

        # Crosshair
        cx2, cy2 = x + w // 2, y + h // 2
        cv2.circle(frame, (cx2, cy2), 3, color, -1)
        cv2.line(frame, (cx2-7, cy2), (cx2+7, cy2), color, 1)
        cv2.line(frame, (cx2, cy2-7), (cx2, cy2+7), color, 1)

        # Label badge
        badge = f" {label.upper()} "
        if confidence is not None:
            badge += f"{int(confidence * 100)}% "
        font   = cv2.FONT_HERSHEY_SIMPLEX
        fs     = 0.52
        (tw, th), _ = cv2.getTextSize(badge, font, fs, 1)
        by1 = max(0, y - th - 10)
        by2 = y
        bty = y - 5
        if by1 == 0:
            by1 = y; by2 = y + th + 10; bty = y + th + 4
        cv2.rectangle(frame, (x, by1), (x + tw + 6, by2), color, -1)
        cv2.putText(frame, badge, (x+3, bty), font, fs, (0, 0, 0), 2)
        cv2.putText(frame, badge, (x+3, bty), font, fs, (255, 255, 255), 1)

    def save_detection_result(self, best_capture, detections, detection_type='object'):
        frame = best_capture['frame'].copy()
        score = best_capture['score']
        for det in detections:
            lbl   = det.get('object', 'OBJECT')
            color = (0, 255, 128) if ('VERIFIED' in lbl or 'SIFT' in lbl) else (255, 180, 0)
            self.draw_object_outline(frame, det['bbox'], label=lbl,
                                     confidence=det.get('confidence'),
                                     color=color, trace_contour=True, quad=det.get('quad'))
        cv2.putText(frame,
                    f"Quality: {score['total']:.1f} | Sharp: {score['sharpness']:.1f} | Total: {best_capture['total_captures']}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.putText(frame, datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        if detection_type == 'object' and detections:
            raw      = detections[0]['object'].split()[0]
            clean    = "".join(c for c in raw if c.isalnum() or c in ('_', '-'))
            filename = f"{clean}_{ts}.jpg"
            save_dir = self.objects_dir
            try:
                bx, by, bw, bh = detections[0]['bbox']
                mg  = int(max(bw, bh) * 0.08)
                hf2, wf2 = frame.shape[:2]
                crop = best_capture['frame'][max(0, by-mg):min(hf2, by+bh+mg),
                                             max(0, bx-mg):min(wf2, bx+bw+mg)]
                if crop.size > 0:
                    cv2.imwrite(str(save_dir / f"{clean}_crop_{ts}.jpg"), crop)
            except Exception:
                pass
        else:
            filename = f"face_{ts}.jpg"
            save_dir = self.faces_dir

        path = save_dir / filename
        cv2.imwrite(str(path), frame)
        return str(path)

    def save_burst_comparison(self, burst_frames):
        if not burst_frames or not self.config.get('save_burst_comparison', True):
            return None
        n    = len(burst_frames)
        cols = min(4, n)
        rows = (n + cols - 1) // cols
        fh, fw = burst_frames[0]['frame'].shape[:2]
        sc     = 0.35
        th, tw = int(fh * sc), int(fw * sc)
        grid   = np.zeros((rows * th, cols * tw, 3), dtype=np.uint8)

        for idx, item in enumerate(burst_frames):
            r, c   = idx // cols, idx % cols
            thumb  = cv2.resize(item['frame'], (tw, th))
            winner = (idx == 0)
            dets   = item.get('detections', [])
            has_d  = len(dets) > 0
            for d in dets:
                bx2, by2, bw2, bh2 = d['bbox']
                col2 = (0, 255, 128) if winner else (0, 220, 255)
                cv2.rectangle(thumb, (int(bx2*sc), int(by2*sc)),
                              (int((bx2+bw2)*sc), int((by2+bh2)*sc)), col2, 2)
            bc = (0,255,128) if winner and has_d else (0,255,128) if winner else (0,220,255) if has_d else (55,55,55)
            bth = 4 if (winner and has_d) else 3 if winner else 2 if has_d else 1
            cv2.rectangle(thumb, (0,0), (tw-1,th-1), bc, bth)
            first = dets[0]['object'].split()[0] if has_d else None
            cfv   = int(dets[0].get('confidence',0.8)*100) if has_d else 0
            if winner and has_d:
                txt, bg = f"#{idx+1} WINNER [{first} {cfv}%]", (0,160,70)
            elif winner:
                txt, bg = f"#{idx+1} WINNER Q:{item['score']['total']:.1f}", (0,140,60)
            elif has_d:
                txt, bg = f"#{idx+1} [{first} {cfv}%]", (140,100,0)
            else:
                txt, bg = f"#{idx+1} Q:{item['score']['total']:.1f}", (20,20,20)
            cv2.rectangle(thumb, (0,0), (min(tw,160),22), bg, -1)
            cv2.putText(thumb, txt, (5,15), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255,255,255), 1)
            cv2.putText(thumb, f"Sharp: {item['score']['sharpness']:.0f}",
                        (5, th-6), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,255,255), 1)
            grid[r*th:(r+1)*th, c*tw:(c+1)*tw] = thumb

        ts   = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        path = self.burst_dir / f'burst_comparison_{ts}.jpg'
        cv2.imwrite(str(path), grid)
        print(f"   📊 Burst saved: {path.name}")
        return str(path)

    def run_burst_detection(self, cap=None, frames_count=10):
        collected = []
        if cap is not None and cap.isOpened():
            for _ in range(frames_count):
                ret, frame = cap.read()
                if ret and frame is not None:
                    collected.append(cv2.flip(frame, 1))
                time.sleep(0.025)
        elif self.burst_capture.burst_buffer:
            with self.burst_capture.lock:
                collected = [item['frame'] for item in self.burst_capture.burst_buffer]
        if not collected:
            return None

        scored = []
        total_dt = 0.0
        for frame in collected:
            score = ImageQualityScorer.score_image(frame)
            dets, dt = self.object_detector.detect_all_objects(frame)
            total_dt += dt
            has_obj  = len(dets) > 0
            if has_obj:
                mc   = max(d.get('confidence', 0.5) for d in dets)
                vfy  = any('[VERIFIED]' in d.get('object', '') for d in dets)
                rank = 1000.0 + mc * 100.0 + (50.0 if vfy else 0.0) + score['total'] * 0.5
            else:
                rank = score['total']
            scored.append({'frame': frame, 'score': score, 'detections': dets,
                           'has_object': has_obj, 'rank_score': rank})

        scored.sort(key=lambda x: x['rank_score'], reverse=True)
        winner = scored[0]
        comp_path = self.save_burst_comparison(scored)
        saved_det_path = None
        winner_dets    = winner.get('detections', [])

        if winner_dets:
            saved_det_path = self.save_detection_result(
                {'frame': winner['frame'], 'score': winner['score'],
                 'total_captures': len(scored)},
                winner_dets, detection_type='object')
            self.active_detections     = winner_dets
            self.active_detection_time = time.time()
            self.total_detections     += len(winner_dets)
            print(f"🎯 DETECTED {len(winner_dets)}: {[d['object'] for d in winner_dets]}")
        else:
            print(f"ℹ️  No objects detected (winner quality: {winner['score']['total']:.1f})")

        return {'winner': winner, 'all_scored': scored,
                'detections': winner_dets, 'has_object': winner['has_object'],
                'comparison_path': comp_path, 'detection_path': saved_det_path,
                'detect_time_ms': total_dt}

    def run(self):
        print(f"\n📹 Opening camera {self.config['camera_id']}...")
        cap = cv2.VideoCapture(self.config['camera_id'])
        if not cap.isOpened():
            print("✗ Camera not found!")
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.config['resolution'][0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['resolution'][1])
        cap.set(cv2.CAP_PROP_FPS, 60)
        print(f"✓ Camera {self.config['resolution'][0]}x{self.config['resolution'][1]}")
        print(f"✓ Enrolled: {list(self.object_detector.object_templates.keys())}")
        print("\n🎯 DETECTION ACTIVE")
        print("   [SPACE]/[B] burst  [T] train  [D] delete  [Q] quit\n")

        prev_frame = None
        frame_count = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)
                frame_count += 1
                now = time.time()
                self.burst_capture.add_frame(frame)

                if prev_frame is not None:
                    if self.detect_motion(prev_frame, frame) and not self.motion_detected:
                        if now - self.last_motion_time > self.motion_cooldown:
                            self.motion_detected  = True
                            self.last_motion_time = now
                            self.burst_capture.start_burst()
                    elif not self.detect_motion(prev_frame, frame) and self.motion_detected:
                        self.motion_detected = False
                        best = self.burst_capture.stop_burst()
                        if best:
                            dets, dt = self.object_detector.detect_all_objects(best['frame'])
                            self.detection_times.append(dt)
                            if dets:
                                self.total_detections     += len(dets)
                                self.active_detections     = dets
                                self.active_detection_time = now
                                self.save_detection_result(best, dets)
                                print(f"   ✓ {dets[0]['object']} [{dets[0]['confidence']:.2f}]")
                prev_frame = frame.copy()

                display = frame.copy()
                if now - self.active_detection_time < 5.0:
                    for det in self.active_detections:
                        lbl   = det.get('object', 'OBJECT')
                        color = (0,255,128) if ('VERIFIED' in lbl or 'SIFT' in lbl) else (0,190,255)
                        self.draw_object_outline(display, det['bbox'], label=lbl,
                                                 confidence=det.get('confidence'),
                                                 color=color, quad=det.get('quad'))
                eng = "HYBRID: SIFT+NEURAL (MPS)" if self.object_detector.neural_enabled else "SIFT RANSAC"
                st  = f"BURST [{eng}]" if self.burst_capture.is_capturing else self.status_message
                cv2.putText(display, st, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                            (0,255,255) if self.burst_capture.is_capturing else (80,220,120), 2)
                cv2.putText(display, "[SPACE]/[B] Burst  [T] Train  [D] Delete  [Q] Quit",
                            (10, display.shape[0]-15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)
                cv2.imshow('NEX Core Detector', display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key in (ord('b'), 32):
                    res = self.run_burst_detection(cap=cap, frames_count=12)
                    if res and res.get('detections'):
                        d0 = res['detections'][0]
                        self.status_message = f"DETECTED: {d0['object']} ({int(d0['confidence']*100)}%)"
                    else:
                        self.status_message = "NO OBJECT DETECTED"
                elif key == ord('t'):
                    training_frame = frame.copy()
                    roi = cv2.selectROI("Select Object to Train", training_frame,
                                        fromCenter=False, showCrosshair=True)
                    cv2.destroyWindow("Select Object to Train")
                    if roi[2] > 20 and roi[3] > 20:
                        x, y, w, h = [int(v) for v in roi]
                        if w >= frame.shape[1] * 0.85 and h >= frame.shape[0] * 0.85:
                            print("❌ Selected area too large — select the object only")
                        else:
                            name = input("📝 Object name: ").strip()
                            if name:
                                self.object_detector.add_object(name, frame[y:y+h, x:x+w])
                elif key == ord('d'):
                    summary = self.object_detector.get_objects_summary()
                    if not summary:
                        print("No enrolled objects.")
                    else:
                        for i, item in enumerate(summary, 1):
                            print(f"  [{i}] {item['name']} ({item['template_count']} templates)")
                        choice = input("Number to delete (or A for all): ").strip().lower()
                        if choice == 'a' and input("Delete ALL? (yes/no): ").strip().lower() == 'yes':
                            self.object_detector.clear_all_objects()
                        elif choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx < len(summary):
                                self.object_detector.delete_object(summary[idx]['name'])
        except KeyboardInterrupt:
            pass
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print(f"\nTotal detections: {self.total_detections}")
            if self.detection_times:
                print(f"Avg detect time: {sum(self.detection_times)/len(self.detection_times):.1f}ms")


if __name__ == '__main__':
    NexCoreDetector().run()
