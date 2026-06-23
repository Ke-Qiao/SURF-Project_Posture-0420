# SURF Posture Detection

Local Week 2 data-collection and posture-demo workspace for the SURF posture
project. The current scope is side-view standing posture only.

## What This App Does

- Runs the teacher baseline separately in `teacher_baseline.py`.
- Runs the extended detector through `main.py`.
- Provides a local web app for image, video, webcam, and batch review.
- Uses webcam mode to collect labeled side-view posture photos.
- Exports local ZIP files for teacher review before data enters GitHub.

The app does not train a model in the Week 2 platform step.

## Setup

```bash
cd /Users/ke-qiao/Desktop/surf/posture-detection
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## Start The Web App

Local computer only:

```bash
./start_web_demo.command
```

Phone collection on the same Wi-Fi:

```bash
SURF_WEB_HOST=0.0.0.0 ./start_web_demo.command
```

The script prints a local URL and, in LAN mode, a phone URL such as:

```text
http://<computer-lan-ip>:5050
```

## Data Collection Flow

1. Start the webcam mode.
2. Fill in `Collector`, `Subject ID`, and `True label`.
3. Ask the subject to stand sideways with the full body visible.
4. Click `Set reference from current pose` on a good side-view frame.
5. Use `Edit reference` to drag the green ear, shoulder, hip, knee, and ankle
   points if needed.
6. Click `Capture / Download`; each click waits 3 seconds and captures one
   frame.
7. After 10 captures, download the ZIP.
8. Send the ZIP or extracted images to the teacher for review before uploading
   approved data to GitHub.

The export contains:

```text
original/
mediapipe/
manifest.csv
reference.json
summary.md
```

## GitHub Policy

- Use a private repository for shared project code and approved data.
- Do not commit raw personal photos, temporary exports, model weights, or local
  cache folders.
- Upload only teacher-approved clean side-view standing images.
- Keep raw provided assets in their original parent directory.

## Validation

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/surf-posture-pycache .venv/bin/python -m py_compile teacher_baseline.py main.py posture/*.py scripts/*.py web/*.py tests/*.py
node --check web/static/app.js
zsh -n start_web_demo.command
git diff --check
```
