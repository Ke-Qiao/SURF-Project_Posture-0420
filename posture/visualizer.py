"""OpenCV drawing utilities for posture analysis results.

All overlay rendering is isolated here so that analysis logic stays
free of any display concerns.
"""

from __future__ import annotations

import cv2

from posture.analyzer import PostureResult
from posture.config import (
    COLOR_ALIGNMENT,
    COLOR_BAD,
    COLOR_GOOD,
    COLOR_KEYPOINT,
    COLOR_REFERENCE,
    COLOR_WARNING,
    COLOR_WHITE,
)

# Short display labels for the three angles
_SHORT_LABELS = {
    "ear_shoulder_hip": "Head",
    "shoulder_hip_knee": "Trunk",
    "hip_knee_ankle": "Knee",
}


def _status_color(deviation: float, threshold: float):
    """Pick green / yellow / red based on severity."""
    if deviation <= threshold:
        return COLOR_GOOD
    if deviation <= threshold * 2:
        return COLOR_WARNING
    return COLOR_BAD


def _draw_dashed_vertical_line(frame, x: int, y1: int, y2: int, color) -> None:
    """Draw a lightweight plumb line reference for side-view posture."""
    dash = 10
    gap = 8
    cur = y1
    while cur < y2:
        end = min(cur + dash, y2)
        cv2.line(frame, (x, cur), (x, end), color, 1)
        cur = end + gap


def draw_analysis(frame, result: PostureResult) -> None:
    """Render the full posture-analysis overlay onto *frame* (BGR, in-place).

    Layout
    ------
    Top-left      : overall verdict + score
    Right panel   : per-angle detail with coloured bars
    Body overlay  : highlighted keypoints + alignment line
    Bottom        : corrective advice (if any)
    """
    h, w = frame.shape[:2]

    # -- no detection ------------------------------------------------
    if not result.detected:
        cv2.putText(
            frame,
            "No person detected",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            COLOR_WHITE,
            2,
        )
        return

    # -- keypoints & alignment line -----------------------------------
    if result.keypoint_coords:
        px_pts = [(int(x * w), int(y * h)) for x, y in result.keypoint_coords]

        # Plumb line: neutral side-view reference through the ankle.
        ankle_x, _ = px_pts[-1]
        top_y = max(0, min(y for _, y in px_pts) - 35)
        bottom_y = min(h - 1, max(y for _, y in px_pts) + 35)
        _draw_dashed_vertical_line(frame, ankle_x, top_y, bottom_y, COLOR_REFERENCE)
        cv2.putText(
            frame,
            "plumb line",
            (max(5, ankle_x + 8), max(18, top_y + 14)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            COLOR_REFERENCE,
            1,
        )

        # alignment line (ear → ankle)
        for i in range(len(px_pts) - 1):
            cv2.line(frame, px_pts[i], px_pts[i + 1], COLOR_ALIGNMENT, 2)

        # keypoint dots
        for pt in px_pts:
            cv2.circle(frame, pt, 6, COLOR_KEYPOINT, -1)
            cv2.circle(frame, pt, 7, COLOR_WHITE, 1)

    # -- top-left: verdict + score ------------------------------------
    verdict = "Good Posture" if result.overall_good else "Bad Posture"
    v_color = COLOR_GOOD if result.overall_good else COLOR_BAD
    cv2.putText(
        frame, verdict, (30, 40),
        cv2.FONT_HERSHEY_SIMPLEX, 1.0, v_color, 2,
    )

    s_color = (
        COLOR_GOOD if result.score >= 80
        else COLOR_WARNING if result.score >= 60
        else COLOR_BAD
    )
    cv2.putText(
        frame, f"Score: {result.score}/100", (30, 70),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, s_color, 2,
    )

    # -- right panel: angle details -----------------------------------
    panel_x = w - 280
    y_cur = 30

    cv2.putText(
        frame, f"Side: {result.side}", (panel_x, y_cur),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1,
    )

    for ar in result.angles:
        y_cur += 35
        color = _status_color(ar.deviation, ar.threshold)
        short = _SHORT_LABELS.get(ar.name, ar.name)

        # colour bar
        cv2.rectangle(
            frame,
            (panel_x - 15, y_cur - 14),
            (panel_x - 7, y_cur + 14),
            color,
            -1,
        )

        # angle value
        cv2.putText(
            frame, f"{short}: {ar.angle:.1f} deg", (panel_x, y_cur),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1,
        )

        # deviation / OK
        status = "OK" if ar.is_good else f"dev {ar.deviation:.1f} deg"
        cv2.putText(
            frame, status, (panel_x, y_cur + 16),
            cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1,
        )

    # -- bottom: advice -----------------------------------------------
    if result.advice:
        y_adv = h - 15 - (len(result.advice) - 1) * 22
        for adv in result.advice:
            cv2.putText(
                frame, f"> {adv}", (30, y_adv),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, COLOR_WARNING, 1,
            )
            y_adv += 22
