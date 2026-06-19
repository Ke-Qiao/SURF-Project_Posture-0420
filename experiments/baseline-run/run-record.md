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

## Week 1 web demo validation

Additional validation was run after adding the lightweight browser demo.

### Files added for the web demo

- `web/app.py`
- `web/static/index.html`
- `web/static/styles.css`
- `web/static/app.js`
- `posture/pipeline.py`
- `docs/week-01-web-demo.md`
- `requirements.txt`

### Behavior added

- `main.py` and `web/app.py` now share the same frame-processing path through
  `posture.pipeline.annotate_frame`.
- The existing MediaPipe full-body skeleton is preserved.
- The side-view five-point overlay is preserved.
- A dashed ankle-based plumb line is added as a neutral standing reference.
- The web page supports mode buttons for webcam, image, and video.
- Uploaded media is stored temporarily outside the Git repository.

### Checks passed

- `teacher_baseline.py`, `main.py`, `posture/*.py`, `scripts/*.py`, and
  `web/*.py` pass `py_compile` when the pyc cache is redirected to
  `/private/tmp`.
- `cv2`, `mediapipe`, `numpy`, `matplotlib`, and `flask` import successfully.
- `mediapipe.__version__` is `0.10.8`.
- `hasattr(mediapipe, "solutions")` is `True`.
- `Flask` version is `3.0.3`.
- `git diff --check` passes.
- The Flask app starts on `http://127.0.0.1:5050`.
- `GET /health` returns HTTP 200.
- `GET /` returns the web demo HTML.
- `GET /static/styles.css` returns HTTP 200.
- Browser DOM validation confirms the webcam, image, and video mode buttons,
  preview area, overlay legend, and metrics panel render.
- Browser mode-switch validation confirms the Image button activates the image
  panel and deactivates the webcam panel.
- Browser layout validation confirms no horizontal overflow at desktop width
  `1280px` or mobile width `390px`.

### Checks blocked in the agent environment

`pip check` was attempted and reported:

```text
mediapipe 0.10.8 is not supported on this platform
```

Direct import validation still passes for `mediapipe==0.10.8` and
`hasattr(mediapipe, "solutions")`. The project keeps this version because newer
MediaPipe builds tested earlier did not expose the teacher-code
`mp.solutions.pose` API path.

The image API was tested with a sample image:

```bash
curl -F file=@data/test_sample/24194505-profile-of-a-young-man-walking.jpg \
  http://127.0.0.1:5050/api/analyze-image
```

It returned HTTP 503 with a readable MediaPipe/OpenGL sandbox error instead of
crashing the server.

The webcam stream endpoint was tested:

```bash
curl --max-time 5 http://127.0.0.1:5050/stream/webcam
```

It returned HTTP 200 with an MJPEG error frame. Full live webcam validation
still requires a normal macOS GUI terminal with Camera permission.

The existing batch command was attempted again:

```bash
.venv/bin/python main.py --batch data/test_sample --output experiments/baseline-run/test-sample-results.csv
```

It remains blocked by the same MediaPipe/OpenGL sandbox initialization failure:

```text
RuntimeError: Service "kGpuService", required by node posedetectioncpu__ImageToTensorCalculator, was not provided and cannot be created: Could not create an NSOpenGLPixelFormat
```

## Web demo launcher validation

A one-click macOS launcher was added:

```text
start_web_demo.command
```

The launcher:

- changes into the project root automatically
- checks `.venv/bin/python`
- checks `cv2`, `flask`, and `mediapipe.solutions`
- starts `python -m web.app`
- opens `http://127.0.0.1:5050` unless `SURF_NO_OPEN=1` is set
- detects an already-running local server through `/health`

Validation commands:

```bash
zsh -n start_web_demo.command
SURF_NO_OPEN=1 ./start_web_demo.command
```

Validation results:

- `zsh -n start_web_demo.command` passed.
- `SURF_NO_OPEN=1 ./start_web_demo.command` passed against the already-running
  local server and skipped browser opening as intended.
- `GET /health` returned HTTP 200 after launcher validation.
- Python `py_compile` and import checks still pass.
- `git diff --check` passes.
- `pip check` still reports the known `mediapipe 0.10.8 is not supported on
  this platform` warning.
- `main.py --batch data/test_sample` is still blocked by the known macOS
  MediaPipe/OpenGL sandbox initialization failure.

## Web demo UI cleanup and MediaPipe error handling

Follow-up changes were made after visual inspection of the local web page:

- Removed the top subtitle `Week 1 side-view posture baseline`.
- Changed Flask to run the local demo in single-thread mode so MediaPipe Pose is
  initialized and used from the server's main request loop instead of worker
  threads.
- Added a stable `app` marker and PID to `/health`.
- Updated `start_web_demo.command` so if port `5050` is occupied by an older
  local server, it automatically tries the next available port.
- Shortened the user-facing MediaPipe/OpenGL error message.
- Kept the low-level MediaPipe exception in the JSON `detail` field for
  debugging.
- Changed the frontend so errors show as `Posture: Error` plus a short advice
  message instead of placing the full exception inside the large `Posture`
  value.

Validation results:

- `zsh -n start_web_demo.command` passed.
- Python `py_compile` passed for `teacher_baseline.py`, `main.py`,
  `posture/*.py`, `scripts/*.py`, and `web/*.py`.
- Import check passed for `cv2`, `mediapipe`, `numpy`, `matplotlib`, and
  `flask`.
- `git diff --check` passed.
- With the older server still occupying port `5050`, the launcher correctly
  selected `http://127.0.0.1:5051`.
- After stopping the older server, the updated launcher started the new server
  on `http://127.0.0.1:5050`.
- `GET /health` returned HTTP 200 with `"app":"surf-posture-web"`.
- HTML validation confirmed the removed subtitle no longer appears.
- Browser DOM validation confirmed no horizontal overflow and a shorter topbar.
- In this Codex sandbox, image analysis still returns the known MediaPipe/OpenGL
  HTTP 503, but the UI-facing error is now short and stable.
