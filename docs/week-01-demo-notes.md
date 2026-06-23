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

## Suggested meeting flow

1. Start with `teacher_baseline.py` to show the original webcam reference logic
   is preserved.
2. Open the local webpage with `start_web_demo.command`.
3. Show image mode first because it is the most stable path for explaining
   side-view keypoints, angles, score, and advice.
4. Show webcam mode next if Camera permission is available in the normal macOS
   Terminal session.
5. Show video mode last to demonstrate that the same frame-processing pipeline
   can run on recorded input.
6. Use `Download evidence` after a clear result to save the current mode,
   frame, score, angles, and advice as a JSON record.
7. Use Batch mode for a quick rule-based triage of uploaded media or the
   teacher image library into `standing`, `sitting`, and `incomplete`.
8. In Webcam mode, use `Capture / Download` to collect 10 delayed snapshots and
   download a ZIP containing original frames plus MediaPipe-processed frames.

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
- Front-facing input is intentionally blocked from side-view scoring and shown
  as `Side view required`, because the Forward Head angle is a side-view
  measurement.
- This week does not include model training. The next reasonable step is
  filtering usable side-view images and tuning thresholds with more examples.
- Dataset filtering comes before model training because many source images are
  sitting, front-facing, partial-body, or unsuitable for standing side-view
  posture detection.
- Batch classification is an auto-suggestion only. It is useful for quickly
  packaging obvious standing/sitting/incomplete samples, but edge cases should
  still be reviewed manually.

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

Current webpage polish:

- Webcam and video modes both use JSON frame streams, so the preview, footer,
  and right-side metrics update from the same `PostureResult`.
- Image mode still previews the selected file immediately before analysis.
- The evidence export is local-only and does not write personal media to Git.
- Batch mode can include uploaded images/videos and the teacher `train`, `val`,
  or full image library. It exports a ZIP with categorized files, annotated
  images, `batch_results.csv`, and `summary.md`.
- Webcam capture waits 3 seconds per click, stores up to 10 local snapshots,
  then switches the button to download a ZIP with `original/`, `mediapipe/`,
  `capture_log.csv`, and `summary.md`.
