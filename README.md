# SURF Posture Detection

Local Week 2 data-collection and posture-demo workspace for the SURF posture
project. The current scope is side-view standing posture only.

## What This App Does

- Runs the teacher baseline separately in `teacher_baseline.py`.
- Runs the extended detector through `main.py`.
- Provides a local web app for image, video, webcam, and batch review.
- Uses webcam mode to collect labeled side-view posture photos.
- Checks whether the teacher-required side-profile body parts are visible
  before saving webcam captures.
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
./start_phone_demo.command
```

Phone live camera collection with HTTPS:

```bash
./start_phone_https_demo.command
```

Equivalent command-line form:

```bash
SURF_WEB_HOST=0.0.0.0 ./start_web_demo.command
```

The script prints a local URL and, in LAN mode, a phone URL such as:

```text
http://<computer-lan-ip>:5050
```

If your Mac IP is `192.168.2.3`, open the printed phone URL on the phone, for
example `http://192.168.2.3:<printed-port>`. Use the printed port, not a port
from an older terminal window.

If the printed phone IP is not your Wi-Fi IP, override it explicitly:

```bash
SURF_PHONE_IP=192.168.2.3 ./start_phone_demo.command
```

On phones, open the printed phone URL and use `Start phone camera` in the
`Webcam` panel. Browser live camera access normally requires HTTPS or another
secure browser context. Use `start_phone_https_demo.command` when the browser
blocks camera access on the HTTP LAN page.

The HTTPS script creates local certificates under `temp/certs/`. These files are
ignored by Git. For iPhone Safari, install and trust the printed local CA
certificate before opening the HTTPS phone URL:

1. Start `./start_phone_https_demo.command`.
2. Find the printed `Local CA certificate for phone trust` path.
3. AirDrop that `.crt` file to the iPhone, or open it from Finder and share it
   to the iPhone.
4. On iPhone, install the downloaded profile in Settings.
5. Enable full trust in Settings > General > About > Certificate Trust Settings.
6. Open the printed `https://<mac-wifi-ip>:<port>` phone URL.

If the printed HTTPS phone IP is wrong, use:

```bash
SURF_PHONE_IP=192.168.2.3 ./start_phone_https_demo.command
```

## Data Collection Flow

1. Start the webcam mode.
2. Fill in `Collector`, `Subject ID`, and `True label`.
3. Ask the subject to stand sideways with the full body visible.
4. Click `Start computer camera` on the laptop or `Start phone camera` on the
   phone.
5. Wait until the fixed green good-posture skeleton appears over the detected
   side-view body.
6. Confirm the profile checklist shows the required body parts as visible.
7. Click `Capture / Download`; each click waits 3 seconds and captures one
   frame.
8. After 10 captures, download the ZIP.
9. Send the ZIP or extracted images to the teacher for review before uploading
   approved data to GitHub.

The green reference skeleton defaults to `fixed-good-posture-v1`. It is
auto-aligned to the detected side-view body and uses 180-degree good-posture
angles. `Use current pose as custom reference` is available only as an optional
debug/demo override.

The profile checklist follows the teacher's latest requirement:

```text
Head, Neck, Shoulder, Hip, Buttock, Knees, Ankle
```

MediaPipe does not provide explicit neck or buttock landmarks. The app checks
`Neck` through the visible ear-shoulder segment and `Buttock` through the hip
landmark proxy.

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
