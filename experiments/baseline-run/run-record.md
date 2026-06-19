# Week 1 Baseline Run Record

## Scope

This record captures the first attempt to run the teacher-provided posture
detection baseline in the local project environment.

## What was prepared

- Created `experiments/photos/good`
- Created `experiments/photos/bad`
- Created `experiments/baseline-run`
- Added a runnable root-level `main.py`
- Created a project-local `.venv`
- Installed a package set compatible with the teacher's code path:
  - `numpy==1.26.4`
  - `matplotlib==3.7.5`
  - `mediapipe==0.10.8`
  - `opencv-contrib-python==4.11.0.86`

## Validation results

### 1. Structure and ignore rules

- `experiments/photos/good` exists
- `experiments/photos/bad` exists
- `.venv/` is ignored by Git
- `experiments/photos/` is ignored by Git

### 2. Python and import validation

- Python version: `3.9.6`
- `cv2` import: success
- `mediapipe` import: success
- `numpy` import: success
- `matplotlib` import: success
- `mediapipe.__version__`: `0.10.8`
- `hasattr(mediapipe, "solutions")`: `True`
- `hasattr(cv2, "VideoCapture")`: `True`

### 3. Camera access validation

Direct camera probing returned:

```text
camera-open False
frame-read False None
```

OpenCV also reported that camera access has been denied in the current
execution environment.

### 4. Baseline script execution

`main.py` starts, imports successfully, and reaches MediaPipe pose graph
initialization. In the current sandboxed terminal environment it fails before
opening the live loop with this runtime blocker:

```text
RuntimeError: Service "kGpuService", required by node posedetectioncpu__ImageToTensorCalculator, was not provided and cannot be created: Could not create an NSOpenGLPixelFormat
```

## Interpretation

- The teacher's code path is now matched at the package/API level.
- The current blockers are no longer Python dependency issues.
- The remaining blockers are environment-specific:
  - camera permission is denied for the current execution context
  - MediaPipe pose graph cannot obtain the required macOS graphics context in
    this sandboxed terminal run

## Next local run for the user

Run the baseline from a normal macOS terminal session with GUI access and with
Camera permission granted:

```bash
cd /Users/ke-qiao/Desktop/surf/posture-detection
.venv/bin/python main.py
```

## Status for this week

- Baseline project initialization: done
- Teacher code materialized into `main.py`: done
- Compatible local environment: done
- Import-level validation: done
- Full live webcam baseline in this agent session: blocked by local
  Camera/OpenGL runtime constraints

## Week 1 stabilization validation

Additional validation was run after preserving the teacher baseline and
organizing the extended demo entrypoint.

### Files added for the demo version

- `teacher_baseline.py`
- `docs/week-01-demo-notes.md`
- `data/test_sample/` with four small teacher-dataset sample images

### Checks passed

- `cv2`, `mediapipe`, `numpy`, and `matplotlib` import successfully.
- `mediapipe.__version__` is `0.10.8`.
- `hasattr(mediapipe, "solutions")` is `True`.
- `hasattr(cv2, "VideoCapture")` is `True`.
- `teacher_baseline.py`, `main.py`, `posture/*.py`, and `scripts/*.py`
  pass `py_compile` when the pyc cache is redirected to `/private/tmp`.
- `.venv/`, `experiments/photos/`, and generated baseline CSV files are
  ignored by Git.

### Checks blocked in the agent environment

The batch command was attempted:

```bash
.venv/bin/python main.py --batch data/test_sample --output experiments/baseline-run/test-sample-results.csv
```

It failed during MediaPipe Pose initialization with the same sandbox graphics
context blocker:

```text
RuntimeError: Service "kGpuService", required by node posedetectioncpu__ImageToTensorCalculator, was not provided and cannot be created: Could not create an NSOpenGLPixelFormat
```

Direct camera probing still reports Camera permission denial in this execution
context:

```text
camera-open False
frame-read False None
```

### Interpretation

The code and dependencies are ready for a normal macOS GUI terminal run. The
remaining failures are caused by this agent session's Camera permission and
MediaPipe/OpenGL runtime constraints, not by missing project code.
