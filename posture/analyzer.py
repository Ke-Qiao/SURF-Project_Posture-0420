"""Posture analysis engine.

Responsibilities
    1. ``pick_side``       – auto-detect which body side faces the camera
    2. ``calc_angle``      – compute the angle at the middle of three points
    3. ``analyze_posture`` – full pipeline: pick side → reference segment angles → score
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

from posture.config import (
    HEAD_LANDMARK_BODY_ALIGNMENT_DEGREES,
    HEAD_LANDMARK_SNAP_DEGREES,
    LEFT_SIDE_IDS,
    PROFILE_VISIBILITY_THRESHOLD,
    RIGHT_SIDE_IDS,
    SEGMENT_SCORE_WEIGHTS,
    SEGMENT_THRESHOLDS,
    THRESHOLDS,
    VIEW_GATE,
)

# ======================================================================
# Data classes – structured results
# ======================================================================


@dataclass
class AngleResult:
    """Auxiliary joint-angle measurement."""

    name: str          # e.g. "ear_shoulder_hip"
    angle: float       # actual angle (degrees)
    deviation: float   # |180 − angle|
    threshold: float   # configured threshold
    is_good: bool      # deviation ≤ threshold?
    label: str         # human-readable, e.g. "Forward Head"


@dataclass
class ProfilePartResult:
    """Collection-quality check for one required side-profile body part."""

    name: str
    visible: bool
    visibility: float
    proxy: str


@dataclass(frozen=True)
class LandmarkPoint:
    """Minimal landmark-like point used for stabilized keypoints."""

    x: float
    y: float
    visibility: float


@dataclass
class SegmentAngleResult:
    """Deviation of one body segment from the vertical reference line."""

    name: str
    label: str
    start: str
    end: str
    angle: float
    threshold: float
    is_good: bool


@dataclass
class PostureResult:
    """Complete posture-analysis output."""

    detected: bool = False
    side: str = ""                                           # "left" | "right"
    view: str = "unknown"                                    # "side" | "front"
    view_valid: bool = True
    message: str = ""
    angles: List[AngleResult] = field(default_factory=list)
    segment_angles: List[SegmentAngleResult] = field(default_factory=list)
    score: float = 0.0                                       # 0–100
    overall_good: bool = True
    issues: List[str] = field(default_factory=list)
    advice: List[str] = field(default_factory=list)
    keypoint_coords: List[Tuple[float, float]] = field(default_factory=list)
    profile_complete: bool = False
    missing_profile_parts: List[str] = field(default_factory=list)
    profile_parts: List[ProfilePartResult] = field(default_factory=list)


# ======================================================================
# Angle metadata (Decision #4: English)
# ======================================================================

_ANGLE_INFO = {
    "ear_shoulder_hip": {
        "label": "Forward Head",
        "advice": "Tuck your chin and align your ears over your shoulders",
    },
    "shoulder_hip_knee": {
        "label": "Trunk Lean",
        "advice": "Engage your core and bring pelvis to neutral",
    },
    "hip_knee_ankle": {
        "label": "Knee Hyperextension",
        "advice": "Soften your knees slightly, avoid locking them",
    },
}

_SEGMENT_INFO = {
    "ear_shoulder": {
        "label": "E-S",
        "start": "ear",
        "end": "shoulder",
        "advice": "Keep your ear vertically aligned above your shoulder",
    },
    "shoulder_hip": {
        "label": "S-H",
        "start": "shoulder",
        "end": "hip",
        "advice": "Stack your shoulder over your hip",
    },
    "hip_knee": {
        "label": "H-K",
        "start": "hip",
        "end": "knee",
        "advice": "Keep your hip, knee, and ankle aligned from the side",
    },
    "knee_ankle": {
        "label": "K-A",
        "start": "knee",
        "end": "ankle",
        "advice": "Keep your knee vertically aligned above your ankle",
    },
}

# ======================================================================
# Core functions
# ======================================================================


def pick_side(landmarks) -> Tuple[str, dict]:
    """Choose the body side that faces the camera.

    Decision #1: compare summed *visibility* of the five key landmarks on
    each side; the side with the higher total is returned.

    Returns
        ``("left" | "right", {name: landmark_id})``
    """
    left_vis = sum(landmarks[lid].visibility for lid in LEFT_SIDE_IDS.values())
    right_vis = sum(landmarks[lid].visibility for lid in RIGHT_SIDE_IDS.values())
    if right_vis >= left_vis:
        return "right", RIGHT_SIDE_IDS
    return "left", LEFT_SIDE_IDS


def is_side_view(landmarks) -> bool:
    """Return False when the body is clearly front-facing.

    The side-view angle rules are only valid when left/right shoulder and hip
    landmarks mostly overlap horizontally. In a front view, those paired
    landmarks are both visible and far apart, so the 2D ear-shoulder-hip angle
    becomes a projection artifact rather than a forward-head measure.
    """
    min_vis = VIEW_GATE["min_pair_visibility"]

    left_shoulder = landmarks[LEFT_SIDE_IDS["shoulder"]]
    right_shoulder = landmarks[RIGHT_SIDE_IDS["shoulder"]]
    left_hip = landmarks[LEFT_SIDE_IDS["hip"]]
    right_hip = landmarks[RIGHT_SIDE_IDS["hip"]]

    shoulders_visible = (
        left_shoulder.visibility >= min_vis
        and right_shoulder.visibility >= min_vis
    )
    hips_visible = left_hip.visibility >= min_vis and right_hip.visibility >= min_vis

    shoulder_width = abs(left_shoulder.x - right_shoulder.x)
    hip_width = abs(left_hip.x - right_hip.x)

    if shoulders_visible and shoulder_width >= VIEW_GATE["front_shoulder_width"]:
        return False
    if hips_visible and hip_width >= VIEW_GATE["front_hip_width"]:
        return False

    return True


def calc_angle(a, b, c) -> float:
    """Return the angle (degrees) at *b* formed by the line segments *a→b→c*.

    Each argument must expose ``.x`` and ``.y`` attributes (MediaPipe
    landmark).  Result is clamped to [0, 180].
    """
    ba = (a.x - b.x, a.y - b.y)
    bc = (c.x - b.x, c.y - b.y)

    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.hypot(*ba)
    mag_bc = math.hypot(*bc)

    if mag_ba * mag_bc == 0:
        return 0.0

    cos_angle = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cos_angle))


def calc_vertical_deviation(a, b) -> float:
    """Return one segment's deviation from the vertical reference line."""
    dx = abs(a.x - b.x)
    dy = abs(a.y - b.y)
    if dx == 0 and dy == 0:
        return 0.0
    return math.degrees(math.atan2(dx, dy))


def calc_reference_deviation(start, lower, reference_x: float) -> float:
    """Return the tilt from a point to the next point on the reference line.

    The teacher reference is a vertical green line. For segment E-S, for
    example, we measure the angle from the current ear point to the shoulder
    height on that vertical reference line. A perfectly aligned segment is 0°.
    """
    dx = abs(start.x - reference_x)
    dy = abs(start.y - lower.y)
    if dx == 0 and dy == 0:
        return 0.0
    return math.degrees(math.atan2(dx, dy))


def reference_line_x(points) -> float:
    """Use shoulder/hip/knee/ankle median x as the green reference axis."""
    values = sorted(point.x for point in points)
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def stabilize_ear_point(raw_ear, shoulder, hip, knee, ankle, reference_x: float):
    """Correct small side-view ear drift caused by MediaPipe landmark noise.

    The correction is intentionally narrow: it only applies when shoulder,
    hip, knee, and ankle are already close to the vertical reference line, and
    the raw ear deviation is just beyond the E-S threshold. Clear forward-head
    offsets remain unmodified and still score as bad.
    """
    body_deviations = [
        calc_reference_deviation(shoulder, hip, reference_x),
        calc_reference_deviation(hip, knee, reference_x),
        calc_reference_deviation(knee, ankle, reference_x),
    ]
    body_is_stable = all(
        angle <= HEAD_LANDMARK_BODY_ALIGNMENT_DEGREES
        for angle in body_deviations
    )
    ear_deviation = calc_reference_deviation(raw_ear, shoulder, reference_x)
    marginal_ear_drift = (
        SEGMENT_THRESHOLDS["ear_shoulder"]
        < ear_deviation
        <= HEAD_LANDMARK_SNAP_DEGREES
    )

    if body_is_stable and marginal_ear_drift:
        return LandmarkPoint(
            x=reference_x,
            y=raw_ear.y,
            visibility=raw_ear.visibility,
        )

    return raw_ear


def check_profile_parts(landmarks, side_ids: dict, ear=None) -> Tuple[bool, List[str], List[ProfilePartResult]]:
    """Check whether teacher-required side-profile parts are visible.

    MediaPipe Pose has no explicit neck or buttock landmark. For collection
    gating, ``Neck`` is represented by the visible ear-shoulder segment and
    ``Buttock`` is represented by the visible hip landmark. This keeps the
    quality gate aligned with the teacher's anatomical checklist while staying
    inside the available landmark set.
    """
    ear = ear or landmarks[side_ids["ear"]]
    shoulder = landmarks[side_ids["shoulder"]]
    hip = landmarks[side_ids["hip"]]
    knee = landmarks[side_ids["knee"]]
    ankle = landmarks[side_ids["ankle"]]

    checks = [
        ("Head", ear.visibility, "ear"),
        ("Neck", min(ear.visibility, shoulder.visibility), "ear-shoulder segment"),
        ("Shoulder", shoulder.visibility, "shoulder"),
        ("Hip", hip.visibility, "hip"),
        ("Buttock", hip.visibility, "hip proxy"),
        ("Knees", knee.visibility, "knee"),
        ("Ankle", ankle.visibility, "ankle"),
    ]

    parts = [
        ProfilePartResult(
            name=name,
            visible=visibility >= PROFILE_VISIBILITY_THRESHOLD,
            visibility=round(float(visibility), 3),
            proxy=proxy,
        )
        for name, visibility, proxy in checks
    ]
    missing = [part.name for part in parts if not part.visible]
    return not missing, missing, parts


def analyze_posture(landmarks) -> PostureResult:
    """Run the full posture-analysis pipeline.

    The teacher-facing Good/Bad decision is based on four segment deviations
    from a vertical green reference line: E-S, S-H, H-K, and K-A. A perfect
    reference-aligned posture is 0 degrees; the current conservative threshold
    is 10 degrees.
    """
    result = PostureResult()

    if landmarks is None:
        return result

    result.detected = True

    if not is_side_view(landmarks):
        result.view = "front"
        result.view_valid = False
        result.message = "Front view detected. Turn sideways for side-view analysis."
        result.overall_good = False
        result.advice.append("Turn to a clear side view before posture scoring")
        return result

    result.view = "side"

    # ---- 1. side selection ----
    side_name, side_ids = pick_side(landmarks)
    result.side = side_name

    # ---- 2. keypoints ----
    shoulder = landmarks[side_ids["shoulder"]]
    hip = landmarks[side_ids["hip"]]
    knee = landmarks[side_ids["knee"]]
    ankle = landmarks[side_ids["ankle"]]
    reference_x = reference_line_x([shoulder, hip, knee, ankle])
    ear = stabilize_ear_point(
        landmarks[side_ids["ear"]],
        shoulder,
        hip,
        knee,
        ankle,
        reference_x,
    )

    result.keypoint_coords = [
        (ear.x, ear.y),
        (shoulder.x, shoulder.y),
        (hip.x, hip.y),
        (knee.x, knee.y),
        (ankle.x, ankle.y),
    ]

    profile_complete, missing_profile_parts, profile_parts = check_profile_parts(landmarks, side_ids, ear=ear)
    result.profile_complete = profile_complete
    result.missing_profile_parts = missing_profile_parts
    result.profile_parts = profile_parts
    if not profile_complete:
        result.overall_good = False
        result.message = "Missing required side-profile parts: " + ", ".join(missing_profile_parts)
        result.advice.append("Retake the photo with head, neck, shoulder, hip, buttock, knees, and ankle visible")
        return result

    # ---- 3. angles ----
    angle_triplets = [
        ("ear_shoulder_hip", ear, shoulder, hip),
        ("shoulder_hip_knee", shoulder, hip, knee),
        ("hip_knee_ankle", hip, knee, ankle),
    ]

    segment_score = 100.0

    for name, pt_a, pt_b, pt_c in angle_triplets:
        angle = calc_angle(pt_a, pt_b, pt_c)
        deviation = abs(180.0 - angle)
        threshold = THRESHOLDS[name]
        is_good = deviation <= threshold
        info = _ANGLE_INFO[name]

        result.angles.append(
            AngleResult(
                name=name,
                angle=round(angle, 1),
                deviation=round(deviation, 1),
                threshold=threshold,
                is_good=is_good,
                label=info["label"],
            )
        )

    # ---- 4. teacher reference-line segment deviations ----
    segment_pairs = [
        ("ear_shoulder", ear, shoulder),
        ("shoulder_hip", shoulder, hip),
        ("hip_knee", hip, knee),
        ("knee_ankle", knee, ankle),
    ]

    for name, pt_a, pt_b in segment_pairs:
        angle = calc_reference_deviation(pt_a, pt_b, reference_x)
        threshold = SEGMENT_THRESHOLDS[name]
        is_good = angle <= threshold
        info = _SEGMENT_INFO[name]

        result.segment_angles.append(
            SegmentAngleResult(
                name=name,
                label=info["label"],
                start=info["start"],
                end=info["end"],
                angle=round(angle, 1),
                threshold=threshold,
                is_good=is_good,
            )
        )

        if not is_good:
            result.overall_good = False
            if info["label"] not in result.issues:
                result.issues.append(info["label"])
            if info["advice"] not in result.advice:
                result.advice.append(info["advice"])

            weight = SEGMENT_SCORE_WEIGHTS[name]
            excess = angle - threshold
            deduction = min(weight, weight * excess / 30.0)
            segment_score -= deduction

    result.score = round(max(0.0, segment_score), 1)
    return result
