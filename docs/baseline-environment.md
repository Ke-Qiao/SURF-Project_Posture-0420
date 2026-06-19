# Baseline Environment

This note records the actual environment setup that matched the teacher's
baseline code on this machine.

## Final package choice

- `python`: 3.9.6
- `numpy`: 1.26.4
- `matplotlib`: 3.7.5
- `mediapipe`: 0.10.8
- `opencv-contrib-python`: 4.11.0.86

## Why the package set changed

- The originally planned `opencv-python==4.13.0.92` requires `numpy>=2` on
  Python 3.9, which conflicts with the teacher's `numpy<2` note.
- The newer `mediapipe==0.10.35` package no longer exposed
  `mediapipe.solutions`, but the teacher's code uses `mp.solutions.pose`.
- `mediapipe` installs `opencv-contrib-python`, and OpenCV's own packaging note
  says not to install multiple OpenCV wheel variants in the same environment.
  Because of that, the final environment keeps `opencv-contrib-python` only and
  does not install `opencv-python` separately.

## Reproducible setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install --progress-bar off -i https://pypi.tuna.tsinghua.edu.cn/simple \
  numpy==1.26.4 \
  matplotlib==3.7.5 \
  mediapipe==0.10.8
```

## Validation commands

```bash
.venv/bin/python --version
.venv/bin/python -c "import cv2, mediapipe as mp, numpy, matplotlib; print(cv2.__file__); print(hasattr(cv2, 'VideoCapture')); print(mp.__version__); print(hasattr(mp, 'solutions')); print('imports-ok')"
.venv/bin/pip show numpy matplotlib opencv-contrib-python mediapipe
.venv/bin/python main.py
```

## Current blockers in this execution environment

- `cv2.VideoCapture(0)` reports that camera access has been denied.
- Running `main.py` in the current sandboxed terminal environment fails while
  MediaPipe initializes the pose graph because macOS OpenGL context creation is
  unavailable there.

## Evidence location

- `experiments/baseline-run/run-record.md`
- `experiments/baseline-run/terminal-run-summary.txt`
- `experiments/baseline-run/terminal-run-evidence.png`
