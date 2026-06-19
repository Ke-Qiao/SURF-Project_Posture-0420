"""Interactive dataset filter for standing side-view posture images.

Opens each image with the posture analysis overlay and waits for a keypress:

    g  →  keep as GOOD posture example
    b  →  keep as BAD  posture example
    x  →  exclude (not suitable for this project)
    q  →  quit and save progress

Filtered images are **copied** (not moved) into the output directory under
``good/`` and ``bad/`` subdirectories.  A ``filter_log.csv`` is written so
the session can be resumed.

Usage
-----
    python scripts/filter_dataset.py \\
        --input  "../Provided elemnets/archive/images/train" \\
        --output data/filtered
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys

# Allow importing the posture package from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2

from posture.analyzer import analyze_posture
from posture.detector import PoseDetector
from posture.visualizer import draw_analysis


# ── CLI ─────────────────────────────────────────────────────────────────


def _parse_args():
    p = argparse.ArgumentParser(description="Filter dataset interactively")
    p.add_argument(
        "--input", required=True,
        help="Directory containing source images",
    )
    p.add_argument(
        "--output", default="data/filtered",
        help="Output directory (default: data/filtered)",
    )
    p.add_argument(
        "--resume", action="store_true",
        help="Skip images already logged in filter_log.csv",
    )
    return p.parse_args()


# ── Helpers ─────────────────────────────────────────────────────────────

_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

_INSTRUCTIONS = (
    "[G] Good  [B] Bad  [X] Exclude  [Q] Quit"
)


def _load_existing_log(log_path: str) -> dict[str, str]:
    """Return {filename: decision} from a previous log, if it exists."""
    done: dict[str, str] = {}
    if os.path.isfile(log_path):
        with open(log_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done[row["filename"]] = row["decision"]
    return done


# ── Main ────────────────────────────────────────────────────────────────


def main() -> None:
    args = _parse_args()

    src_dir = args.input
    out_dir = args.output
    good_dir = os.path.join(out_dir, "good")
    bad_dir = os.path.join(out_dir, "bad")
    log_path = os.path.join(out_dir, "filter_log.csv")

    os.makedirs(good_dir, exist_ok=True)
    os.makedirs(bad_dir, exist_ok=True)

    # Collect image files
    files = sorted(
        f for f in os.listdir(src_dir)
        if os.path.splitext(f)[1].lower() in _IMG_EXTS
    )
    if not files:
        print(f"No images found in '{src_dir}'.")
        return

    # Resume support
    done = _load_existing_log(log_path) if args.resume else {}
    remaining = [f for f in files if f not in done]

    print(f"Total images: {len(files)}")
    print(f"Already done: {len(done)}")
    print(f"Remaining:    {len(remaining)}")
    print(f"Output:       {out_dir}")
    print()
    print(_INSTRUCTIONS)
    print()

    detector = PoseDetector(static_image_mode=True)

    # Open log for appending
    write_header = not os.path.isfile(log_path) or not args.resume
    log_file = open(log_path, "a" if args.resume else "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(log_file, fieldnames=["filename", "decision", "score", "issues"])
    if write_header:
        writer.writeheader()

    counts = {"good": 0, "bad": 0, "exclude": 0}

    try:
        for idx, fname in enumerate(remaining, 1):
            fpath = os.path.join(src_dir, fname)
            frame = cv2.imread(fpath)
            if frame is None:
                print(f"  [SKIP] cannot read: {fname}")
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)
            detector.draw_skeleton(frame, results)
            posture = analyze_posture(detector.get_landmarks(results))
            draw_analysis(frame, posture)

            # Add instruction bar at top
            bar = frame.copy()
            cv2.rectangle(bar, (0, 0), (frame.shape[1], 22), (40, 40, 40), -1)
            info = f"[{idx}/{len(remaining)}] {fname}  |  {_INSTRUCTIONS}"
            cv2.putText(bar, info, (8, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            cv2.imshow("Filter Dataset", bar)

            # Wait for valid key
            while True:
                key = cv2.waitKey(0) & 0xFF
                if key in (ord("g"), ord("G")):
                    decision = "good"
                    break
                elif key in (ord("b"), ord("B")):
                    decision = "bad"
                    break
                elif key in (ord("x"), ord("X")):
                    decision = "exclude"
                    break
                elif key in (ord("q"), ord("Q"), 27):
                    decision = None
                    break

            if decision is None:
                print("Quit by user.")
                break

            # Copy image to appropriate subdirectory
            if decision in ("good", "bad"):
                dest = good_dir if decision == "good" else bad_dir
                shutil.copy2(fpath, os.path.join(dest, fname))

            # Log
            writer.writerow({
                "filename": fname,
                "decision": decision,
                "score": posture.score if posture.detected else "",
                "issues": "; ".join(posture.issues) if posture.detected else "",
            })
            log_file.flush()

            counts[decision] += 1
            print(f"  {fname} → {decision.upper()}")

    finally:
        log_file.close()
        detector.close()
        cv2.destroyAllWindows()

    print()
    print(f"Session complete.  Good: {counts['good']}  Bad: {counts['bad']}  Excluded: {counts['exclude']}")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
