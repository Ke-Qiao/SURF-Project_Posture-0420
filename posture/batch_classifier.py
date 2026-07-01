"""Rule-based batch media classification for the Week 1 demo.

This module intentionally uses MediaPipe landmarks and simple geometry rules.
It is not a trained posture classifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2

from posture.analyzer import analyze_posture, calc_angle
from posture.config import LEFT_SIDE_IDS, RIGHT_SIDE_IDS
from posture.pipeline import result_to_dict
from posture.visualizer import append_analysis_footer, draw_analysis


CATEGORY_STANDING = "standing"
CATEGORY_SITTING = "sitting"
CATEGORY_INCOMPLETE = "incomplete"
CATEGORIES = (CATEGORY_STANDING, CATEGORY_SITTING, CATEGORY_INCOMPLETE)

VISIBILITY_THRESHOLD = 0.45
MAX_VIDEO_SAMPLES = 30


@dataclass
class Classification:
    category: str
    confidence: float
    reason: str
    knee_angle: float | None = None


@dataclass
class BatchMediaResult:
    filename: str
    media_type: str
    category: str
    confidence: float
    reason: str
    detected: bool = False
    posture: str = "No detection"
    score: float | None = None
    side: str = ""
    view: str = "unknown"
    view_valid: bool = False
    profile_complete: bool = False
    missing_profile_parts: str = ""
    knee_angle: float | None = None
    ear_shoulder_hip_angle: float | None = None
    shoulder_hip_knee_angle: float | None = None
    hip_knee_ankle_angle: float | None = None
    ear_shoulder_segment_angle: float | None = None
    shoulder_hip_segment_angle: float | None = None
    hip_knee_segment_angle: float | None = None
    knee_ankle_segment_angle: float | None = None
    frames_sampled: int = 0
    standing_votes: int = 0
    sitting_votes: int = 0
    incomplete_votes: int = 0

    def to_row(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "media_type": self.media_type,
            "category": self.category,
            "confidence": self.confidence,
            "reason": self.reason,
            "detected": self.detected,
            "posture": self.posture,
            "score": "" if self.score is None else self.score,
            "side": self.side,
            "view": self.view,
            "view_valid": self.view_valid,
            "profile_complete": self.profile_complete,
            "missing_profile_parts": self.missing_profile_parts,
            "knee_angle": "" if self.knee_angle is None else self.knee_angle,
            "ear_shoulder_hip_angle": "" if self.ear_shoulder_hip_angle is None else self.ear_shoulder_hip_angle,
            "shoulder_hip_knee_angle": "" if self.shoulder_hip_knee_angle is None else self.shoulder_hip_knee_angle,
            "hip_knee_ankle_angle": "" if self.hip_knee_ankle_angle is None else self.hip_knee_ankle_angle,
            "ear_shoulder_segment_angle": "" if self.ear_shoulder_segment_angle is None else self.ear_shoulder_segment_angle,
            "shoulder_hip_segment_angle": "" if self.shoulder_hip_segment_angle is None else self.shoulder_hip_segment_angle,
            "hip_knee_segment_angle": "" if self.hip_knee_segment_angle is None else self.hip_knee_segment_angle,
            "knee_ankle_segment_angle": "" if self.knee_ankle_segment_angle is None else self.knee_ankle_segment_angle,
            "frames_sampled": self.frames_sampled,
            "standing_votes": self.standing_votes,
            "sitting_votes": self.sitting_votes,
            "incomplete_votes": self.incomplete_votes,
        }


CSV_FIELDS = list(BatchMediaResult("", "", "", 0.0, "").to_row().keys())


def classify_landmarks(landmarks) -> Classification:
    """Classify one pose as standing, sitting, or incomplete.

    The rules are conservative. If the lower body is missing or the geometry
    does not clearly match standing/sitting, return ``incomplete``.
    """
    if landmarks is None:
        return Classification(CATEGORY_INCOMPLETE, 1.0, "No person detected")

    visible_groups = _visible_body_groups(landmarks)
    required_groups = {"shoulder", "hip", "knee", "ankle"}
    missing = sorted(required_groups - visible_groups)
    if missing:
        return Classification(
            CATEGORY_INCOMPLETE,
            0.92,
            f"Missing or low-confidence body groups: {', '.join(missing)}",
        )

    side_ids, side_visibility = _best_lower_body_side(landmarks)
    if side_visibility < VISIBILITY_THRESHOLD * 3:
        return Classification(
            CATEGORY_INCOMPLETE,
            0.9,
            "Lower-body landmarks are too weak for standing/sitting rules",
        )

    hip = landmarks[side_ids["hip"]]
    knee = landmarks[side_ids["knee"]]
    ankle = landmarks[side_ids["ankle"]]
    knee_angle = round(calc_angle(hip, knee, ankle), 1)
    hip_to_ankle_span = ankle.y - hip.y
    hip_knee_gap = abs(knee.y - hip.y)
    vertical_order = ankle.y > knee.y > hip.y - 0.05

    if knee_angle <= 135.0 or hip_knee_gap <= 0.16:
        confidence = min(0.95, 0.62 + max(0.0, 135.0 - knee_angle) / 90.0)
        return Classification(
            CATEGORY_SITTING,
            round(confidence, 2),
            "Bent knee or hip-knee alignment suggests sitting",
            knee_angle,
        )

    if knee_angle >= 150.0 and hip_to_ankle_span >= 0.22 and vertical_order:
        confidence = min(0.95, 0.62 + (knee_angle - 150.0) / 120.0 + min(hip_to_ankle_span, 0.5) / 4.0)
        return Classification(
            CATEGORY_STANDING,
            round(confidence, 2),
            "Visible lower body with extended knee suggests standing",
            knee_angle,
        )

    return Classification(
        CATEGORY_INCOMPLETE,
        0.72,
        "Pose is detected but not clearly standing or sitting",
        knee_angle,
    )


def process_image_file(detector, image_path: str, filename: str) -> tuple[BatchMediaResult, Any | None]:
    """Analyze and classify one image file."""
    frame = cv2.imread(image_path)
    if frame is None:
        return (
            BatchMediaResult(
                filename=filename,
                media_type="image",
                category=CATEGORY_INCOMPLETE,
                confidence=1.0,
                reason="OpenCV could not read image",
            ),
            None,
        )

    result, classification, annotated = _process_frame(detector, frame)
    posture_payload = result_to_dict(result)
    posture_details = _posture_details(posture_payload)
    media_result = BatchMediaResult(
        filename=filename,
        media_type="image",
        category=classification.category,
        confidence=classification.confidence,
        reason=classification.reason,
        detected=result.detected,
        posture=posture_payload["posture"],
        score=posture_payload["score"],
        side=result.side,
        view=result.view,
        view_valid=result.view_valid,
        profile_complete=posture_details["profile_complete"],
        missing_profile_parts=posture_details["missing_profile_parts"],
        knee_angle=classification.knee_angle,
        ear_shoulder_hip_angle=posture_details["ear_shoulder_hip_angle"],
        shoulder_hip_knee_angle=posture_details["shoulder_hip_knee_angle"],
        hip_knee_ankle_angle=posture_details["hip_knee_ankle_angle"],
        ear_shoulder_segment_angle=posture_details["ear_shoulder_segment_angle"],
        shoulder_hip_segment_angle=posture_details["shoulder_hip_segment_angle"],
        hip_knee_segment_angle=posture_details["hip_knee_segment_angle"],
        knee_ankle_segment_angle=posture_details["knee_ankle_segment_angle"],
        frames_sampled=1,
        standing_votes=1 if classification.category == CATEGORY_STANDING else 0,
        sitting_votes=1 if classification.category == CATEGORY_SITTING else 0,
        incomplete_votes=1 if classification.category == CATEGORY_INCOMPLETE else 0,
    )
    return media_result, annotated


def process_video_file(detector, video_path: str, filename: str, max_samples: int = MAX_VIDEO_SAMPLES) -> tuple[BatchMediaResult, Any | None]:
    """Sample and classify one video file."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return (
            BatchMediaResult(
                filename=filename,
                media_type="video",
                category=CATEGORY_INCOMPLETE,
                confidence=1.0,
                reason="OpenCV could not open video",
            ),
            None,
        )

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    sample_step = max(1, int(frame_count / max_samples)) if frame_count else 15
    votes = {category: 0 for category in CATEGORIES}
    sampled = 0
    first_annotated = None
    latest_result = None
    latest_classification: Classification | None = None
    frame_index = 0

    try:
        while sampled < max_samples:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % sample_step != 0:
                frame_index += 1
                continue

            result, classification, annotated = _process_frame(detector, frame)
            votes[classification.category] += 1
            sampled += 1
            latest_result = result
            latest_classification = classification
            if first_annotated is None:
                first_annotated = annotated
            frame_index += 1
    finally:
        cap.release()

    if sampled == 0 or latest_result is None or latest_classification is None:
        return (
            BatchMediaResult(
                filename=filename,
                media_type="video",
                category=CATEGORY_INCOMPLETE,
                confidence=1.0,
                reason="No readable frames sampled from video",
            ),
            first_annotated,
        )

    category = max(CATEGORIES, key=lambda item: votes[item])
    confidence = round(votes[category] / sampled, 2)
    posture_payload = result_to_dict(latest_result)
    posture_details = _posture_details(posture_payload)
    media_result = BatchMediaResult(
        filename=filename,
        media_type="video",
        category=category,
        confidence=confidence,
        reason=f"Video majority vote: {votes[category]}/{sampled} sampled frames classified as {category}",
        detected=latest_result.detected,
        posture=posture_payload["posture"],
        score=posture_payload["score"],
        side=latest_result.side,
        view=latest_result.view,
        view_valid=latest_result.view_valid,
        profile_complete=posture_details["profile_complete"],
        missing_profile_parts=posture_details["missing_profile_parts"],
        knee_angle=latest_classification.knee_angle,
        ear_shoulder_hip_angle=posture_details["ear_shoulder_hip_angle"],
        shoulder_hip_knee_angle=posture_details["shoulder_hip_knee_angle"],
        hip_knee_ankle_angle=posture_details["hip_knee_ankle_angle"],
        ear_shoulder_segment_angle=posture_details["ear_shoulder_segment_angle"],
        shoulder_hip_segment_angle=posture_details["shoulder_hip_segment_angle"],
        hip_knee_segment_angle=posture_details["hip_knee_segment_angle"],
        knee_ankle_segment_angle=posture_details["knee_ankle_segment_angle"],
        frames_sampled=sampled,
        standing_votes=votes[CATEGORY_STANDING],
        sitting_votes=votes[CATEGORY_SITTING],
        incomplete_votes=votes[CATEGORY_INCOMPLETE],
    )
    return media_result, first_annotated


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {category: 0 for category in CATEGORIES}
    media_counts = {"image": 0, "video": 0}
    for row in rows:
        counts[row["category"]] = counts.get(row["category"], 0) + 1
        media_counts[row["media_type"]] = media_counts.get(row["media_type"], 0) + 1

    total = len(rows)
    return {
        "total": total,
        "counts": counts,
        "media_counts": media_counts,
        "standing_rate": round(counts[CATEGORY_STANDING] / total, 3) if total else 0.0,
        "sitting_rate": round(counts[CATEGORY_SITTING] / total, 3) if total else 0.0,
        "incomplete_rate": round(counts[CATEGORY_INCOMPLETE] / total, 3) if total else 0.0,
    }


def render_summary_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    counts = summary["counts"]
    media_counts = summary["media_counts"]
    lines = [
        "# SURF Batch Classification Summary",
        "",
        "This is a rule-based auto-suggestion for Week 1 dataset triage. It is not a trained model.",
        "",
        f"- Total files: {summary['total']}",
        f"- Images: {media_counts.get('image', 0)}",
        f"- Videos: {media_counts.get('video', 0)}",
        f"- Standing: {counts.get(CATEGORY_STANDING, 0)}",
        f"- Sitting: {counts.get(CATEGORY_SITTING, 0)}",
        f"- Incomplete: {counts.get(CATEGORY_INCOMPLETE, 0)}",
        "",
        "## First 20 Results",
        "",
        "| File | Media | Category | Confidence | Reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows[:20]:
        reason = str(row["reason"]).replace("|", "/")
        lines.append(
            f"| {row['filename']} | {row['media_type']} | {row['category']} | {row['confidence']} | {reason} |"
        )
    lines.append("")
    return "\n".join(lines)


def _posture_details(posture_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "profile_complete": bool(posture_payload.get("profile_complete", False)),
        "missing_profile_parts": ";".join(posture_payload.get("missing_profile_parts", []) or []),
        "ear_shoulder_hip_angle": _angle_payload_value(posture_payload, "ear_shoulder_hip"),
        "shoulder_hip_knee_angle": _angle_payload_value(posture_payload, "shoulder_hip_knee"),
        "hip_knee_ankle_angle": _angle_payload_value(posture_payload, "hip_knee_ankle"),
        "ear_shoulder_segment_angle": _segment_payload_value(posture_payload, "ear_shoulder"),
        "shoulder_hip_segment_angle": _segment_payload_value(posture_payload, "shoulder_hip"),
        "hip_knee_segment_angle": _segment_payload_value(posture_payload, "hip_knee"),
        "knee_ankle_segment_angle": _segment_payload_value(posture_payload, "knee_ankle"),
    }


def _angle_payload_value(posture_payload: dict[str, Any], name: str) -> float | None:
    for item in posture_payload.get("angles", []) or []:
        if isinstance(item, dict) and item.get("name") == name:
            return item.get("angle")
    return None


def _segment_payload_value(posture_payload: dict[str, Any], name: str) -> float | None:
    for item in posture_payload.get("segment_angles", []) or []:
        if isinstance(item, dict) and item.get("name") == name:
            return item.get("angle")
    return None


def _process_frame(detector, frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = detector.process(rgb)
    detector.draw_skeleton(frame, results)
    landmarks = detector.get_landmarks(results)
    posture_result = analyze_posture(landmarks)
    draw_analysis(frame, posture_result, show_text=False)
    classification = classify_landmarks(landmarks)
    _draw_classification_badge(frame, classification)
    annotated = append_analysis_footer(frame, posture_result)
    return posture_result, classification, annotated


def _visible_body_groups(landmarks) -> set[str]:
    groups = {
        "head": [LEFT_SIDE_IDS["ear"], RIGHT_SIDE_IDS["ear"]],
        "shoulder": [LEFT_SIDE_IDS["shoulder"], RIGHT_SIDE_IDS["shoulder"]],
        "hip": [LEFT_SIDE_IDS["hip"], RIGHT_SIDE_IDS["hip"]],
        "knee": [LEFT_SIDE_IDS["knee"], RIGHT_SIDE_IDS["knee"]],
        "ankle": [LEFT_SIDE_IDS["ankle"], RIGHT_SIDE_IDS["ankle"]],
    }
    visible = set()
    for name, ids in groups.items():
        if any(landmarks[idx].visibility >= VISIBILITY_THRESHOLD for idx in ids):
            visible.add(name)
    return visible


def _best_lower_body_side(landmarks):
    left_score = sum(landmarks[LEFT_SIDE_IDS[name]].visibility for name in ("hip", "knee", "ankle"))
    right_score = sum(landmarks[RIGHT_SIDE_IDS[name]].visibility for name in ("hip", "knee", "ankle"))
    if right_score >= left_score:
        return RIGHT_SIDE_IDS, right_score
    return LEFT_SIDE_IDS, left_score


def _draw_classification_badge(frame, classification: Classification) -> None:
    color = {
        CATEGORY_STANDING: (0, 170, 0),
        CATEGORY_SITTING: (0, 170, 255),
        CATEGORY_INCOMPLETE: (0, 0, 220),
    }[classification.category]
    label = f"{classification.category.upper()}  {classification.confidence:.2f}"
    cv2.rectangle(frame, (18, 18), (330, 58), (20, 24, 22), -1)
    cv2.putText(
        frame,
        label,
        (30, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        color,
        2,
        cv2.LINE_AA,
    )
