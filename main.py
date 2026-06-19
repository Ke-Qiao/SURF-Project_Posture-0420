"""SURF Posture Detection — side-view angle analysis with multiple input modes.

Usage
-----
    python main.py                          # webcam  (default)
    python main.py --image photo.jpg        # single image
    python main.py --video clip.mp4         # video file
    python main.py --batch images_dir/      # batch → CSV

Press **ESC** to quit camera / video mode.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

import cv2

from posture.detector import PoseDetector
from posture.pipeline import annotate_frame

# ======================================================================
# CLI
# ======================================================================


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="SURF Posture Detection System")
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--image", type=str, help="Path to a single image file")
    grp.add_argument("--video", type=str, help="Path to a video file")
    grp.add_argument(
        "--batch", type=str,
        help="Directory of images — analyse every image and write CSV",
    )
    p.add_argument(
        "--output", type=str, default="batch_results.csv",
        help="Output CSV path for --batch mode (default: batch_results.csv)",
    )
    return p


# ======================================================================
# Mode: webcam
# ======================================================================


def run_camera(detector: PoseDetector) -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: cannot open camera. Check permissions.")
        sys.exit(1)

    print("Webcam started. Press ESC to exit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        annotate_frame(detector, frame)

        cv2.imshow("SURF Posture Detection", frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# ======================================================================
# Mode: single image
# ======================================================================


def run_image(detector: PoseDetector, path: str) -> None:
    frame = cv2.imread(path)
    if frame is None:
        print(f"Error: cannot read image '{path}'")
        sys.exit(1)

    posture = annotate_frame(detector, frame)
    _print_result(path, posture)

    cv2.imshow("SURF Posture Detection", frame)
    print("Press any key to close the window.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ======================================================================
# Mode: video
# ======================================================================


def run_video(detector: PoseDetector, path: str) -> None:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Error: cannot open video '{path}'")
        sys.exit(1)

    print(f"Playing: {path}  |  Press ESC to exit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        annotate_frame(detector, frame)

        cv2.imshow("SURF Posture Detection", frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# ======================================================================
# Mode: batch → CSV
# ======================================================================

_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Column order for the three angles
_ANGLE_NAMES = ["ear_shoulder_hip", "shoulder_hip_knee", "hip_knee_ankle"]


def run_batch(detector: PoseDetector, directory: str, csv_path: str) -> None:
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory.")
        sys.exit(1)

    files = sorted(
        f for f in os.listdir(directory)
        if os.path.splitext(f)[1].lower() in _IMG_EXTS
    )
    if not files:
        print(f"No image files found in '{directory}'.")
        sys.exit(1)

    print(f"Processing {len(files)} images from '{directory}' …")

    fieldnames = (
        ["filename", "side"]
        + [f"{n}_angle" for n in _ANGLE_NAMES]
        + [f"{n}_deviation" for n in _ANGLE_NAMES]
        + ["score", "posture", "issues"]
    )

    rows: list[dict] = []
    for fname in files:
        fpath = os.path.join(directory, fname)
        frame = cv2.imread(fpath)
        if frame is None:
            print(f"  [SKIP] cannot read: {fname}")
            continue

        posture = annotate_frame(detector, frame)

        row: dict = {"filename": fname}
        if posture.detected and posture.view_valid:
            row["side"] = posture.side
            angle_map = {ar.name: ar for ar in posture.angles}
            for n in _ANGLE_NAMES:
                ar = angle_map[n]
                row[f"{n}_angle"] = ar.angle
                row[f"{n}_deviation"] = ar.deviation
            row["score"] = posture.score
            row["posture"] = "Good" if posture.overall_good else "Bad"
            row["issues"] = "; ".join(posture.issues) if posture.issues else ""
            tag = f"[{posture.score}/100 {'Good' if posture.overall_good else 'Bad'}]"
        elif posture.detected:
            row["side"] = posture.view
            for n in _ANGLE_NAMES:
                row[f"{n}_angle"] = ""
                row[f"{n}_deviation"] = ""
            row["score"] = ""
            row["posture"] = "Side view required"
            row["issues"] = posture.message
            tag = "[Side view required]"
        else:
            row["side"] = ""
            for n in _ANGLE_NAMES:
                row[f"{n}_angle"] = ""
                row[f"{n}_deviation"] = ""
            row["score"] = ""
            row["posture"] = "No detection"
            row["issues"] = ""
            tag = "[No detection]"

        rows.append(row)
        print(f"  {fname}  {tag}")

    # write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults saved to: {csv_path}")
    print(f"Done. {len(rows)}/{len(files)} images processed.")


# ======================================================================
# Helpers
# ======================================================================


def _print_result(filename: str, p) -> None:
    """Pretty-print a single PostureResult to the terminal."""
    if not p.detected:
        print(f"  {filename}: no person detected")
        return

    if not p.view_valid:
        print(f"  {filename}: side view required ({p.message})")
        return

    status = "GOOD" if p.overall_good else "BAD"
    print(f"\n  {filename}  [{status}]  Score: {p.score}/100  (side: {p.side})")
    for ar in p.angles:
        flag = "OK" if ar.is_good else "!!"
        print(f"    [{flag}] {ar.label}: {ar.angle} deg  (deviation: {ar.deviation} deg)")
    if p.advice:
        print("  Advice:")
        for a in p.advice:
            print(f"    > {a}")


# ======================================================================
# Entry point
# ======================================================================


def main() -> None:
    args = _build_parser().parse_args()

    static = args.image is not None or args.batch is not None
    detector = PoseDetector(static_image_mode=static)

    try:
        if args.image:
            run_image(detector, args.image)
        elif args.video:
            run_video(detector, args.video)
        elif args.batch:
            run_batch(detector, args.batch, args.output)
        else:
            run_camera(detector)
    finally:
        detector.close()


if __name__ == "__main__":
    main()
