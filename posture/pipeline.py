"""Shared frame-processing helpers for CLI and web demos."""

from __future__ import annotations

from typing import Any, Dict

import cv2

from posture.analyzer import PostureResult, analyze_posture
from posture.detector import PoseDetector
from posture.visualizer import draw_analysis


def annotate_frame(
    detector: PoseDetector,
    frame,
    show_text: bool = True,
) -> PostureResult:
    """Run detection and draw the existing skeleton/analysis overlay in-place."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = detector.process(rgb)

    detector.draw_skeleton(frame, results)
    posture = analyze_posture(detector.get_landmarks(results))
    draw_analysis(frame, posture, show_text=show_text)
    return posture


def result_to_dict(result: PostureResult) -> Dict[str, Any]:
    """Convert a posture result into JSON-friendly data for the web UI."""
    keypoint_names = ["ear", "shoulder", "hip", "knee", "ankle"]
    return {
        "detected": result.detected,
        "side": result.side,
        "view": result.view,
        "view_valid": result.view_valid,
        "message": result.message,
        "score": result.score if result.view_valid and result.profile_complete else None,
        "overall_good": result.overall_good,
        "posture": (
            "No detection"
            if not result.detected
            else "Side view required"
            if not result.view_valid
            else "Incomplete profile"
            if not result.profile_complete
            else "Good"
            if result.overall_good
            else "Bad"
        ),
        "issues": list(result.issues),
        "advice": list(result.advice),
        "profile_complete": result.profile_complete,
        "missing_profile_parts": list(result.missing_profile_parts),
        "profile_parts": [
            {
                "name": part.name,
                "visible": part.visible,
                "visibility": part.visibility,
                "proxy": part.proxy,
            }
            for part in result.profile_parts
        ],
        "keypoints": [
            {"name": name, "x": round(x, 6), "y": round(y, 6)}
            for name, (x, y) in zip(keypoint_names, result.keypoint_coords)
        ],
        "angles": [
            {
                "name": angle.name,
                "label": angle.label,
                "angle": angle.angle,
                "deviation": angle.deviation,
                "threshold": angle.threshold,
                "is_good": angle.is_good,
            }
            for angle in result.angles
        ],
        "segment_angles": [
            {
                "name": angle.name,
                "label": angle.label,
                "start": angle.start,
                "end": angle.end,
                "angle": angle.angle,
                "threshold": angle.threshold,
                "is_good": angle.is_good,
            }
            for angle in result.segment_angles
        ],
    }
