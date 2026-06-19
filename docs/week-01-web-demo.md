# Week 1 Web Demo

## Purpose

This is a lightweight local webpage for presenting the current Week 1 posture
baseline. It does not train a model and does not replace `main.py`; it calls the
same frame-processing path used by the CLI.

## Run command

For the easiest local demo, double-click:

```text
/Users/ke-qiao/Desktop/surf/posture-detection/start_web_demo.command
```

The launcher starts the Flask server and opens the browser at
`http://127.0.0.1:5050`. Keep the terminal window open while presenting.

Manual command:

```bash
cd /Users/ke-qiao/Desktop/surf/posture-detection
.venv/bin/python -m web.app
```

Then open:

```text
http://127.0.0.1:5050
```

To use another port:

```bash
SURF_WEB_PORT=5051 .venv/bin/python -m web.app
SURF_WEB_PORT=5051 ./start_web_demo.command
```

## Demo modes

- Webcam: streams `cv2.VideoCapture(0)` through the browser as MJPEG.
- Image: uploads one image, analyzes it, and returns an annotated JPEG plus
  structured angle metrics.
- Video: uploads one local video, stores it temporarily outside the repo, and
  streams annotated frames as MJPEG.

## Overlay contract

The webpage keeps the same core overlay as `main.py`:

- MediaPipe full-body skeleton.
- Side-view keypoints: ear, shoulder, hip, knee, and ankle.
- Side-view alignment line connecting the five keypoints.
- A dashed ankle-based plumb line used as a neutral standing reference.
- Overall posture label, score, selected side, angle values, deviations, and
  advice.

## Current limits

- Camera mode still depends on macOS Camera permission for the terminal that
  starts the server.
- In the current Codex sandbox, MediaPipe Pose may fail during graph
  initialization because the sandbox cannot create the required macOS OpenGL
  context. The web server handles this as a visible error instead of crashing.
- Video metrics are drawn on the stream frames. The right-side structured panel
  is currently populated for image mode only.
