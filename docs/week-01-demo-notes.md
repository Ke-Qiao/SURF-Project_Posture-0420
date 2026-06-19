# Week 1 Demo Notes

## Meeting message

This week's work focuses on running and understanding the teacher's baseline,
then making small, explainable increments around it. It does not train a model.

## What is ready

- `teacher_baseline.py` preserves the teacher's original webcam logic.
- `main.py` is the extended experiment entrypoint.
- The extended version supports webcam, image, video, and batch image analysis.
- The posture analysis uses side-view keypoints: ear, shoulder, hip, knee, and
  ankle.
- The current score is rule-based and angle-based, not machine-learning based.
- `scripts/filter_dataset.py` is ready for sorting teacher images into useful
  `good`, `bad`, and excluded samples.

## Commands for the meeting

```bash
cd /Users/ke-qiao/Desktop/surf/posture-detection
.venv/bin/python teacher_baseline.py
.venv/bin/python main.py
.venv/bin/python main.py --image data/test_sample/24194505-profile-of-a-young-man-walking.jpg
.venv/bin/python main.py --batch data/test_sample --output experiments/baseline-run/test-sample-results.csv
.venv/bin/python -m web.app
.venv/bin/python scripts/filter_dataset.py --input "/Users/ke-qiao/Desktop/surf/Provided elemnets/archive/images/train" --output data/filtered --resume
```

## How to explain the increment

- The teacher baseline checks shoulder imbalance and torso slant from webcam
  frames.
- The extended version keeps the same MediaPipe skeleton foundation but adds
  side-view posture reasoning.
- Instead of training immediately, the system measures three interpretable
  alignments: head, trunk, and knee.
- Batch mode gives a fast way to inspect multiple teacher images and export CSV
  evidence.
- The webpage adds a local browser demo for webcam, image, and video inputs,
  while keeping the same skeleton, side-view keypoints, and rule-based logic.
- Dataset filtering comes before model training because many source images are
  sitting, front-facing, partial-body, or unsuitable for standing side-view
  posture detection.

## Current technical limits

- Camera mode requires macOS Camera permission for the terminal or IDE that runs
  Python.
- In the current Codex sandbox, MediaPipe Pose cannot create the required macOS
  OpenGL context, so live webcam validation must be done from a normal GUI
  terminal.
- The rule thresholds are initial engineering values and should be tuned after
  more side-view examples are reviewed.

## Webpage increment

The lightweight local webpage is implemented in `web/`. It calls the existing
analysis path instead of redesigning posture detection logic.
