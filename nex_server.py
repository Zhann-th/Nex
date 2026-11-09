#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
NEX VISION CORE — OBJECT DATABASE & DATA MANAGEMENT SERVER
═══════════════════════════════════════════════════════════════════
High-performance asynchronous FastAPI & Web Dashboard for:
1. Object Management: Enrolling, viewing, and completely deleting
   detection objects (SIFT keypoints + YOLO-World vocabulary).
2. Data Vault: Managing, inspecting, filtering, and deleting captured
   detection snapshots (objects, faces, burst comparisons).
3. Live Feed: Real-time video monitoring with detection overlays.
═══════════════════════════════════════════════════════════════════
"""

import os
import sys
import time
import shutil
import base64
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add local directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from nex_core_detector import HybridObjectDetector, ImageQualityScorer, BurstCapture

# Initialize directories
TEMPLATES_DIR = BASE_DIR / 'object_database'
OUTPUT_DIR = BASE_DIR / 'nex_output'
TEMPLATES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / 'detected_objects').mkdir(exist_ok=True)
(OUTPUT_DIR / 'detected_faces').mkdir(exist_ok=True)
(OUTPUT_DIR / 'burst_comparison').mkdir(exist_ok=True)

# Shared Global Detector instance
detector = HybridObjectDetector(templates_dir=str(TEMPLATES_DIR), min_confidence=0.60, use_neural=True)

# Thread-safe Camera Stream Manager
class CameraManager:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.lock = threading.Lock()
        self.cap_lock = threading.Lock()
        self.is_running = False
        self.last_frame = None
        self.last_raw_frame = None
        self.active_detections = []
        self.last_det_time = 0
        self.thread = None
        self.burst_active = False
        self.burst_frames = []

    def start(self):
        with self.lock:
            if self.is_running:
                return
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                print(f"⚠️ Camera {self.camera_id} not available")
                return
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            print("✓ Camera stream manager started (Mirroring & On-Demand Burst active)")

    def _capture_loop(self):
        frame_idx = 0
        while self.is_running and self.cap and self.cap.isOpened():
            with self.cap_lock:
                ret, frame = self.cap.read()

            if not ret or frame is None:
                time.sleep(0.03)
                continue

            frame_idx += 1
            now = time.time()

            # Mirror horizontally for natural selfie/mirror camera view
            frame = cv2.flip(frame, 1)

            with self.lock:
                self.last_raw_frame = frame.copy()
                if self.burst_active:
                    self.burst_frames.append(frame.copy())

            # Render detection overlay on stream copy (holds recent burst detection for 5 seconds)
            display = frame.copy()
            if now - self.last_det_time < 5.0:
                for det in self.active_detections:
                    bbox = det['bbox']
                    label = det.get('object', 'OBJECT')
                    conf = det.get('confidence', 0.8)
                    x, y, w, h = bbox
                    color = (0, 255, 128) if ('VERIFIED' in label or 'SIFT' in label) else (0, 190, 255)

                    # Bounding Box
                    cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
                    txt = f"{label} {int(conf * 100)}%"
                    cv2.putText(display, txt, (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

                    # Safe Quad contour if SIFT homography
                    if 'quad' in det and det['quad'] is not None:
                        try:
                            quad = np.array(det['quad'], dtype=np.int32).reshape((-1, 1, 2))
                            cv2.polylines(display, [quad], isClosed=True, color=(0, 255, 255), thickness=2)
                        except Exception:
                            pass

            with self.lock:
                self.last_frame = display

            time.sleep(0.02)

    def get_frame(self):
        with self.lock:
            return self.last_frame

    def get_raw_frame(self):
        with self.lock:
            if self.last_raw_frame is not None:
                return self.last_raw_frame.copy()
        if self.cap and self.cap.isOpened():
            with self.cap_lock:
                ret, frame = self.cap.read()
            if ret and frame is not None:
                return cv2.flip(frame, 1)
        return self.last_frame

    def run_burst_comparison_and_detection(self, count=12):
        """
        Executes on-demand burst capture and detection:
        1. Captures a rapid sequence of frames from camera
        2. Evaluates sharpness, contrast and brightness with ImageQualityScorer
        3. Ranks frames and selects sharpest winner without blur
        4. Stitches and saves burst comparison grid with winner highlighted
        5. Runs hybrid object detection on winner
        6. If detected, saves snapshot and displays overlay on live stream
        """
        burst_frames = []
        with self.lock:
            self.burst_frames = []
            self.burst_active = True

        # Wait for count frames to be captured in the stream loop
        start_t = time.time()
        while len(burst_frames) < count and time.time() - start_t < 1.5:
            with self.lock:
                if len(self.burst_frames) >= count:
                    burst_frames = list(self.burst_frames[:count])
                    break
            time.sleep(0.02)

        with self.lock:
            self.burst_active = False

        # Fallback if not enough frames from background thread
        if len(burst_frames) < 3 and self.cap and self.cap.isOpened():
            with self.cap_lock:
                for _ in range(count):
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        burst_frames.append(cv2.flip(frame, 1))
                    time.sleep(0.025)

        if not burst_frames:
            if self.last_raw_frame is not None:
                burst_frames = [self.last_raw_frame.copy()]
            else:
                fallback_img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(fallback_img, "NEX CAMERA FEED READY", (140, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                burst_frames = [fallback_img]

        # Score all frames and run object detection across ALL burst frames
        scored = []
        total_detect_ms = 0.0

        for f in burst_frames:
            score = ImageQualityScorer.score_image(f)
            dets, dt = detector.detect_all_objects(f)
            total_detect_ms += dt
            has_obj = len(dets) > 0

            # Priority ranking: ANY frame with an object ALWAYS ranks higher than frames without
            if has_obj:
                max_conf = max(d.get('confidence', 0.5) for d in dets)
                is_verified = any('[VERIFIED]' in d.get('object', '') for d in dets)
                # Base 1000 + confidence boost + verification bonus + quality factor
                rank_score = 1000.0 + (max_conf * 100.0) + (50.0 if is_verified else 0.0) + (score['total'] * 0.5)
            else:
                rank_score = score['total']

            scored.append({
                'frame': f,
                'score': score,
                'detections': dets,
                'has_object': has_obj,
                'rank_score': rank_score
            })

        # Rank: frames with objects win! Among them, highest confidence and sharpness wins!
        scored.sort(key=lambda x: x['rank_score'], reverse=True)
        winner = scored[0]

        # Save burst comparison grid
        comp_dir = OUTPUT_DIR / 'burst_comparison'
        comp_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        comp_filename = f"burst_comparison_{timestamp}.jpg"
        comp_path = comp_dir / comp_filename

        n_frames = len(scored)
        cols = min(4, n_frames)
        rows = (n_frames + cols - 1) // cols
        fh, fw = scored[0]['frame'].shape[:2]
        scale = 0.35
        th, tw = int(fh * scale), int(fw * scale)
        comparison = np.zeros((rows * th, cols * tw, 3), dtype=np.uint8)

        for idx, item in enumerate(scored):
            r = idx // cols
            c = idx % cols
            thumb = cv2.resize(item['frame'], (tw, th))
            is_win = (idx == 0)
            item_dets = item.get('detections', [])
            item_has_obj = len(item_dets) > 0

            # If thumbnail has detected object, draw bounding box on thumbnail
            if item_has_obj:
                for d in item_dets:
                    bx, by, bw, bh = d['bbox']
                    tbx, tby = int(bx * scale), int(by * scale)
                    tbw, tbh = int(bw * scale), int(bh * scale)
                    bcol = (0, 255, 128) if is_win else (0, 220, 255)
                    cv2.rectangle(thumb, (tbx, tby), (tbx + tbw, tby + tbh), bcol, 2)

            # Border
            if is_win and item_has_obj:
                b_col = (0, 255, 128)
                b_thick = 4
            elif is_win:
                b_col = (0, 255, 128)
                b_thick = 3
            elif item_has_obj:
                b_col = (0, 220, 255)
                b_thick = 2
            else:
                b_col = (55, 55, 55)
                b_thick = 1
            cv2.rectangle(thumb, (0, 0), (tw - 1, th - 1), b_col, b_thick)

            # Badge
            first_obj = item_dets[0]['object'].split()[0] if item_has_obj else None
            conf_pct = int(item_dets[0].get('confidence', 0.8) * 100) if item_has_obj else 0

            if is_win and item_has_obj:
                badge_txt = f"#{idx+1} WINNER [{first_obj} {conf_pct}%]"
                badge_bg = (0, 160, 70)
            elif is_win:
                badge_txt = f"#{idx+1} WINNER Q:{item['score']['total']:.1f}"
                badge_bg = (0, 140, 60)
            elif item_has_obj:
                badge_txt = f"#{idx+1} [{first_obj} {conf_pct}%]"
                badge_bg = (140, 100, 0)
            else:
                badge_txt = f"#{idx+1} Q:{item['score']['total']:.1f}"
                badge_bg = (20, 20, 20)

            cv2.rectangle(thumb, (0, 0), (min(tw, 160), 22), badge_bg, -1)
            cv2.putText(thumb, badge_txt, (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)

            sharp_txt = f"Sharp: {item['score']['sharpness']:.0f}"
            cv2.putText(thumb, sharp_txt, (5, th - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)

            comparison[r*th:(r+1)*th, c*tw:(c+1)*tw] = thumb

        cv2.imwrite(str(comp_path), comparison)

        # Annotate and outline winner frame
        dets = winner.get('detections', [])
        det_filename = None
        crop_filename = None
        winner_annotated = winner['frame'].copy()

        if dets:
            w_h, w_w = winner_annotated.shape[:2]
            for det in dets:
                label = det.get('object', 'OBJECT')
                conf = det.get('confidence', 0.8)
                x, y, w, h = det['bbox']
                color = (0, 255, 128) if ('VERIFIED' in label or 'SIFT' in label) else (0, 210, 255)

                # 1. Semi-transparent glow box
                overlay = winner_annotated.copy()
                cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
                cv2.addWeighted(overlay, 0.45, winner_annotated, 0.55, 0, winner_annotated)

                # 2. Cyber corner brackets
                corner_len = max(8, min(25, min(w, h) // 4))
                cv2.line(winner_annotated, (x, y), (x + corner_len, y), color, 3)
                cv2.line(winner_annotated, (x, y), (x, y + corner_len), color, 3)
                cv2.line(winner_annotated, (x + w, y), (x + w - corner_len, y), color, 3)
                cv2.line(winner_annotated, (x + w, y), (x + w, y + corner_len), color, 3)
                cv2.line(winner_annotated, (x, y + h), (x + corner_len, y + h), color, 3)
                cv2.line(winner_annotated, (x, y + h), (x, y + h - corner_len), color, 3)
                cv2.line(winner_annotated, (x + w, y + h), (x + w - corner_len, y + h), color, 3)
                cv2.line(winner_annotated, (x + w, y + h), (x + w, y + h - corner_len), color, 3)

                # 3. Center targeting reticle
                cx, cy = x + w // 2, y + h // 2
                cv2.circle(winner_annotated, (cx, cy), 3, color, -1)
                cv2.line(winner_annotated, (cx - 7, cy), (cx + 7, cy), color, 1)
                cv2.line(winner_annotated, (cx, cy - 7), (cx, cy + 7), color, 1)

                # 4. Polygon contour / quad if available
                if 'quad' in det and det['quad'] is not None:
                    try:
                        quad = np.array(det['quad'], dtype=np.int32).reshape((-1, 1, 2))
                        cv2.polylines(winner_annotated, [quad], isClosed=True, color=(0, 255, 255), thickness=2)
                    except Exception:
                        pass

                # 5. Label badge
                txt = f" {label.upper()} {int(conf * 100)}% "
                (tw_txt, th_txt), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                by = max(th_txt + 8, y)
                cv2.rectangle(winner_annotated, (x, by - th_txt - 8), (x + tw_txt + 8, by), color, -1)
                cv2.putText(winner_annotated, txt, (x + 4, by - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
                cv2.putText(winner_annotated, txt, (x + 4, by - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

            # Save outlined snapshot to objects folder (detected_objects/)
            obj_dir = OUTPUT_DIR / 'detected_objects'
            obj_dir.mkdir(exist_ok=True)
            clean_name = "".join(c for c in dets[0]['object'].split()[0] if c.isalnum() or c in ('_', '-')) or "object"
            det_filename = f"{clean_name}_{timestamp}.jpg"
            cv2.imwrite(str(obj_dir / det_filename), winner_annotated)

            # Also save tight crop into detected_objects/
            try:
                x, y, w, h = dets[0]['bbox']
                crop_margin = int(max(w, h) * 0.08)
                h_f, w_f = winner['frame'].shape[:2]
                cx1 = max(0, x - crop_margin)
                cy1 = max(0, y - crop_margin)
                cx2 = min(w_f, x + w + crop_margin)
                cy2 = min(h_f, y + h + crop_margin)
                crop_img = winner['frame'][cy1:cy2, cx1:cx2]
                if crop_img.size > 0:
                    crop_filename = f"{clean_name}_crop_{timestamp}.jpg"
                    cv2.imwrite(str(obj_dir / crop_filename), crop_img)
            except Exception:
                pass

            with self.lock:
                self.active_detections = dets
                self.last_det_time = time.time()  # Hold active on stream

        # Encode winner display frame to b64 for instant frontend preview
        ret, buf = cv2.imencode('.jpg', winner_annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        winner_b64 = f"data:image/jpeg;base64,{base64.b64encode(buf).decode('utf-8')}" if ret else None

        return {
            "success": True,
            "has_object": winner['has_object'],
            "winner_score": {
                "total": round(winner['score']['total'], 1),
                "sharpness": round(winner['score']['sharpness'], 1),
                "brightness": round(winner['score']['brightness'], 1),
                "contrast": round(winner['score']['contrast'], 1)
            },
            "frames_analyzed": len(scored),
            "detected_count": len(dets),
            "detections": dets,
            "comparison_url": f"/api/files/output/burst_comparison/{comp_filename}",
            "detection_snapshot_url": f"/api/files/output/detected_objects/{det_filename}" if det_filename else None,
            "crop_snapshot_url": f"/api/files/output/detected_objects/{crop_filename}" if crop_filename else None,
            "winner_preview_b64": winner_b64,
            "detect_time_ms": round(total_detect_ms, 1)
        }

    def stop(self):
        with self.lock:
            self.is_running = False
            if self.cap:
                with self.cap_lock:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                self.cap = None
            self.last_frame = None
            self.last_raw_frame = None
            self.thread = None
        print("✓ Camera stream stopped and hardware device released")

camera_manager = CameraManager()

# FastAPI Application
app = FastAPI(
    title="NEX Core Object & Data Management API",
    description="Interface for managing detection objects, deleting trained targets, and controlling captured data.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════
class TrainObjectRequest(BaseModel):
    name: str
    image_base64: str  # Base64 data URL or raw base64 string

class CleanDataRequest(BaseModel):
    category: Optional[str] = "all"  # "all", "detected_objects", "detected_faces", "burst_comparison"


# ═══════════════════════════════════════════════════════════════════
# STATIC, LANDING & DASHBOARD ROUTES
# ═══════════════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def get_landing():
    landing_file = BASE_DIR / "index.html"
    if landing_file.exists():
        return HTMLResponse(content=landing_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>NEX Vision Mart — Landing loading...</h2>")


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    dashboard_file = BASE_DIR / "nex_dashboard.html"
    if dashboard_file.exists():
        return HTMLResponse(content=dashboard_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>NEX Dashboard loading...</h2>")


@app.get("/fonts/{font_name:path}")
async def get_font_file(font_name: str):
    font_file = (BASE_DIR / "fonts" / font_name).resolve()
    if not str(font_file).startswith(str((BASE_DIR / "fonts").resolve())):
        raise HTTPException(status_code=403, detail="Forbidden")
    if font_file.exists() and font_file.is_file():
        return FileResponse(str(font_file), media_type="font/woff2")
    raise HTTPException(status_code=404, detail="Font not found")


# ═══════════════════════════════════════════════════════════════════
# 1. OBJECT DATABASE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/objects")
async def list_objects():
    """Returns all enrolled detection objects with templates, keypoints, and sizes"""
    summary = detector.get_objects_summary()
    # Format template URLs for web consumption
    for obj in summary:
        for tpl in obj['templates']:
            tpl['url'] = f"/api/files/object_database/{obj['name']}/{tpl['filename']}"
    return {
        "success": True,
        "total_objects": len(summary),
        "objects": summary,
        "neural_enabled": detector.neural_enabled,
        "device": detector.device.upper() if detector.neural_enabled else "CPU"
    }


@app.post("/api/objects/train")
async def train_object(data: TrainObjectRequest):
    """Enrolls a new object or additional angle to existing object"""
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Имя объекта не может быть пустым")

    # Sanitize name
    clean_name = "".join(c for c in name if c.isalnum() or c in ('_', '-', ' ')).strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Недопустимое имя объекта")

    # Decode base64
    raw_b64 = data.image_base64
    if "," in raw_b64:
        raw_b64 = raw_b64.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(raw_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Не удалось декодировать изображение")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка декодирования фото: {str(e)}")

    h, w = img.shape[:2]
    if w < 20 or h < 20:
        raise HTTPException(status_code=400, detail="Изображение слишком маленькое (< 20px)")

    # Add to detector
    success = detector.add_object(clean_name, img)
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось добавить объект в базу детектора")

    feat_list = detector.template_features.get(clean_name, [])
    total_kp = sum(len(f['kp']) for f in feat_list) if feat_list else 0

    return {
        "success": True,
        "name": clean_name,
        "dimensions": f"{w}x{h}px",
        "total_keypoints": total_kp,
        "message": f"Объект '{clean_name}' успешно зарегистрирован и активирован в ИИ!"
    }


@app.delete("/api/objects/{name}")
async def delete_object(name: str):
    """Completely deletes an object category from disk and detector memory"""
    # Verify object exists
    obj_dir = TEMPLATES_DIR / name
    exists_on_disk = obj_dir.exists()
    exists_in_mem = name in detector.object_templates or name in detector.template_features

    if not exists_on_disk and not exists_in_mem:
        raise HTTPException(status_code=404, detail=f"Объект '{name}' не найден в базе")

    success = detector.delete_object(name)
    return {
        "success": True,
        "name": name,
        "message": f"Объект '{name}' полностью удален из базы и из памяти детектора"
    }


@app.delete("/api/objects/{name}/template/{filename}")
async def delete_template(name: str, filename: str):
    """Deletes a specific template image from an object"""
    file_path = TEMPLATES_DIR / name / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл шаблона не найден")

    success = detector.delete_template(name, filename)
    return {
        "success": success,
        "message": f"Шаблон '{filename}' объекта '{name}' удален"
    }


@app.delete("/api/objects")
async def clear_all_objects():
    """Completely deletes ALL enrolled objects"""
    detector.clear_all_objects()
    return {
        "success": True,
        "message": "Все объекты детекции полностью удалены из базы"
    }


# ═══════════════════════════════════════════════════════════════════
# 2. DATA VAULT & GALLERY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/data")
async def list_data(category: Optional[str] = "all"):
    """Lists all captured snapshots and detections in nex_output"""
    categories = ['detected_objects', 'detected_faces', 'burst_comparison']
    if category != "all" and category in categories:
        target_cats = [category]
    else:
        target_cats = categories

    files_list = []
    total_size_bytes = 0
    cat_counts = {c: 0 for c in categories}

    for cat in categories:
        cat_dir = OUTPUT_DIR / cat
        if not cat_dir.exists():
            continue

        for f in cat_dir.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                cat_counts[cat] += 1
                stat = f.stat()
                total_size_bytes += stat.st_size

                if cat in target_cats:
                    files_list.append({
                        "filename": f.name,
                        "category": cat,
                        "url": f"/api/files/output/{cat}/{f.name}",
                        "size_kb": round(stat.st_size / 1024, 1),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        "timestamp": stat.st_mtime
                    })

    # Sort newest first
    files_list.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "success": True,
        "total_files": sum(cat_counts.values()),
        "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
        "counts": cat_counts,
        "files": files_list
    }


@app.delete("/api/data/{category}/{filename}")
async def delete_data_file(category: str, filename: str):
    """Deletes a specific snapshot file"""
    if category not in ['detected_objects', 'detected_faces', 'burst_comparison']:
        raise HTTPException(status_code=400, detail="Неверная категория данных")

    target_file = OUTPUT_DIR / category / filename
    if not target_file.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    target_file.unlink()
    return {
        "success": True,
        "category": category,
        "filename": filename,
        "message": f"Файл {filename} успешно удален"
    }


@app.post("/api/data/clean")
async def clean_data(req: CleanDataRequest):
    """Batch cleans captured snapshots in one or all categories"""
    categories = ['detected_objects', 'detected_faces', 'burst_comparison']
    target_cats = categories if req.category == "all" else [req.category]

    deleted_count = 0
    freed_bytes = 0

    for cat in target_cats:
        cat_dir = OUTPUT_DIR / cat
        if not cat_dir.exists():
            continue
        for f in cat_dir.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                try:
                    size = f.stat().st_size
                    f.unlink()
                    deleted_count += 1
                    freed_bytes += size
                except Exception:
                    pass

    return {
        "success": True,
        "deleted_count": deleted_count,
        "freed_mb": round(freed_bytes / (1024 * 1024), 2),
        "message": f"Очищено {deleted_count} файлов ({round(freed_bytes / (1024 * 1024), 2)} МБ)"
    }


# ═══════════════════════════════════════════════════════════════════
# 3. LIVE CAMERA & SYSTEM STATS
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/stats")
async def get_system_stats():
    """Returns real-time system metrics, hardware acceleration, and counts"""
    summary = detector.get_objects_summary()

    total_snapshots = 0
    total_data_bytes = 0
    for cat in ['detected_objects', 'detected_faces', 'burst_comparison']:
        cat_dir = OUTPUT_DIR / cat
        if cat_dir.exists():
            for f in cat_dir.iterdir():
                if f.is_file() and not f.name.startswith('.'):
                    total_snapshots += 1
                    total_data_bytes += f.stat().st_size

    return {
        "success": True,
        "neural_enabled": detector.neural_enabled,
        "device": detector.device.upper() if detector.neural_enabled else "CPU",
        "objects_count": len(summary),
        "total_templates": sum(o['template_count'] for o in summary),
        "snapshots_count": total_snapshots,
        "storage_mb": round(total_data_bytes / (1024 * 1024), 2),
        "camera_active": camera_manager.is_running
    }


# ═══════════════════════════════════════════════════════════════════
# 4. CAMERA CONTROLS (ON / OFF / STATUS)
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/camera/status")
async def get_camera_status():
    """Returns current camera running status"""
    return {
        "success": True,
        "is_running": camera_manager.is_running
    }


@app.post("/api/camera/start")
async def start_camera():
    """Starts camera capture thread and hardware"""
    if not camera_manager.is_running:
        camera_manager.start()
    return {
        "success": True,
        "is_running": camera_manager.is_running,
        "message": "Камера успешно включена"
    }


@app.post("/api/camera/stop")
async def stop_camera():
    """Stops camera capture thread and completely releases webcam hardware"""
    if camera_manager.is_running:
        camera_manager.stop()
    return {
        "success": True,
        "is_running": False,
        "message": "Камера выключена (питание снято)"
    }


@app.post("/api/camera/toggle")
async def toggle_camera():
    """Toggles camera on/off"""
    if camera_manager.is_running:
        camera_manager.stop()
        new_state = False
    else:
        camera_manager.start()
        new_state = camera_manager.is_running

    return {
        "success": True,
        "is_running": new_state,
        "message": "Камера включена" if new_state else "Камера выключена"
    }


@app.get("/api/stream")
def video_stream():
    """MJPEG Live stream with real-time detection boxes and offline standby screen"""
    def generate_frames():
        while True:
            if not camera_manager.is_running:
                # Modern tech standby screen when camera is OFF
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                placeholder[:] = (12, 16, 24)
                # Grid lines
                for y in range(0, 480, 40):
                    cv2.line(placeholder, (0, y), (640, y), (18, 24, 36), 1)
                for x in range(0, 640, 40):
                    cv2.line(placeholder, (x, 0), (x, 480), (18, 24, 36), 1)

                cv2.putText(placeholder, "NEX CAMERA IS OFF", (190, 220),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 51, 102), 2)
                cv2.putText(placeholder, "[ HARDWARE RELEASED // ПИТАНИЕ СНЯТО ]", (125, 255),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (138, 153, 173), 1)
                cv2.putText(placeholder, "Нажмите 'Включить камеру' для запуска", (150, 290),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 255), 1)
                frame = placeholder
            else:
                frame = camera_manager.get_frame()
                if frame is None:
                    placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(placeholder, "CONNECTING TO CAMERA SENSOR...", (140, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 136), 2)
                    frame = placeholder

            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                time.sleep(0.04)
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.033 if camera_manager.is_running else 0.1)

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/api/capture_frame")
async def capture_frame():
    """Captures a single raw frame from camera for visual ROI training in browser"""
    if not camera_manager.is_running:
        camera_manager.start()
        time.sleep(0.5)

    frame = camera_manager.get_raw_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="Камера недоступна")

    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ret:
        raise HTTPException(status_code=500, detail="Ошибка кодирования кадра")

    b64_str = base64.b64encode(buffer.tobytes()).decode('utf-8')
    return {
        "success": True,
        "image_base64": f"data:image/jpeg;base64,{b64_str}",
        "width": frame.shape[1],
        "height": frame.shape[0]
    }


@app.post("/api/burst_detect")
async def trigger_burst_detect():
    """
    On-Demand Burst Comparison & Detection Endpoint:
    Captures a series of frames, ranks quality, selects winner,
    generates burst comparison grid, and detects enrolled objects on winner.
    """
    if not camera_manager.is_running:
        camera_manager.start()
        time.sleep(0.5)

    res = camera_manager.run_burst_comparison_and_detection(count=12)
    return res


# ═══════════════════════════════════════════════════════════════════
# 4. STATIC FILE SERVING WITH PATH TRAVERSAL GUARDS
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/files/{storage}/{subpath:path}")
async def serve_file(storage: str, subpath: str):
    """Safely serves images from object_database or nex_output"""
    if storage == "object_database":
        base = TEMPLATES_DIR
    elif storage == "output":
        base = OUTPUT_DIR
    else:
        raise HTTPException(status_code=400, detail="Неверное хранилище")

    target = (base / subpath).resolve()
    # Path traversal protection
    if not str(target).startswith(str(base.resolve())):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(str(target))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting NEX Management Server on http://localhost:{port}")
    uvicorn.run("nex_server:app", host="0.0.0.0", port=port, reload=False)
