"""Flask web demo for the SURF posture detection pipeline."""

from __future__ import annotations

import base64
import binascii
import csv
import json
import os
import re
import shutil
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
from threading import Lock

import cv2
import numpy as np
from flask import Flask, Response, jsonify, request, send_file, send_from_directory

from posture.batch_classifier import (
    CSV_FIELDS,
    CATEGORIES,
    process_image_file,
    process_video_file,
    render_summary_markdown,
    summarize_rows,
)
from posture.detector import PoseDetector
from posture.pipeline import annotate_frame, result_to_dict
from posture.visualizer import append_analysis_footer

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
WORKSPACE_DIR = PROJECT_DIR.parent
UPLOAD_ROOT = Path(tempfile.gettempdir()) / "surf-posture-web"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
TEACHER_IMAGE_ROOT = WORKSPACE_DIR / "Provided elemnets" / "archive" / "images"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
APP_VERSION = "week-02-reference-angle-v3"
WEBCAM_CAPTURE_TARGET = 10
WEBCAM_LATEST_MAX_AGE_SECONDS = 8
REFERENCE_POINT_NAMES = ("ear", "shoulder", "hip", "knee", "ankle")
ANGLE_FIELD_NAMES = ("ear_shoulder_hip", "shoulder_hip_knee", "hip_knee_ankle")
SEGMENT_FIELD_NAMES = ("ear_shoulder", "shoulder_hip", "hip_knee", "knee_ankle")
REVIEW_LABELS = ("good", "bad")
REVIEW_POSITIVE_LABEL = "bad"
REVIEW_FIELDS = [
    "filename",
    "true_label",
    "predicted_label",
    "correct",
    "evaluation_status",
    "original_file",
    "annotated_file",
] + [field for field in CSV_FIELDS if field != "filename"]

app = Flask(__name__, static_folder=str(BASE_DIR / "static"), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

_VIDEO_UPLOADS: dict[str, Path] = {}
_BATCH_EXPORTS: dict[str, Path] = {}
_REVIEW_EXPORTS: dict[str, Path] = {}
_WEBCAM_CAPTURE_LOCK = Lock()
_WEBCAM_LATEST: dict = {}
_WEBCAM_CAPTURES: list[dict] = []
_WEBCAM_CAPTURE_ZIPS: dict[str, Path] = {}
_WEBCAM_CAPTURE_TOKEN = ""


@app.get("/")
def index():
    """Serve the local demo page."""
    return send_from_directory(app.static_folder, "index.html")


@app.get("/health")
def health():
    """Lightweight server health check that does not initialize MediaPipe."""
    return jsonify(
        {
            "app": "surf-posture-web",
            "status": "ok",
            "version": APP_VERSION,
            "host": os.environ.get("SURF_WEB_HOST", "127.0.0.1"),
            "https": bool(os.environ.get("SURF_WEB_CERT_FILE") and os.environ.get("SURF_WEB_KEY_FILE")),
            "opencv": cv2.__version__,
            "pid": os.getpid(),
            "upload_root": str(UPLOAD_ROOT),
        }
    )


@app.post("/api/webcam-capture")
def webcam_capture():
    """Capture the latest streamed webcam frame into a 10-photo local set."""
    global _WEBCAM_CAPTURE_TOKEN

    metadata, error = _capture_metadata()
    if error:
        return _json_error(error, 400)

    with _WEBCAM_CAPTURE_LOCK:
        if not _WEBCAM_LATEST:
            return _json_error("No camera frame is ready. Start computer camera or phone camera first.", 409)

        latest_age = time.time() - float(_WEBCAM_LATEST.get("stored_at", 0))
        if latest_age > WEBCAM_LATEST_MAX_AGE_SECONDS:
            return _json_error("Webcam frame is stale. Restart camera before capture.", 409)

        latest_result = _WEBCAM_LATEST["result"]
        if not latest_result.get("profile_complete", False):
            missing = ", ".join(latest_result.get("missing_profile_parts") or ["required body profile"])
            return _json_error(f"Incomplete side profile. Missing: {missing}.", 409)

        if len(_WEBCAM_CAPTURES) >= WEBCAM_CAPTURE_TARGET:
            return jsonify(_webcam_capture_payload(ready=True))

        capture_index = len(_WEBCAM_CAPTURES) + 1
        _WEBCAM_CAPTURES.append(
            {
                "index": capture_index,
                "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "original_jpeg": _WEBCAM_LATEST["original_jpeg"],
                "annotated_jpeg": _annotated_with_reference(
                    _WEBCAM_LATEST["annotated_jpeg"],
                    metadata["reference"],
                ),
                "result": dict(_WEBCAM_LATEST["result"]),
                "metadata": metadata,
            }
        )

        ready = len(_WEBCAM_CAPTURES) >= WEBCAM_CAPTURE_TARGET
        if ready and not _WEBCAM_CAPTURE_TOKEN:
            _WEBCAM_CAPTURE_TOKEN = uuid.uuid4().hex
            zip_path = _create_webcam_capture_zip(_WEBCAM_CAPTURE_TOKEN, list(_WEBCAM_CAPTURES))
            _WEBCAM_CAPTURE_ZIPS[_WEBCAM_CAPTURE_TOKEN] = zip_path

        return jsonify(_webcam_capture_payload(ready=ready))


@app.post("/api/browser-camera-frame")
def browser_camera_frame():
    """Analyze one browser camera frame and cache it for capture export."""
    frame, error = _frame_from_data_url((request.get_json(silent=True) or {}).get("image"))
    if error:
        return _json_error(error, 400)

    detector = None
    try:
        detector = PoseDetector(static_image_mode=True)
        original_frame = frame.copy()
        result = annotate_frame(detector, frame, show_text=False)
        result_payload = result_to_dict(result)
        jpeg = _store_webcam_latest(original_frame, frame, result_payload)
        encoded = base64.b64encode(jpeg).decode("ascii")
        return jsonify(
            {
                "image": f"data:image/jpeg;base64,{encoded}",
                "result": result_payload,
            }
        )
    except Exception as exc:
        return _json_error(_runtime_error_message(), 503, detail=str(exc))
    finally:
        if detector is not None:
            detector.close()


@app.post("/api/webcam-captures-reset")
def webcam_captures_reset():
    """Clear the local webcam capture set after a download is started."""
    global _WEBCAM_CAPTURE_TOKEN

    with _WEBCAM_CAPTURE_LOCK:
        _WEBCAM_CAPTURES.clear()
        _WEBCAM_CAPTURE_TOKEN = ""
    return jsonify({"status": "ok", "count": 0, "target": WEBCAM_CAPTURE_TARGET})


@app.get("/api/webcam-captures-download/<token>")
def webcam_captures_download(token: str):
    """Download one completed webcam capture ZIP."""
    path = _WEBCAM_CAPTURE_ZIPS.get(token)
    if path is None or not path.exists():
        return _json_error("Webcam capture export not found.", 404)
    return send_file(path, as_attachment=True, download_name=path.name)


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
        result = annotate_frame(detector, frame, show_text=False)
        jpeg = _encode_jpeg(frame)
        encoded = base64.b64encode(jpeg).decode("ascii")
        return jsonify(
            {
                "image": f"data:image/jpeg;base64,{encoded}",
                "result": result_to_dict(result),
            }
        )
    except Exception as exc:  # MediaPipe/OpenGL failures should not crash demo.
        return _json_error(_runtime_error_message(), 503, detail=str(exc))
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
    return jsonify(
        {
            "token": token,
            "stream_url": f"/stream/video/{token}",
            "json_stream_url": f"/stream/video-json/{token}",
        }
    )


@app.post("/api/batch-analyze")
def batch_analyze():
    """Batch classify images/videos and return a downloadable ZIP export."""
    token = uuid.uuid4().hex
    sources: list[dict[str, str | Path]] = []

    teacher_source = request.form.get("teacher_source", "").strip()
    if teacher_source:
        try:
            sources.extend(_teacher_sources(teacher_source))
        except ValueError as exc:
            return _json_error(str(exc), 400)

    uploaded_files = [file for file in request.files.getlist("files") if file.filename]
    upload_dir = UPLOAD_ROOT / f"batch-upload-{token}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    for uploaded in uploaded_files:
        ext = _suffix(uploaded.filename)
        if ext not in IMAGE_EXTS and ext not in VIDEO_EXTS:
            return _json_error(f"Unsupported batch file type: {ext or '(none)'}", 400)
        path = upload_dir / f"{uuid.uuid4().hex}{ext}"
        uploaded.save(path)
        sources.append(
            {
                "path": path,
                "name": Path(uploaded.filename).name,
                "media_type": _media_type(ext),
            }
        )

    if not sources:
        return _json_error("Choose uploaded files or a teacher image library source.", 400)

    try:
        payload = _create_batch_export(token, sources)
    except Exception as exc:
        return _json_error(_runtime_error_message(), 503, detail=str(exc))

    return jsonify(payload)


@app.get("/api/batch-download/<token>")
def batch_download(token: str):
    """Download one completed batch export ZIP."""
    path = _BATCH_EXPORTS.get(token)
    if path is None or not path.exists():
        return _json_error("Batch export not found.", 404)
    return send_file(path, as_attachment=True, download_name=path.name)


@app.post("/api/review-dataset")
def review_dataset():
    """Review labeled good/bad images and compute baseline classification metrics."""
    token = uuid.uuid4().hex
    upload_dir = UPLOAD_ROOT / f"review-upload-{token}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    sources: list[dict[str, str | Path]] = []

    for label, field_name in (("good", "good_files"), ("bad", "bad_files")):
        label_dir = upload_dir / label
        label_dir.mkdir(parents=True, exist_ok=True)
        for uploaded in request.files.getlist(field_name):
            if not uploaded.filename:
                continue
            ext = _suffix(uploaded.filename)
            if ext not in IMAGE_EXTS:
                return _json_error(f"Unsupported review image type: {ext or '(none)'}", 400)
            path = label_dir / f"{uuid.uuid4().hex}{ext}"
            uploaded.save(path)
            sources.append(
                {
                    "path": path,
                    "name": Path(uploaded.filename).name,
                    "true_label": label,
                }
            )

    if not sources:
        return _json_error("Choose good or bad review images.", 400)

    try:
        payload = _create_review_export(token, sources)
    except Exception as exc:
        return _json_error(_runtime_error_message(), 503, detail=str(exc))

    return jsonify(payload)


@app.get("/api/review-download/<token>")
def review_download(token: str):
    """Download one completed dataset review ZIP."""
    path = _REVIEW_EXPORTS.get(token)
    if path is None or not path.exists():
        return _json_error("Dataset review export not found.", 404)
    return send_file(path, as_attachment=True, download_name=path.name)


@app.get("/stream/webcam")
def stream_webcam():
    """Stream annotated webcam frames as MJPEG."""
    return Response(
        _frame_stream(0, label="Webcam unavailable"),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/stream/webcam-json")
def stream_webcam_json():
    """Stream annotated webcam frames with JSON posture metadata."""
    return Response(
        _json_frame_stream(0, label="Webcam unavailable", cache_webcam_latest=True),
        mimetype="application/x-ndjson",
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


@app.get("/stream/video-json/<token>")
def stream_video_json(token: str):
    """Stream uploaded video frames with JSON posture metadata."""
    path = _VIDEO_UPLOADS.get(token)
    if path is None or not path.exists():
        return Response(
            _json_line({"error": "Video file not found."}),
            mimetype="application/x-ndjson",
            status=404,
        )

    return Response(
        _json_frame_stream(str(path), label="Video unavailable"),
        mimetype="application/x-ndjson",
    )


def _suffix(filename: str) -> str:
    return Path(filename).suffix.lower()


def _media_type(ext: str) -> str:
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return "unknown"


def _save_upload(uploaded, ext: str, token: str | None = None) -> Path:
    file_id = token or uuid.uuid4().hex
    path = UPLOAD_ROOT / f"{file_id}{ext}"
    uploaded.save(path)
    return path


def _frame_from_data_url(value) -> tuple[np.ndarray | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "image data URL is required."

    header, separator, encoded = value.partition(",")
    if separator != "," or not header.startswith("data:image/"):
        return None, "image must be a data:image URL."

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return None, "image data is not valid base64."

    frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return None, "OpenCV could not read this camera frame."
    return frame, None


def _teacher_sources(selection: str) -> list[dict[str, str | Path]]:
    if selection not in {"train", "val", "all"}:
        raise ValueError(f"Unsupported teacher source: {selection}")

    subsets = ("train", "val") if selection == "all" else (selection,)
    sources: list[dict[str, str | Path]] = []
    for subset in subsets:
        source_dir = TEACHER_IMAGE_ROOT / subset
        if not source_dir.is_dir():
            raise ValueError(f"Teacher image directory not found: {source_dir}")
        for path in sorted(source_dir.iterdir()):
            if path.suffix.lower() in IMAGE_EXTS:
                sources.append(
                    {
                        "path": path,
                        "name": f"teacher-{subset}/{path.name}",
                        "media_type": "image",
                    }
                )
    return sources


def _create_batch_export(token: str, sources: list[dict[str, str | Path]]) -> dict:
    export_dir = UPLOAD_ROOT / f"batch-export-{token}"
    export_dir.mkdir(parents=True, exist_ok=True)
    for category in CATEGORIES:
        (export_dir / category).mkdir(parents=True, exist_ok=True)
        (export_dir / "annotated" / category).mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    image_detector = None
    video_detector = None
    try:
        for idx, source in enumerate(sources, 1):
            path = Path(source["path"])
            display_name = str(source["name"])
            media_type = str(source["media_type"])
            export_name = _export_filename(idx, display_name, path.suffix)

            if media_type == "image":
                if image_detector is None:
                    image_detector = PoseDetector(static_image_mode=True)
                media_result, annotated = process_image_file(image_detector, str(path), display_name)
            elif media_type == "video":
                if video_detector is None:
                    video_detector = PoseDetector(static_image_mode=False)
                media_result, annotated = process_video_file(video_detector, str(path), display_name)
            else:
                continue

            rows.append(media_result.to_row())
            target_path = export_dir / media_result.category / export_name
            shutil.copy2(path, target_path)

            if annotated is not None:
                annotated_name = f"{Path(export_name).stem}.jpg"
                cv2.imwrite(str(export_dir / "annotated" / media_result.category / annotated_name), annotated)
    finally:
        if image_detector is not None:
            image_detector.close()
        if video_detector is not None:
            video_detector.close()

    summary = summarize_rows(rows)
    csv_path = export_dir / "batch_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    summary_path = export_dir / "summary.md"
    summary_path.write_text(render_summary_markdown(summary, rows), encoding="utf-8")

    zip_path = UPLOAD_ROOT / f"surf-posture-batch-{token}.zip"
    _zip_directory(export_dir, zip_path)
    _BATCH_EXPORTS[token] = zip_path

    return {
        "token": token,
        "summary": summary,
        "rows": rows[:100],
        "row_count": len(rows),
        "download_url": f"/api/batch-download/{token}",
    }


def _create_review_export(token: str, sources: list[dict[str, str | Path]]) -> dict:
    export_dir = UPLOAD_ROOT / f"dataset-review-{token}"
    for label in REVIEW_LABELS:
        (export_dir / "original" / label).mkdir(parents=True, exist_ok=True)
        (export_dir / "annotated" / label).mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    detector = None
    try:
        detector = PoseDetector(static_image_mode=True)
        for idx, source in enumerate(sources, 1):
            path = Path(source["path"])
            true_label = str(source["true_label"])
            display_name = str(source["name"])
            export_name = _export_filename(idx, display_name, path.suffix)

            media_result, annotated = process_image_file(detector, str(path), display_name)
            base_row = media_result.to_row()
            predicted_label = _prediction_label(base_row.get("posture", ""))
            evaluation_status = "evaluated" if predicted_label in REVIEW_LABELS else "needs_review"
            correct = predicted_label == true_label if evaluation_status == "evaluated" else ""

            original_path = export_dir / "original" / true_label / export_name
            shutil.copy2(path, original_path)
            annotated_file = ""
            if annotated is not None:
                annotated_name = f"{Path(export_name).stem}.jpg"
                annotated_path = export_dir / "annotated" / true_label / annotated_name
                cv2.imwrite(str(annotated_path), annotated)
                annotated_file = str(annotated_path.relative_to(export_dir))

            row = {
                "filename": display_name,
                "true_label": true_label,
                "predicted_label": predicted_label,
                "correct": correct,
                "evaluation_status": evaluation_status,
                "original_file": str(original_path.relative_to(export_dir)),
                "annotated_file": annotated_file,
            }
            for field in CSV_FIELDS:
                if field != "filename":
                    row[field] = base_row.get(field, "")
            rows.append(row)
    finally:
        if detector is not None:
            detector.close()

    summary = _review_metrics(rows)
    csv_path = export_dir / "review_report.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    metrics_path = export_dir / "metrics.json"
    metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    summary_path = export_dir / "summary.md"
    summary_path.write_text(_render_review_summary_markdown(summary, rows), encoding="utf-8")

    zip_path = UPLOAD_ROOT / f"surf-posture-review-{token}.zip"
    _zip_directory(export_dir, zip_path)
    _REVIEW_EXPORTS[token] = zip_path

    return {
        "token": token,
        "summary": summary,
        "rows": rows[:100],
        "row_count": len(rows),
        "download_url": f"/api/review-download/{token}",
    }


def _prediction_label(posture: str) -> str:
    value = str(posture or "").strip().lower()
    if value.startswith("good"):
        return "good"
    if value.startswith("bad"):
        return "bad"
    return "needs_review"


def _review_metrics(rows: list[dict]) -> dict:
    total = len(rows)
    evaluated_rows = [row for row in rows if row.get("evaluation_status") == "evaluated"]
    needs_review = total - len(evaluated_rows)
    tp = fp = tn = fn = 0
    correct = 0
    true_counts = {label: 0 for label in REVIEW_LABELS}
    predicted_counts = {label: 0 for label in (*REVIEW_LABELS, "needs_review")}

    for row in rows:
        true_label = row.get("true_label")
        predicted_label = row.get("predicted_label")
        if true_label in true_counts:
            true_counts[true_label] += 1
        if predicted_label in predicted_counts:
            predicted_counts[predicted_label] += 1

        if row.get("evaluation_status") != "evaluated":
            continue
        if predicted_label == true_label:
            correct += 1
        if true_label == REVIEW_POSITIVE_LABEL and predicted_label == REVIEW_POSITIVE_LABEL:
            tp += 1
        elif true_label != REVIEW_POSITIVE_LABEL and predicted_label == REVIEW_POSITIVE_LABEL:
            fp += 1
        elif true_label != REVIEW_POSITIVE_LABEL and predicted_label != REVIEW_POSITIVE_LABEL:
            tn += 1
        elif true_label == REVIEW_POSITIVE_LABEL and predicted_label != REVIEW_POSITIVE_LABEL:
            fn += 1

    precision = _safe_ratio(tp, tp + fp)
    recall = _safe_ratio(tp, tp + fn)
    return {
        "total": total,
        "evaluated": len(evaluated_rows),
        "needs_review": needs_review,
        "correct": correct,
        "positive_label": REVIEW_POSITIVE_LABEL,
        "accuracy": _safe_ratio(correct, len(evaluated_rows)),
        "precision": precision,
        "recall": recall,
        "f1": _safe_ratio(2 * precision * recall, precision + recall),
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
        },
        "true_counts": true_counts,
        "predicted_counts": predicted_counts,
        "map": None,
        "map_note": (
            "mAP is not computed by this rule-based review because it requires "
            "ground-truth boxes/keypoints and detector confidence outputs."
        ),
    }


def _safe_ratio(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 3) if denominator else 0.0


def _render_review_summary_markdown(summary: dict, rows: list[dict]) -> str:
    matrix = summary["confusion_matrix"]
    lines = [
        "# SURF Dataset Review Summary",
        "",
        "This is a rule-based baseline review for labeled good/bad posture photos.",
        "It is intended for dataset cleaning and meeting evidence, not final model evaluation.",
        "",
        f"- Total images: {summary['total']}",
        f"- Evaluated good/bad images: {summary['evaluated']}",
        f"- Needs manual review: {summary['needs_review']}",
        f"- Positive label for Precision/Recall/F1: `{summary['positive_label']}`",
        f"- Accuracy: {summary['accuracy']}",
        f"- Precision: {summary['precision']}",
        f"- Recall: {summary['recall']}",
        f"- F1: {summary['f1']}",
        f"- mAP: not computed. {summary['map_note']}",
        "",
        "## Confusion Matrix",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| TP | {matrix['tp']} |",
        f"| FP | {matrix['fp']} |",
        f"| TN | {matrix['tn']} |",
        f"| FN | {matrix['fn']} |",
        "",
        "## First 30 Results",
        "",
        "| File | True | Predicted | Status | Correct | Posture | Score | Missing Parts |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:30]:
        missing = str(row.get("missing_profile_parts", "")).replace("|", "/")
        lines.append(
            "| {filename} | {true_label} | {predicted_label} | {evaluation_status} | "
            "{correct} | {posture} | {score} | {missing} |".format(
                filename=str(row.get("filename", "")).replace("|", "/"),
                true_label=row.get("true_label", ""),
                predicted_label=row.get("predicted_label", ""),
                evaluation_status=row.get("evaluation_status", ""),
                correct=row.get("correct", ""),
                posture=str(row.get("posture", "")).replace("|", "/"),
                score=row.get("score", ""),
                missing=missing,
            )
        )
    lines.append("")
    return "\n".join(lines)


def _store_webcam_latest(original_frame, annotated_frame, result_payload: dict) -> bytes:
    original_jpeg = _encode_jpeg(original_frame)
    annotated_jpeg = _encode_jpeg(annotated_frame)
    with _WEBCAM_CAPTURE_LOCK:
        _WEBCAM_LATEST.clear()
        _WEBCAM_LATEST.update(
            {
                "original_jpeg": original_jpeg,
                "annotated_jpeg": annotated_jpeg,
                "result": result_payload,
                "stored_at": time.time(),
            }
        )
    return annotated_jpeg


def _capture_metadata() -> tuple[dict, str | None]:
    payload = request.get_json(silent=True) or {}
    collector = _clean_text(payload.get("collector", ""), 60)
    subject_id = _clean_text(payload.get("subject_id", ""), 60)
    label = _clean_text(payload.get("label", ""), 12).lower()
    notes = _clean_text(payload.get("notes", ""), 240)
    source = _clean_text(payload.get("source", "computer-webcam"), 40)
    reference = _clean_reference(payload.get("reference"))

    if not collector:
        return {}, "collector is required."
    if not subject_id:
        return {}, "subject_id is required."
    if label not in {"good", "bad"}:
        return {}, "label must be good or bad."
    if not _reference_complete(reference):
        return {}, "reference skeleton is required."

    return {
        "collector": collector,
        "subject_id": subject_id,
        "label": label,
        "notes": notes,
        "source": source or "computer-webcam",
        "reference": reference,
    }, None


def _reference_complete(reference: dict) -> bool:
    points = reference.get("points", {}) if isinstance(reference, dict) else {}
    return all(name in points for name in REFERENCE_POINT_NAMES)


def _clean_text(value, max_len: int) -> str:
    return str(value or "").strip()[:max_len]


def _clean_reference(reference) -> dict:
    if not isinstance(reference, dict):
        return {}

    raw_points = reference.get("points", {})
    points = {}
    if isinstance(raw_points, dict):
        for name in REFERENCE_POINT_NAMES:
            point = raw_points.get(name)
            if not isinstance(point, dict):
                continue
            try:
                x = min(1.0, max(0.0, float(point["x"])))
                y = min(1.0, max(0.0, float(point["y"])))
            except (KeyError, TypeError, ValueError):
                continue
            points[name] = {"x": round(x, 6), "y": round(y, 6)}

    raw_angles = reference.get("angles", {})
    angles = {}
    if isinstance(raw_angles, dict):
        for name in ANGLE_FIELD_NAMES:
            try:
                angles[name] = round(float(raw_angles[name]), 1)
            except (KeyError, TypeError, ValueError):
                continue

    raw_segment_angles = reference.get("segment_angles", {})
    segment_angles = {}
    if isinstance(raw_segment_angles, dict):
        for name in SEGMENT_FIELD_NAMES:
            try:
                segment_angles[name] = round(float(raw_segment_angles[name]), 1)
            except (KeyError, TypeError, ValueError):
                continue

    return {
        "points": points,
        "angles": angles,
        "segment_angles": segment_angles,
        "source": _clean_text(reference.get("source", "web"), 40),
        "updated_at": _clean_text(reference.get("updated_at", ""), 40),
    }


def _webcam_capture_payload(ready: bool) -> dict:
    download_url = (
        f"/api/webcam-captures-download/{_WEBCAM_CAPTURE_TOKEN}"
        if ready and _WEBCAM_CAPTURE_TOKEN
        else ""
    )
    return {
        "count": len(_WEBCAM_CAPTURES),
        "target": WEBCAM_CAPTURE_TARGET,
        "ready": ready,
        "download_url": download_url,
    }


def _create_webcam_capture_zip(token: str, captures: list[dict]) -> Path:
    export_dir = UPLOAD_ROOT / f"webcam-captures-{token}"
    original_dir = export_dir / "original"
    annotated_dir = export_dir / "mediapipe"
    original_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for capture in captures:
        index = int(capture["index"])
        original_path = original_dir / f"{index:02d}-original.jpg"
        annotated_path = annotated_dir / f"{index:02d}-mediapipe.jpg"
        original_path.write_bytes(capture["original_jpeg"])
        annotated_path.write_bytes(capture["annotated_jpeg"])
        result = capture["result"]
        metadata = capture.get("metadata", {})
        reference = metadata.get("reference", {})
        result_angles = _angles_by_name(result)
        result_segments = _segment_angles_by_name(result)
        reference_angles = reference.get("angles", {}) if isinstance(reference, dict) else {}
        reference_segments = reference.get("segment_angles", {}) if isinstance(reference, dict) else {}
        rows.append(
            {
                "index": index,
                "original_file": str(original_path.relative_to(export_dir)),
                "mediapipe_file": str(annotated_path.relative_to(export_dir)),
                "collector": metadata.get("collector", ""),
                "subject_id": metadata.get("subject_id", ""),
                "true_label": metadata.get("label", ""),
                "capture_source": metadata.get("source", ""),
                "captured_at": capture["captured_at"],
                "predicted_posture": result.get("posture", ""),
                "score": "" if result.get("score") is None else result.get("score"),
                "side": result.get("side", ""),
                "view": result.get("view", ""),
                "view_valid": result.get("view_valid", ""),
                "profile_complete": result.get("profile_complete", ""),
                "missing_profile_parts": ";".join(result.get("missing_profile_parts", []) or []),
                "ear_shoulder_hip_angle": _angle_value(result_angles, "ear_shoulder_hip"),
                "shoulder_hip_knee_angle": _angle_value(result_angles, "shoulder_hip_knee"),
                "hip_knee_ankle_angle": _angle_value(result_angles, "hip_knee_ankle"),
                "ear_shoulder_segment_angle": _segment_value(result_segments, "ear_shoulder"),
                "shoulder_hip_segment_angle": _segment_value(result_segments, "shoulder_hip"),
                "hip_knee_segment_angle": _segment_value(result_segments, "hip_knee"),
                "knee_ankle_segment_angle": _segment_value(result_segments, "knee_ankle"),
                "ear_shoulder_segment_reference_delta": _segment_reference_delta(
                    result_segments,
                    reference_segments,
                    "ear_shoulder",
                ),
                "shoulder_hip_segment_reference_delta": _segment_reference_delta(
                    result_segments,
                    reference_segments,
                    "shoulder_hip",
                ),
                "hip_knee_segment_reference_delta": _segment_reference_delta(
                    result_segments,
                    reference_segments,
                    "hip_knee",
                ),
                "knee_ankle_segment_reference_delta": _segment_reference_delta(
                    result_segments,
                    reference_segments,
                    "knee_ankle",
                ),
                "ear_shoulder_hip_reference_delta": _reference_delta(
                    result_angles,
                    reference_angles,
                    "ear_shoulder_hip",
                ),
                "shoulder_hip_knee_reference_delta": _reference_delta(
                    result_angles,
                    reference_angles,
                    "shoulder_hip_knee",
                ),
                "hip_knee_ankle_reference_delta": _reference_delta(
                    result_angles,
                    reference_angles,
                    "hip_knee_ankle",
                ),
                "notes": metadata.get("notes", ""),
            }
        )

    csv_path = export_dir / "capture_log.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    csv_path.rename(export_dir / "manifest.csv")

    reference_payload = {
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "capture_count": len(captures),
        "reference": captures[0].get("metadata", {}).get("reference", {}) if captures else {},
    }
    (export_dir / "reference.json").write_text(
        json.dumps(reference_payload, indent=2),
        encoding="utf-8",
    )

    summary_path = export_dir / "summary.md"
    summary_path.write_text(
        "\n".join(
            [
                "# SURF Webcam Capture Set",
                "",
                f"- Captures: {len(captures)}",
                f"- Collector: {captures[0].get('metadata', {}).get('collector', '') if captures else ''}",
                f"- Subject ID: {captures[0].get('metadata', {}).get('subject_id', '') if captures else ''}",
                f"- True label: {captures[0].get('metadata', {}).get('label', '') if captures else ''}",
                f"- Capture source: {captures[0].get('metadata', {}).get('source', '') if captures else ''}",
                "- Each capture includes the original webcam frame and the MediaPipe-processed frame.",
                "- `manifest.csv` contains collection labels and posture measurements for review.",
                "- `reference.json` contains the green reference skeleton used during collection.",
                "- This export is local-only and is not committed to Git.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    zip_path = UPLOAD_ROOT / f"surf-webcam-captures-{token}.zip"
    _zip_directory(export_dir, zip_path)
    return zip_path


def _angles_by_name(result: dict) -> dict:
    angles = {}
    for item in result.get("angles", []) or []:
        if isinstance(item, dict) and item.get("name"):
            angles[item["name"]] = item
    return angles


def _segment_angles_by_name(result: dict) -> dict:
    angles = {}
    for item in result.get("segment_angles", []) or []:
        if isinstance(item, dict) and item.get("name"):
            angles[item["name"]] = item
    return angles


def _angle_value(angles: dict, name: str):
    value = angles.get(name, {}).get("angle")
    return "" if value is None else value


def _segment_value(angles: dict, name: str):
    value = angles.get(name, {}).get("angle")
    return "" if value is None else value


def _reference_delta(result_angles: dict, reference_angles: dict, name: str):
    result_value = _angle_value(result_angles, name)
    reference_value = reference_angles.get(name) if isinstance(reference_angles, dict) else None
    if result_value == "" or reference_value is None:
        return ""
    try:
        return round(float(result_value) - float(reference_value), 1)
    except (TypeError, ValueError):
        return ""


def _segment_reference_delta(result_angles: dict, reference_angles: dict, name: str):
    result_value = _segment_value(result_angles, name)
    reference_value = reference_angles.get(name) if isinstance(reference_angles, dict) else None
    if result_value == "" or reference_value is None:
        return ""
    try:
        return round(float(result_value) - float(reference_value), 1)
    except (TypeError, ValueError):
        return ""


def _annotated_with_reference(jpeg_bytes: bytes, reference: dict) -> bytes:
    frame = cv2.imdecode(np.frombuffer(jpeg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return jpeg_bytes
    _draw_reference_overlay(frame, reference)
    return _encode_jpeg(frame)


def _draw_reference_overlay(frame, reference: dict) -> None:
    points = reference.get("points", {}) if isinstance(reference, dict) else {}
    if not points:
        return

    h, w = frame.shape[:2]
    px_points = []
    for name in REFERENCE_POINT_NAMES:
        point = points.get(name)
        if not isinstance(point, dict):
            return
        px_points.append((int(float(point["x"]) * w), int(float(point["y"]) * h)))

    green = (0, 180, 0)
    white = (255, 255, 255)
    for idx in range(len(px_points) - 1):
        cv2.line(frame, px_points[idx], px_points[idx + 1], green, 2, cv2.LINE_AA)
    for point in px_points:
        cv2.circle(frame, point, 7, green, -1, cv2.LINE_AA)
        cv2.circle(frame, point, 8, white, 1, cv2.LINE_AA)


def _export_filename(index: int, display_name: str, fallback_suffix: str) -> str:
    suffix = Path(display_name).suffix or fallback_suffix or ".dat"
    stem = Path(display_name).stem or f"item-{index}"
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-")[:80] or f"item-{index}"
    return f"{index:04d}-{safe_stem}{suffix.lower()}"


def _zip_directory(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))


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
            result = annotate_frame(detector, frame, show_text=False)
            frame = append_analysis_footer(frame, result)
            yield _multipart_frame(frame)
            time.sleep(delay)
    except Exception:
        yield _multipart_frame(_error_frame(_runtime_error_message()))
    finally:
        if cap is not None:
            cap.release()
        if detector is not None:
            detector.close()


def _json_frame_stream(source, label: str, cache_webcam_latest: bool = False):
    detector = None
    cap = None
    try:
        detector = PoseDetector(static_image_mode=False)
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            yield _json_line({"error": label})
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = 1.0 / min(max(fps or 12.0, 1.0), 18.0)

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            original_frame = frame.copy()
            result = annotate_frame(detector, frame, show_text=False)
            result_payload = result_to_dict(result)
            if cache_webcam_latest:
                jpeg = _store_webcam_latest(original_frame, frame, result_payload)
            else:
                jpeg = _encode_jpeg(frame)
            encoded = base64.b64encode(jpeg).decode("ascii")
            yield _json_line(
                {
                    "image": f"data:image/jpeg;base64,{encoded}",
                    "result": result_payload,
                }
            )
            time.sleep(delay)
    except Exception as exc:
        yield _json_line({"error": _runtime_error_message(), "detail": str(exc)})
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


def _json_line(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":")) + "\n"


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


def _json_error(message: str, status: int, detail: str | None = None):
    payload = {"error": message}
    if detail:
        payload["detail"] = detail
    return jsonify(payload), status


def _runtime_error_message() -> str:
    return (
        "MediaPipe/OpenGL could not start in this server session. "
        "Close old demo server windows and relaunch with start_web_demo.command "
        "from a normal macOS Terminal."
    )


def main() -> None:
    port = int(os.environ.get("SURF_WEB_PORT", "5050"))
    host = os.environ.get("SURF_WEB_HOST", "127.0.0.1")
    cert_file = os.environ.get("SURF_WEB_CERT_FILE", "").strip()
    key_file = os.environ.get("SURF_WEB_KEY_FILE", "").strip()
    ssl_context = (cert_file, key_file) if cert_file and key_file else None
    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True,
        use_reloader=False,
        ssl_context=ssl_context,
    )


if __name__ == "__main__":
    main()
