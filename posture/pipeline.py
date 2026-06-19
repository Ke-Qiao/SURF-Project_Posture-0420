"""Shared frame-processing helpers for CLI and web demos."""

from __future__ import annotations

from typing import Any, Dict

import cv2

from posture.analyzer import PostureResult, analyze_posture
from posture.detector import PoseDetector
from posture.visualizer import draw_analysis


def annotate_frame(detector: PoseDetector, frame) -> PostureResult:
    """Run detection and draw the existing skeleton/analysis overlay in-place."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = detector.process(rgb)

    detector.draw_skeleton(frame, results)
    posture = analyze_posture(detector.get_landmarks(results))
    draw_analysis(frame, posture)
    return posture


def result_to_dict(result: PostureResult) -> Dict[str, Any]:
    """Convert a posture result into JSON-friendly data for the web UI."""
    return {
        "detected": result.detected,
        "side": result.side,
        "score": result.score,
        "overall_good": result.overall_good,
        "posture": (
            "No detection"
            if not result.detected
            else "Good"
            if result.overall_good
            else "Bad"
        ),
        "issues": list(result.issues),
        "advice": list(result.advice),
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
    }
