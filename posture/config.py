"""Configurable parameters for posture detection.

All thresholds and constants live here so they can be tuned in one place
without touching the analysis or display logic.
"""

# ---------------------------------------------------------------------------
# MediaPipe Pose landmark IDs
# Reference: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
# ---------------------------------------------------------------------------

LEFT_SIDE_IDS = {
    "ear": 7,
    "shoulder": 11,
    "hip": 23,
    "knee": 25,
    "ankle": 27,
}

RIGHT_SIDE_IDS = {
    "ear": 8,
    "shoulder": 12,
    "hip": 24,
    "knee": 26,
    "ankle": 28,
}

# ---------------------------------------------------------------------------
# View gate for side-view-only posture rules.
# If both left/right shoulders or hips are clearly visible and far apart in
# image x-coordinates, the person is likely front-facing rather than side-view.
# ---------------------------------------------------------------------------

VIEW_GATE = {
    "min_pair_visibility": 0.55,
    "front_shoulder_width": 0.22,
    "front_hip_width": 0.18,
}

# ---------------------------------------------------------------------------
# Data-collection profile quality gate.
# MediaPipe Pose does not expose explicit neck or buttock landmarks, so those
# are checked through side-profile proxy landmarks documented in analyzer.py.
# ---------------------------------------------------------------------------

PROFILE_VISIBILITY_THRESHOLD = 0.45

# ---------------------------------------------------------------------------
# Angle deviation thresholds (degrees away from 180°)
# Decision #2: start with experience-based values; interface preserved for
# future data-driven tuning.
# ---------------------------------------------------------------------------

THRESHOLDS = {
    "ear_shoulder_hip": 15.0,   # forward head
    "shoulder_hip_knee": 15.0,  # trunk lean
    "hip_knee_ankle": 15.0,     # knee hyperextension
}

# ---------------------------------------------------------------------------
# Teacher reference-line segment thresholds.
# These match the expected display:
#   E-S: ear to shoulder, S-H: shoulder to hip,
#   H-K: hip to knee, K-A: knee to ankle.
# The value is the segment's deviation from the vertical green reference line.
# ---------------------------------------------------------------------------

SEGMENT_THRESHOLDS = {
    "ear_shoulder": 10.0,
    "shoulder_hip": 10.0,
    "hip_knee": 10.0,
    "knee_ankle": 10.0,
}

SEGMENT_SCORE_WEIGHTS = {
    "ear_shoulder": 30,
    "shoulder_hip": 30,
    "hip_knee": 20,
    "knee_ankle": 20,
}

# ---------------------------------------------------------------------------
# MediaPipe ear landmark stabilization.
# In side-view photos, MediaPipe can place the ear landmark slightly forward on
# the face/hair contour. If the rest of the body reference line is already
# straight and only E-S is marginally over the threshold, snap the head point
# back to the reference line. Larger forward-head offsets still stay bad.
# ---------------------------------------------------------------------------

HEAD_LANDMARK_SNAP_DEGREES = 14.0
HEAD_LANDMARK_BODY_ALIGNMENT_DEGREES = 5.0

# ---------------------------------------------------------------------------
# Scoring weights (must sum to 100)
# ---------------------------------------------------------------------------

SCORE_WEIGHTS = {
    "ear_shoulder_hip": 40,
    "shoulder_hip_knee": 35,
    "hip_knee_ankle": 25,
}

# ---------------------------------------------------------------------------
# MediaPipe Pose configuration
# ---------------------------------------------------------------------------

POSE_CONFIG = {
    "model_complexity": 1,
    "min_detection_confidence": 0.5,
    "min_tracking_confidence": 0.5,
}

# ---------------------------------------------------------------------------
# Display colours (BGR for OpenCV)
# ---------------------------------------------------------------------------

COLOR_GOOD = (0, 200, 0)        # green
COLOR_WARNING = (0, 200, 255)   # yellow
COLOR_BAD = (0, 0, 255)         # red
COLOR_WHITE = (255, 255, 255)
COLOR_KEYPOINT = (0, 255, 255)  # cyan – highlighted keypoints
COLOR_ALIGNMENT = (0, 0, 255)   # red – current body segment line
COLOR_REFERENCE = (0, 180, 0)   # green – good-posture reference line
