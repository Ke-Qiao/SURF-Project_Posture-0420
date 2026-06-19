"""Auto-annotate images with 5 keypoints in YOLOv8 Pose format.

Uses MediaPipe Pose to detect landmarks, picks the camera-facing side
(decision #1), extracts 5 keypoints (ear / shoulder / hip / knee / ankle),
and writes one ``.txt`` label file per image in YOLOv8 Pose format.

Also generates a ``data.yaml`` config for training.

Label format (per line)
-----------------------
    class_id  cx  cy  w  h  kp1_x kp1_y kp1_v  kp2_x kp2_y kp2_v  ...

All coordinates are normalised to [0, 1].  Visibility flags:
    0 = not labelled,  1 = labelled but occluded,  2 = labelled and visible.

Usage
-----
    python scripts/auto_annotate.py \\
        --input  data/filtered/good  data/filtered/bad \\
        --output data/annotated \\
        --split  0.8

This produces:
    data/annotated/
        images/train/  images/val/
        labels/train/  labels/val/
        data.yaml
"""

from __future__ import annotations

import argparse
import math
import os
import random
import shutil
import sys

# Allow importing the posture package from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import yaml

from posture.analyzer import pick_side
from posture.config import LEFT_SIDE_IDS, RIGHT_SIDE_IDS
from posture.detector import PoseDetector

# ── Config ──────────────────────────────────────────────────────────────

# Keypoint order in the label file (Decision #6: 5 keypoints)
KEYPOINT_ORDER = ["ear", "shoulder", "hip", "knee", "ankle"]
NUM_KPT = len(KEYPOINT_ORDER)

_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


# ── CLI ─────────────────────────────────────────────────────────────────


def _parse_args():
    p = argparse.ArgumentParser(
        description="Auto-annotate images with 5 keypoints (YOLOv8 Pose format)",
    )
    p.add_argument(
        "--input", nargs="+", required=True,
        help="One or more directories containing images",
    )
    p.add_argument(
        "--output", default="data/annotated",
        help="Output root directory (default: data/annotated)",
    )
    p.add_argument(
        "--split", type=float, default=0.8,
        help="Train fraction (default: 0.8, remainder goes to val)",
    )
    p.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for train/val split (default: 42)",
    )
    return p.parse_args()


# ── Annotation logic ────────────────────────────────────────────────────


def _bounding_box(kpts: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Compute a bounding box (cx, cy, w, h) from keypoints, with padding.

    All values are normalised [0, 1].
    """
    xs = [x for x, y in kpts]
    ys = [y for x, y in kpts]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    # Add 15 % padding on each side
    pad_x = (x_max - x_min) * 0.15
    pad_y = (y_max - y_min) * 0.15

    x_min = max(0.0, x_min - pad_x)
    x_max = min(1.0, x_max + pad_x)
    y_min = max(0.0, y_min - pad_y)
    y_max = min(1.0, y_max + pad_y)

    cx = (x_min + x_max) / 2
    cy = (y_min + y_max) / 2
    w = x_max - x_min
    h = y_max - y_min
    return cx, cy, w, h


def annotate_image(detector: PoseDetector, img_path: str) -> str | None:
    """Return the YOLOv8 Pose label line for one image, or None if failed."""
    frame = cv2.imread(img_path)
    if frame is None:
        return None

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = detector.process(rgb)
    landmarks = detector.get_landmarks(results)

    if landmarks is None:
        return None

    # Pick the camera-facing side
    _, side_ids = pick_side(landmarks)

    # Extract the 5 keypoints
    kpts: list[tuple[float, float, int]] = []
    kpts_xy: list[tuple[float, float]] = []

    for name in KEYPOINT_ORDER:
        lm = landmarks[side_ids[name]]
        vis = 2 if lm.visibility > 0.5 else 1
        kpts.append((lm.x, lm.y, vis))
        kpts_xy.append((lm.x, lm.y))

    # Bounding box
    cx, cy, w, h = _bounding_box(kpts_xy)

    # Format: class_id cx cy w h  kp1_x kp1_y kp1_v  kp2_x kp2_y kp2_v  ...
    parts = [f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"]
    for kx, ky, kv in kpts:
        parts.append(f"{kx:.6f} {ky:.6f} {kv}")

    return " ".join(parts)


# ── Main ────────────────────────────────────────────────────────────────


def main() -> None:
    args = _parse_args()

    out_root = args.output

    # Collect all image files from input directories
    all_images: list[str] = []
    for d in args.input:
        if not os.path.isdir(d):
            print(f"Warning: '{d}' is not a directory, skipping.")
            continue
        for f in sorted(os.listdir(d)):
            if os.path.splitext(f)[1].lower() in _IMG_EXTS:
                all_images.append(os.path.join(d, f))

    if not all_images:
        print("No images found.")
        return

    print(f"Found {len(all_images)} images across {len(args.input)} directories.")

    # Shuffle and split
    random.seed(args.seed)
    random.shuffle(all_images)
    split_idx = int(len(all_images) * args.split)
    train_imgs = all_images[:split_idx]
    val_imgs = all_images[split_idx:]

    print(f"Train: {len(train_imgs)}  Val: {len(val_imgs)}")

    # Create output directories
    for subset in ("train", "val"):
        os.makedirs(os.path.join(out_root, "images", subset), exist_ok=True)
        os.makedirs(os.path.join(out_root, "labels", subset), exist_ok=True)

    # Annotate
    detector = PoseDetector(static_image_mode=True)
    stats = {"train_ok": 0, "train_fail": 0, "val_ok": 0, "val_fail": 0}

    for subset, img_list in [("train", train_imgs), ("val", val_imgs)]:
        print(f"\nAnnotating {subset} ({len(img_list)} images)…")
        for img_path in img_list:
            fname = os.path.basename(img_path)
            base, _ = os.path.splitext(fname)

            label_line = annotate_image(detector, img_path)

            if label_line is None:
                stats[f"{subset}_fail"] += 1
                print(f"  [FAIL] {fname}")
                continue

            # Copy image
            shutil.copy2(
                img_path,
                os.path.join(out_root, "images", subset, fname),
            )
            # Write label
            label_path = os.path.join(out_root, "labels", subset, f"{base}.txt")
            with open(label_path, "w") as f:
                f.write(label_line + "\n")

            stats[f"{subset}_ok"] += 1

    detector.close()

    # Write data.yaml
    yaml_path = os.path.join(out_root, "data.yaml")
    data_cfg = {
        "path": os.path.abspath(out_root),
        "train": "images/train",
        "val": "images/val",
        "kpt_shape": [NUM_KPT, 3],
        "flip_idx": list(range(NUM_KPT)),
        "names": {0: "person"},
    }
    with open(yaml_path, "w") as f:
        yaml.dump(data_cfg, f, default_flow_style=False, sort_keys=False)

    print(f"\n{'='*50}")
    print(f"Annotation complete.")
    print(f"  Train: {stats['train_ok']} OK, {stats['train_fail']} failed")
    print(f"  Val:   {stats['val_ok']} OK, {stats['val_fail']} failed")
    print(f"  data.yaml: {yaml_path}")
    print(f"  Output:    {out_root}/")


if __name__ == "__main__":
    main()
