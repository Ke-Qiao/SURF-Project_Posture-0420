"""Flask web demo for the SURF posture detection pipeline."""

from __future__ import annotations

import base64
import os
import tempfile
import time
import uuid
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, Response, jsonify, request, send_from_directory

from posture.detector import PoseDetector
from posture.pipeline import annotate_frame, result_to_dict

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_ROOT = Path(tempfile.gettempdir()) / "surf-posture-web"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}

app = Flask(__name__, static_folder=str(BASE_DIR / "static"), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

_VIDEO_UPLOADS: dict[str, Path] = {}


@app.get("/")
def index():
    """Serve the local demo page."""
    return send_from_directory(app.static_folder, "index.html")


@app.get("/health")
def health():
    """Lightweight server health check that does not initialize MediaPipe."""
    return jsonify(
        {
            "status": "ok",
            "opencv": cv2.__version__,
            "upload_root": str(UPLOAD_ROOT),
        }
    )


@app.post("/api/analyze-image")
def analyze_image():
    """Analyze one uploaded image and return an annotated JPEG data URL."""
    uploaded = request.files.get("file")
    if uploaded is None or uploaded.filename == "":
        return _json_error("No image file uploaded.", 400)

    ext = _suffix(uploaded.filename)
    if ext not in IMAGE_EXTS:
        return _json_error(f"Unsupported image type: {ext or '(none)'}", 400)

    path = _save_upload(uploaded, ext)
    frame = cv2.imread(str(path))
    if frame is None:
        return _json_error("OpenCV could not read this image.", 400)

    detector = None
    try:
        detector = PoseDetector(static_image_mode=True)
        result = annotate_frame(detector, frame)
        jpeg = _encode_jpeg(frame)
        encoded = base64.b64encode(jpeg).decode("ascii")
        return jsonify(
            {
                "image": f"data:image/jpeg;base64,{encoded}",
                "result": result_to_dict(result),
            }
        )
    except Exception as exc:  # MediaPipe/OpenGL failures should not crash demo.
        return _json_error(_runtime_error_message(exc), 503)
    finally:
        if detector is not None:
            detector.close()


@app.post("/api/load-video")
def load_video():
    """Store an uploaded video in tmp and return a stream URL token."""
    uploaded = request.files.get("file")
    if uploaded is None or uploaded.filename == "":
        return _json_error("No video file uploaded.", 400)

    ext = _suffix(uploaded.filename)
    if ext not in VIDEO_EXTS:
        return _json_error(f"Unsupported video type: {ext or '(none)'}", 400)

    token = uuid.uuid4().hex
    path = _save_upload(uploaded, ext, token=token)
    _VIDEO_UPLOADS[token] = path
    return jsonify({"token": token, "stream_url": f"/stream/video/{token}"})


@app.get("/stream/webcam")
def stream_webcam():
    """Stream annotated webcam frames as MJPEG."""
    return Response(
        _frame_stream(0, label="Webcam unavailable"),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/stream/video/<token>")
def stream_video(token: str):
    """Stream an uploaded video with the same overlay used by main.py."""
    path = _VIDEO_UPLOADS.get(token)
    if path is None or not path.exists():
        return Response(
            _single_error_stream("Video file not found."),
            mimetype="multipart/x-mixed-replace; boundary=frame",
            status=404,
        )

    return Response(
        _frame_stream(str(path), label="Video unavailable"),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def _suffix(filename: str) -> str:
    return Path(filename).suffix.lower()


def _save_upload(uploaded, ext: str, token: str | None = None) -> Path:
    file_id = token or uuid.uuid4().hex
    path = UPLOAD_ROOT / f"{file_id}{ext}"
    uploaded.save(path)
    return path


def _frame_stream(source, label: str):
    detector = None
    cap = None
    try:
        detector = PoseDetector(static_image_mode=False)
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            yield _multipart_frame(_error_frame(label))
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = 1.0 / min(max(fps or 15.0, 1.0), 30.0)

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            annotate_frame(detector, frame)
            yield _multipart_frame(frame)
            time.sleep(delay)
    except Exception as exc:
        yield _multipart_frame(_error_frame(_runtime_error_message(exc)))
    finally:
        if cap is not None:
            cap.release()
        if detector is not None:
            detector.close()


def _single_error_stream(message: str):
    yield _multipart_frame(_error_frame(message))


def _encode_jpeg(frame) -> bytes:
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if not ok:
        raise RuntimeError("Could not encode annotated frame as JPEG.")
    return buffer.tobytes()


def _multipart_frame(frame) -> bytes:
    jpeg = _encode_jpeg(frame)
    return b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"


def _error_frame(message: str):
    frame = np.full((540, 960, 3), 28, dtype=np.uint8)
    lines = _wrap_text(message, max_chars=74)
    cv2.putText(
        frame,
        "SURF Posture Demo",
        (34, 58),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )
    y = 118
    for line in lines:
        cv2.putText(
            frame,
            line,
            (34, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 210, 255),
            1,
        )
        y += 32
    return frame


def _wrap_text(text: str, max_chars: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        next_line = " ".join(cur + [word])
        if len(next_line) > max_chars and cur:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))
    return lines[:10]


def _json_error(message: str, status: int):
    return jsonify({"error": message}), status


def _runtime_error_message(exc: Exception) -> str:
    return (
        "Posture detector could not run in this environment. "
        "Use a normal macOS GUI terminal with Camera permission if this is "
        f"a MediaPipe/OpenGL sandbox issue. Detail: {exc}"
    )


def main() -> None:
    port = int(os.environ.get("SURF_WEB_PORT", "5050"))
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
