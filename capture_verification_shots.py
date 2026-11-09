#!/usr/bin/env python3
import subprocess
import os
import time

out_dir = "/tmp/nex_verify"
os.makedirs(out_dir, exist_ok=True)

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

tests = [
    ("stage0_standby.png", "http://localhost:8000/index.html?p=0.00", "1440,900"),
    ("stage1_approach.png", "http://localhost:8000/index.html?p=0.35", "1440,900"),
    ("stage2_door_opening.png", "http://localhost:8000/index.html?p=0.55", "1440,900"),
    ("stage3_steadicam_transition.png", "http://localhost:8000/index.html?p=0.75", "1440,900"),
    ("stage3_pod_approach.png", "http://localhost:8000/index.html?p=0.88", "1440,900"),
    ("stage3_lens_plunge.png", "http://localhost:8000/index.html?p=0.98", "1440,900"),
    ("panel1_blindspot.png", "http://localhost:8000/index.html?section=panels#panel-1", "1440,900"),
    ("panel2_theft_vault.png", "http://localhost:8000/index.html?section=panels#panel-2", "1440,900"),
    ("panel3_lockout.png", "http://localhost:8000/index.html?section=panels#panel-3", "1440,900"),
    ("panel4_retrofit.png", "http://localhost:8000/index.html?section=panels#panel-4", "1440,900"),
]

for filename, url, win_size in tests:
    target_path = os.path.join(out_dir, filename)
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        f"--screenshot={target_path}",
        f"--window-size={win_size}",
        "--virtual-time-budget=2000",
        "--hide-scrollbars",
        url
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(target_path):
        size = os.path.getsize(target_path)
        print(f"Captured {filename:32s}: {size:8d} bytes")
    else:
        print(f"FAILED to capture {filename}")

print("Verification capture run completed!")
