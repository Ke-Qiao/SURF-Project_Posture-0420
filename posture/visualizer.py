"""OpenCV drawing utilities for posture analysis results.

All overlay rendering is isolated here so that analysis logic stays
free of any display concerns.
"""

from __future__ import annotations

import cv2
import numpy as np

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


def draw_analysis(frame, result: PostureResult, show_text: bool = True) -> None:
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
        if show_text:
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

    if not result.view_valid:
        if show_text:
            cv2.putText(
                frame,
                "Side view required",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                COLOR_WARNING,
                2,
            )
        return

    if not result.profile_complete:
        if show_text:
            cv2.putText(
                frame,
                "Incomplete side profile",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                COLOR_WARNING,
                2,
            )
            if result.missing_profile_parts:
                cv2.putText(
                    frame,
                    "Missing: " + ", ".join(result.missing_profile_parts[:4]),
                    (30, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    COLOR_WARNING,
                    1,
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
        if show_text:
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

    if not show_text:
        return

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


def append_analysis_footer(frame, result: PostureResult):
    """Return a copy of *frame* with posture text moved into a bottom footer."""
    _, w = frame.shape[:2]
    footer_h = 142 if result.detected and result.view_valid else 72
    footer = np.full((footer_h, w, 3), (245, 247, 246), dtype=np.uint8)

    text = (29, 42, 37)
    muted = (107, 115, 111)
    good = COLOR_GOOD
    bad = COLOR_BAD
    warn = COLOR_WARNING

    if not result.detected:
        _put_footer_text(footer, "No person detected", (18, 30), bad, 0.58, 2)
        _put_footer_text(
            footer,
            "Use a clear side view and keep the body landmarks visible.",
            (18, 58),
            muted,
            0.46,
            1,
        )
        return np.vstack([frame, footer])

    if not result.view_valid:
        _put_footer_text(footer, "Side view required", (18, 30), bad, 0.58, 2)
        _put_footer_text(
            footer,
            result.message or "Turn sideways before running side-view posture scoring.",
            (18, 58),
            muted,
            0.46,
            1,
        )
        return np.vstack([frame, footer])

    if not result.profile_complete:
        _put_footer_text(footer, "Incomplete side profile", (18, 30), bad, 0.58, 2)
        missing = ", ".join(result.missing_profile_parts) or "required body parts"
        _put_footer_text(
            footer,
            _fit_text(f"Missing: {missing}", w, 0.46, 28),
            (18, 58),
            muted,
            0.46,
            1,
        )
        return np.vstack([frame, footer])

    verdict = "Good Posture" if result.overall_good else "Bad Posture"
    verdict_color = good if result.overall_good else bad
    _put_footer_text(footer, verdict, (18, 32), verdict_color, 0.62, 2)
    _put_footer_text(
        footer,
        f"Score {result.score}/100  |  Side {result.side}",
        (18, 60),
        text,
        0.48,
        1,
    )

    x = 18
    y = 91
    for angle in result.angles:
        color = good if angle.is_good else warn
        label = _SHORT_LABELS.get(angle.name, angle.label)
        chunk = f"{label}: {angle.angle} deg, dev {angle.deviation} deg"
        _put_footer_text(footer, chunk, (x, y), color, 0.42, 1)
        x += max(210, int(w / 3.2))
        if x > w - 220:
            break

    if result.advice:
        advice = " | ".join(result.advice[:2])
        _put_footer_text(
            footer,
            _fit_text(advice, w, 0.38, 28),
            (18, footer_h - 12),
            muted,
            0.38,
            1,
        )

    return np.vstack([frame, footer])


def _put_footer_text(canvas, text: str, origin, color, scale: float, thickness: int):
    cv2.putText(
        canvas,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def _fit_text(text: str, max_width: int, scale: float, margin: int) -> str:
    """Trim OpenCV text so it fits the footer width."""
    available = max_width - margin * 2
    if cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0][0] <= available:
        return text

    ellipsis = "..."
    trimmed = text
    while trimmed:
        candidate = trimmed.rstrip() + ellipsis
        width = cv2.getTextSize(candidate, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0][0]
        if width <= available:
            return candidate
        trimmed = trimmed[:-1]
    return ellipsis
