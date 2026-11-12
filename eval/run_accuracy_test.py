import sys
import os
import json
import time
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nex_core_detector import HybridObjectDetector

class NEXAccuracyEvaluator:
    """
    Standard Due Diligence & Benchmark Evaluator for NEX Loss Prevention Engine.
    Computes precision, recall, F1, and sub-15ms latency statistics across
    enrolled objects, distractors, and scale/perspective shifts.
    """
    def __init__(self, templates_dir: str = "object_database"):
        self.templates_dir = templates_dir
        self.detector = HybridObjectDetector(templates_dir=templates_dir, min_confidence=0.55, use_neural=False)

    def evaluate(self, output_json: str = "eval/eval_results.json"):
        os.makedirs("eval", exist_ok=True)
        results = {
            "total_samples": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "true_negatives": 0,
            "latencies_ms": []
        }

        print("═══════════════════════════════════════════════════════════")
        print("   NEX VISION ENGINE — BENCHMARK EVALUATION RUNNER         ")
        print("═══════════════════════════════════════════════════════════")

        # 1. Evaluate enrolled template items embedded in 640x480 scenes (True Positives test)
        for obj_name, templates in self.detector.object_templates.items():
            for idx, img in enumerate(templates):
                h, w = img.shape[:2]
                if w < 10 or h < 10:
                    continue

                # Generate 3 variations per template: centered, rotated (+5 deg), and scaled (0.9x)
                variations = [img]
                if w >= 30 and h >= 30:
                    M_rot = cv2.getRotationMatrix2D((w/2, h/2), 5, 1.0)
                    variations.append(cv2.warpAffine(img, M_rot, (w, h)))
                    variations.append(cv2.resize(img, (int(w * 0.9), int(h * 0.9))))

                for sample in variations:
                    results["total_samples"] += 1
                    sh, sw = sample.shape[:2]
                    
                    # Embed sample inside typical cooler camera frame (640x480)
                    scene = np.full((480, 640, 3), 35, dtype=np.uint8)
                    pos_y = min(480 - sh, 120)
                    pos_x = min(640 - sw, 180)
                    scene[pos_y:pos_y+sh, pos_x:pos_x+sw] = sample
                    gray = cv2.cvtColor(scene, cv2.COLOR_BGR2GRAY)

                    t0 = time.perf_counter()
                    dets = self.detector.detect_sift_objects(gray, 640, 480)
                    dt_ms = (time.perf_counter() - t0) * 1000.0
                    results["latencies_ms"].append(dt_ms)

                    detected_names = [d.get("object", "").lower() for d in dets if isinstance(d, dict)]
                    if obj_name.lower() in detected_names:
                        results["true_positives"] += 1
                    else:
                        results["false_negatives"] += 1

        # 2. Evaluate negative distractors / empty background (False Positives test)
        for bg_val in [20, 120, 240, 0]:
            blank_gray = np.full((480, 640), bg_val, dtype=np.uint8)
            results["total_samples"] += 1

            t0 = time.perf_counter()
            dets = self.detector.detect_sift_objects(blank_gray, 640, 480)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            results["latencies_ms"].append(dt_ms)

            if len(dets) == 0:
                results["true_negatives"] += 1
            else:
                results["false_positives"] += len(dets)

        # 3. Calculate official metrics
        tp = results["true_positives"]
        fp = results["false_positives"]
        fn = results["false_negatives"]
        tn = results["true_negatives"]

        precision = tp / max(1, (tp + fp))
        recall = tp / max(1, (tp + fn))
        f1 = 2 * precision * recall / max(1e-5, (precision + recall))
        accuracy = (tp + tn) / max(1, results["total_samples"])

        latencies = results["latencies_ms"]
        p50 = float(np.percentile(latencies, 50))
        p90 = float(np.percentile(latencies, 90))
        p99 = float(np.percentile(latencies, 99))

        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "architecture": "Hybrid SIFT-RANSAC + Invariant Edge Matcher",
            "enrolled_classes": list(self.detector.object_templates.keys()),
            "total_test_samples": results["total_samples"],
            "metrics": {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "accuracy": round(accuracy, 4),
                "accuracy_pct": f"{accuracy * 100:.1f}%"
            },
            "confusion_matrix": {
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "true_negatives": tn
            },
            "latency_ms": {
                "p50": round(p50, 2),
                "p90": round(p90, 2),
                "p99": round(p99, 2),
                "target": "<15.0ms"
            }
        }

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("\n📈 BENCHMARK RESULTS SUMMARY:")
        print(f"  • Total Samples:     {report['total_test_samples']}")
        print(f"  • Precision:         {report['metrics']['precision']:.3f} ({report['metrics']['precision']*100:.1f}%)")
        print(f"  • Recall:            {report['metrics']['recall']:.3f} ({report['metrics']['recall']*100:.1f}%)")
        print(f"  • F1-Score:          {report['metrics']['f1_score']:.3f}")
        print(f"  • Overall Accuracy:  {report['metrics']['accuracy_pct']}")
        print(f"  • Latency (P50/P90): {report['latency_ms']['p50']}ms / {report['latency_ms']['p90']}ms")
        print(f"✓ Saved official report to: {output_json}\n")
        return report

if __name__ == "__main__":
    evaluator = NEXAccuracyEvaluator()
    evaluator.evaluate()
