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

## Web demo media preview and text footer update

Follow-up changes were made after reviewing the webpage layout:

- Removed posture verdict, score, angle, side, and advice text from the visual
  area for web image, webcam, and video outputs.
- Kept the skeleton, side-view keypoint line, keypoint dots, and plumb line on
  the visual area.
- Added `append_analysis_footer` so analysis text is appended below the frame.
- Added a `<video>` preview element for selected video files.
- Added image/video `change` handlers so selected files are previewed before
  analysis starts.
- Added a web app health version marker: `preview-footer-v1`.
- Updated the one-click launcher so older local servers with no matching health
  version are treated as occupied, and the next available port is selected.

Validation results:

- Python `py_compile` passed for `teacher_baseline.py`, `main.py`,
  `posture/*.py`, `scripts/*.py`, and `web/*.py`.
- Import check passed for `cv2`, `mediapipe`, `numpy`, `matplotlib`, and
  `flask`.
- `zsh -n start_web_demo.command` passed.
- `git diff --check` passed.
- With an older server already running on `5050`, the launcher correctly
  selected `http://127.0.0.1:5051`.
- `GET /health` on the updated server returned HTTP 200 with
  `"version":"preview-footer-v1"`.
- HTML/JS validation confirmed `previewVideo`, `previewSelectedImage`,
  `previewSelectedVideo`, `showVideo`, and `URL.createObjectURL` are present.
- Browser DOM validation confirmed no horizontal overflow and no subtitle text.
- Direct `append_analysis_footer` validation confirmed a detected result adds a
  142px footer below the frame.
- The currently running older `5050` service can still analyze the sample image,
  but because it was started before this change, its in-memory backend does not
  include the footer logic. Relaunch with `start_web_demo.command` to load the
  new backend.
- The temporary updated `5051` service started from this agent session still
  returns the known Codex MediaPipe/OpenGL HTTP 503 for live analysis.
- `pip check` still reports the known `mediapipe 0.10.8 is not supported on
  this platform` warning.
- `main.py --batch data/test_sample` is still blocked by the known macOS
  MediaPipe/OpenGL sandbox initialization failure in this agent session.

## Week 1 webcam capture ZIP export

Follow-up changes were made to support webcam data collection from the web demo:

- Added a `Capture / Download` button inside Webcam mode.
- Each click waits 3 seconds, then stores the latest server-side webcam frame in
  memory.
- Each capture stores both the original frame and the MediaPipe-processed frame.
- After 10 captures, the button switches to `Download capture ZIP`.
- The ZIP contains `original/`, `mediapipe/`, `capture_log.csv`, and
  `summary.md`.
- Updated the web app health version marker to `week-01-webcam-capture-v1`.
- The capture endpoint rejects stale cached webcam frames, so stopping the
  camera will not accidentally export an old frame after the cache expires.

Validation results:

- `.venv/bin/python -m unittest discover -s tests` passed 19 tests.
- `PYTHONPYCACHEPREFIX=/private/tmp/surf-posture-pycache .venv/bin/python -m py_compile ...`
  passed for `teacher_baseline.py`, `main.py`, `posture/*.py`, `scripts/*.py`,
  `web/*.py`, and `tests/*.py`.
- Import check passed for `cv2`, `mediapipe`, `numpy`, `matplotlib`, and
  `flask`.
- `node --check web/static/app.js` passed.
- `zsh -n start_web_demo.command` passed.
- `git diff --check` passed.
- `.venv/bin/pip check` still reports the known
  `mediapipe 0.10.8 is not supported on this platform` warning.
- Local smoke test started `SURF_NO_OPEN=1 ./start_web_demo.command` at
  `http://127.0.0.1:5050`.
- `GET /health` returned HTTP 200 with
  `"version":"week-01-webcam-capture-v1"`.
- `POST /api/webcam-capture` without an active camera frame returned the
  expected HTTP 409 `No webcam frame is ready. Start camera first.` message.
- Static checks confirmed the updated `Capture / Download` button and webcam
  capture JavaScript were served by the running local app.

## Week 1 batch triage export

Follow-up changes were made to support batch media triage from the web demo:

- Added a `Batch` mode to the local webpage.
- Batch mode accepts uploaded images/videos and can also include the teacher
  image library from `train`, `val`, or all teacher images.
- Added rule-based standing/sitting/incomplete auto-suggestions using MediaPipe
  landmark completeness and lower-body geometry.
- Added a batch ZIP export containing categorized files, annotated images,
  `batch_results.csv`, and `summary.md`.
- Added `GET /api/batch-download/<token>` for downloading completed exports.
- Updated the web app health version marker to `week-01-batch-v1`.
- Kept this as dataset triage, not model training or a trained classifier.

Validation results:

- `python -m unittest discover -s tests` passed 14 tests.
- Python `py_compile` passed for `teacher_baseline.py`, `main.py`,
  `posture/*.py`, `scripts/*.py`, `web/*.py`, and `tests/*.py`.
- Import check passed for `cv2`, `mediapipe`, `numpy`, `matplotlib`, and
  `flask`.
- `node --check web/static/app.js` passed.
- `zsh -n start_web_demo.command` passed.
- `git diff --check` passed.
- The launcher avoided an occupied older service on `5050` and started the
  updated server on `5051`.
- `GET /health` returned HTTP 200 with `"version":"week-01-batch-v1"`.
- Static checks confirmed Batch UI appears in `index.html`, and `app.js` /
  `styles.css` are served by the updated service.
- Empty `POST /api/batch-analyze` returned the expected HTTP 400 JSON error.
- `pip check` still reports the known `mediapipe 0.10.8 is not supported on
  this platform` warning.
- `main.py --batch data/test_sample` is still blocked by the known macOS
  MediaPipe/OpenGL sandbox initialization failure in this agent session.

## Front-view gate for side-view scoring

Follow-up changes were made after the webcam view showed a frontal pose being
classified as bad because `Forward Head` was computed from the side-view
`ear-shoulder-hip` angle.

- The existing `Forward Head` metric still means the angle at the shoulder
  between ear, shoulder, and hip.
- That metric is valid only for side-view posture, where those landmarks should
  roughly align in the image plane.
- In a frontal view, MediaPipe correctly sees both shoulders and both hips far
  apart horizontally, so forcing either left or right side into a 2D
  `ear-shoulder-hip` angle creates a projection artifact.
- Added a conservative view gate in `posture/config.py` and
  `posture/analyzer.py`.
- If both left/right shoulders or hips are visible and wide apart, the pipeline
  returns `Side view required` and does not produce side-view angle scores.
- Updated CLI batch output, web JSON output, OpenCV footer, and browser metrics
  to show the unsupported view clearly.
- Updated the web app health version marker to `side-view-gate-v1`.

Validation results:

- Synthetic landmark validation passed: a frontal pose returns
  `view="front"`, `view_valid=False`, `posture="Side view required"`, and no
  side-view angle scores.
- Synthetic landmark validation passed: a clear side pose still returns
  `view="side"` and the original three angle scores.
- Python `py_compile` passed for `teacher_baseline.py`, `main.py`,
  `posture/*.py`, `scripts/*.py`, and `web/*.py`.
- Import check passed for `cv2`, `mediapipe`, `numpy`, `matplotlib`, and
  `flask`.
- `node --check web/static/app.js` passed.
- `zsh -n start_web_demo.command` passed.
- `git diff --check` passed.
- The launcher now treats occupied or stale ports as unavailable even when
  `/health` times out, then selects the next available port.
- With an older or stuck service on `5050`, the launcher selected
  `http://127.0.0.1:5051`.
- `GET /health` on the updated service returned HTTP 200 with
  `"version":"side-view-gate-v1"`.
- Static checks confirmed `index.html` and `app.js` are served by the updated
  service.
- `pip check` still reports the known `mediapipe 0.10.8 is not supported on
  this platform` warning.
- `main.py --batch data/test_sample` is still blocked by the known macOS
  MediaPipe/OpenGL sandbox initialization failure in this agent session.

## Web demo webcam footer live update

Follow-up changes were made after the webcam view showed skeleton lines but no
live posture text in the footer:

- Added `GET /stream/webcam-json`.
- The new endpoint streams newline-delimited JSON containing a JPEG data URL and
  the current `PostureResult` converted to JSON.
- Updated the webcam Start button to read this stream with `fetch` instead of
  using a plain MJPEG `<img>` source.
- Added a real browser `analysisFooter` below the visual frame.
- The footer now mirrors the right-side metrics: posture verdict, score, side,
  per-angle values, deviations, and advice.
- Added abort handling so Stop or mode switching closes the live stream.
- Updated the web app health version marker to `webcam-result-stream-v1`.

Validation results:

- Python `py_compile` passed for `teacher_baseline.py`, `main.py`,
  `posture/*.py`, `scripts/*.py`, and `web/*.py`.
- Import check passed for `cv2`, `mediapipe`, `numpy`, `matplotlib`, and
  `flask`.
- `zsh -n start_web_demo.command` passed.
- `git diff --check` passed.
- `GET /health` returned HTTP 200 with
  `"version":"webcam-result-stream-v1"`.
- HTML/JS/CSS validation confirmed `analysisFooter`, `footerPosture`,
  `/stream/webcam-json`, `readWebcamStream`, and footer styles are present.
- Browser DOM validation confirmed the footer exists, has initial text, and no
  horizontal overflow.
- In this Codex agent session, `/stream/webcam-json` returns the known
  MediaPipe/OpenGL error as JSON; in a normal macOS Terminal session it is the
  path that will populate the webcam footer live.
- Browser button-click automation timed out in this agent browser, so live UI
  click verification remains manual.
- `pip check` still reports the known `mediapipe 0.10.8 is not supported on
  this platform` warning.
- `main.py --batch data/test_sample` is still blocked by the known macOS
  MediaPipe/OpenGL sandbox initialization failure in this agent session.

## Week 1 demo polish for meeting

Follow-up changes were made before the Week 1 meeting demo:

- Added `GET /stream/video-json/<token>` so uploaded videos can use the same
  frame-plus-result JSON stream pattern as webcam mode.
- Updated video mode to refresh the preview, footer, and right-side metrics from
  the current frame result.
- Added a local `Download evidence` button that exports the current mode, source
  name, timestamp, posture result, angles, advice, and current preview frame as
  JSON.
- Kept the teacher baseline, CLI flags, posture thresholds, side-view gate, and
  original provided dataset unchanged.
- Updated the web app health version marker to `week-01-demo-polish-v1`.

Validation results:

- `python -m unittest discover -s tests` passed 6 tests.
- Python `py_compile` passed for `teacher_baseline.py`, `main.py`,
  `posture/*.py`, `scripts/*.py`, `web/*.py`, and `tests/*.py`.
- Import check passed for `cv2`, `mediapipe`, `numpy`, `matplotlib`, and
  `flask`.
- `node --check web/static/app.js` passed.
- `zsh -n start_web_demo.command` passed.
- `git diff --check` passed.
- `GET /health` on the updated service returned HTTP 200 with
  `"version":"week-01-demo-polish-v1"`.
- Static checks confirmed `index.html`, `app.js`, and `styles.css` are served
  by the updated service.
- `pip check` still reports the known `mediapipe 0.10.8 is not supported on
  this platform` warning.
- `main.py --batch data/test_sample` is still blocked by the known macOS
  MediaPipe/OpenGL sandbox initialization failure in this agent session.
