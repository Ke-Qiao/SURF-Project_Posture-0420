"""YOLO-pose JSON export helpers for the five-point posture dataset."""

from __future__ import annotations

from typing import Any


KEYPOINT_NAMES = ("ear", "shoulder", "hip", "knee", "ankle")
KEYPOINT_SHAPE = [len(KEYPOINT_NAMES), 3]
DEFAULT_CLASS_ID = 0
DEFAULT_CLASS_NAME = "person"
VISIBILITY_THRESHOLD = 0.45


def build_yolo_pose_json(
    result_payload: dict[str, Any],
    image_width: int,
    image_height: int,
    image_filename: str,
    class_id: int = DEFAULT_CLASS_ID,
    class_name: str = DEFAULT_CLASS_NAME,
) -> dict[str, Any]:
    """Return a YOLO-pose-compatible JSON payload with pixel coordinates.

    YOLO pose labels are normally stored as normalized text lines. This project
    stores JSON so the same file can preserve pixel coordinates, normalized
    coordinates, keypoint names, and the generated YOLO label line.
    """
    width = int(image_width or 0)
    height = int(image_height or 0)
    payload = {
        "format": "yolo-pose-json-v1",
        "image": {
            "file_name": image_filename,
            "width": width,
            "height": height,
        },
        "classes": [{"id": class_id, "name": class_name}],
        "keypoint_names": list(KEYPOINT_NAMES),
        "keypoint_shape": KEYPOINT_SHAPE,
        "annotations": [],
    }

    keypoints = _keypoints_by_name(result_payload)
    if width <= 0 or height <= 0 or not _has_all_keypoints(keypoints):
        payload["status"] = "no_valid_pose"
        return payload

    pixel_keypoints = [
        _pixel_keypoint(keypoints[name], width, height)
        for name in KEYPOINT_NAMES
    ]
    normalized_keypoints = [
        [round(point[0] / width, 6), round(point[1] / height, 6), point[2]]
        for point in pixel_keypoints
    ]
    bbox_xyxy = _bbox_xyxy(pixel_keypoints, width, height)
    bbox_xywh = _xyxy_to_xywh(bbox_xyxy)
    bbox_xywhn = [
        round(bbox_xywh[0] / width, 6),
        round(bbox_xywh[1] / height, 6),
        round(bbox_xywh[2] / width, 6),
        round(bbox_xywh[3] / height, 6),
    ]

    yolo_values = [str(class_id), *[f"{value:.6f}" for value in bbox_xywhn]]
    for x_norm, y_norm, visibility in normalized_keypoints:
        yolo_values.extend([f"{x_norm:.6f}", f"{y_norm:.6f}", str(visibility)])

    payload["status"] = "ok"
    payload["annotations"].append(
        {
            "class_id": class_id,
            "class_name": class_name,
            "bbox_xyxy": bbox_xyxy,
            "bbox_xywh": bbox_xywh,
            "bbox_xywhn": bbox_xywhn,
            "keypoints": pixel_keypoints,
            "keypoints_normalized": normalized_keypoints,
            "yolo_pose_label": " ".join(yolo_values),
        }
    )
    return payload


def _keypoints_by_name(result_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    points = {}
    for point in result_payload.get("keypoints", []) or []:
        if isinstance(point, dict) and point.get("name") in KEYPOINT_NAMES:
            points[point["name"]] = point
    return points


def _has_all_keypoints(points: dict[str, dict[str, Any]]) -> bool:
    return all(
        name in points
        and _is_number(points[name].get("x"))
        and _is_number(points[name].get("y"))
        for name in KEYPOINT_NAMES
    )


def _pixel_keypoint(point: dict[str, Any], width: int, height: int) -> list[float | int]:
    x_px = round(_clamp(float(point["x"]), 0.0, 1.0) * width, 2)
    y_px = round(_clamp(float(point["y"]), 0.0, 1.0) * height, 2)
    confidence = point.get("visibility", point.get("confidence", 1.0))
    visibility = 2 if _safe_float(confidence, 1.0) >= VISIBILITY_THRESHOLD else 1
    return [x_px, y_px, visibility]


def _bbox_xyxy(pixel_keypoints: list[list[float | int]], width: int, height: int) -> list[float]:
    x_values = [float(point[0]) for point in pixel_keypoints]
    y_values = [float(point[1]) for point in pixel_keypoints]
    padding = max(width, height) * 0.02
    x1 = round(_clamp(min(x_values) - padding, 0.0, float(width)), 2)
    y1 = round(_clamp(min(y_values) - padding, 0.0, float(height)), 2)
    x2 = round(_clamp(max(x_values) + padding, 0.0, float(width)), 2)
    y2 = round(_clamp(max(y_values) + padding, 0.0, float(height)), 2)
    return [x1, y1, x2, y2]


def _xyxy_to_xywh(bbox: list[float]) -> list[float]:
    x1, y1, x2, y2 = bbox
    return [
        round((x1 + x2) / 2, 2),
        round((y1 + y2) / 2, 2),
        round(x2 - x1, 2),
        round(y2 - y1, 2),
    ]


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_number(value: Any) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))
