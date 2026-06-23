"""Posture analysis engine.

Responsibilities
    1. ``pick_side``       – auto-detect which body side faces the camera
    2. ``calc_angle``      – compute the angle at the middle of three points
    3. ``analyze_posture`` – full pipeline: pick side → angles → score → advice
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

from posture.config import (
    LEFT_SIDE_IDS,
    PROFILE_VISIBILITY_THRESHOLD,
    RIGHT_SIDE_IDS,
    SCORE_WEIGHTS,
    THRESHOLDS,
    VIEW_GATE,
)

# ======================================================================
# Data classes – structured results
# ======================================================================


@dataclass
class AngleResult:
    """Measurement for one body-segment angle."""

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


@dataclass
class PostureResult:
    """Complete posture-analysis output."""

    detected: bool = False
    side: str = ""                                           # "left" | "right"
    view: str = "unknown"                                    # "side" | "front"
    view_valid: bool = True
    message: str = ""
    angles: List[AngleResult] = field(default_factory=list)
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


def check_profile_parts(landmarks, side_ids: dict) -> Tuple[bool, List[str], List[ProfilePartResult]]:
    """Check whether teacher-required side-profile parts are visible.

    MediaPipe Pose has no explicit neck or buttock landmark. For collection
    gating, ``Neck`` is represented by the visible ear-shoulder segment and
    ``Buttock`` is represented by the visible hip landmark. This keeps the
    quality gate aligned with the teacher's anatomical checklist while staying
    inside the available landmark set.
    """
    ear = landmarks[side_ids["ear"]]
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

    Steps
        1. Pick the body side facing the camera.
        2. Extract 5 keypoints (ear / shoulder / hip / knee / ankle).
        3. Compute 3 joint angles.
        4. Score each angle against its threshold.
        5. Produce a weighted overall score and advice list.
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
    ear = landmarks[side_ids["ear"]]
    shoulder = landmarks[side_ids["shoulder"]]
    hip = landmarks[side_ids["hip"]]
    knee = landmarks[side_ids["knee"]]
    ankle = landmarks[side_ids["ankle"]]

    result.keypoint_coords = [
        (ear.x, ear.y),
        (shoulder.x, shoulder.y),
        (hip.x, hip.y),
        (knee.x, knee.y),
        (ankle.x, ankle.y),
    ]

    profile_complete, missing_profile_parts, profile_parts = check_profile_parts(landmarks, side_ids)
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

    total_score = 100.0

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

        if not is_good:
            result.overall_good = False
            result.issues.append(info["label"])
            result.advice.append(info["advice"])

            # proportional deduction: fully lost at threshold + 30°
            weight = SCORE_WEIGHTS[name]
            excess = deviation - threshold
            deduction = min(weight, weight * excess / 30.0)
            total_score -= deduction

    result.score = round(max(0.0, total_score), 1)
    return result
