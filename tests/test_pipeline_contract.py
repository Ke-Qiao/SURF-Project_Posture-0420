from types import SimpleNamespace
import unittest

from posture.analyzer import analyze_posture
from posture.pipeline import result_to_dict


def _landmark(x=0.0, y=0.0, visibility=0.95):
    return SimpleNamespace(x=x, y=y, visibility=visibility)


def _blank_landmarks():
    return [_landmark(0.0, 0.0, 0.0) for _ in range(33)]


class PipelineContractTests(unittest.TestCase):
    def test_front_view_returns_side_view_required(self):
        landmarks = _blank_landmarks()
        landmarks[7] = _landmark(0.44, 0.28)
        landmarks[8] = _landmark(0.56, 0.28)
        landmarks[11] = _landmark(0.35, 0.45)
        landmarks[12] = _landmark(0.65, 0.45)
        landmarks[23] = _landmark(0.40, 0.68)
        landmarks[24] = _landmark(0.60, 0.68)

        result = analyze_posture(landmarks)
        payload = result_to_dict(result)

        self.assertTrue(result.detected)
        self.assertEqual("front", result.view)
        self.assertFalse(result.view_valid)
        self.assertEqual("Side view required", payload["posture"])
        self.assertIsNone(payload["score"])
        self.assertEqual([], payload["angles"])

    def test_side_view_keeps_angle_scoring_contract(self):
        landmarks = _blank_landmarks()
        for idx, x, y, visibility in [
            (7, 0.50, 0.26, 0.98),
            (8, 0.52, 0.26, 0.20),
            (11, 0.50, 0.44, 0.98),
            (12, 0.51, 0.44, 0.20),
            (23, 0.50, 0.66, 0.98),
            (24, 0.51, 0.66, 0.20),
            (25, 0.50, 0.84, 0.98),
            (26, 0.51, 0.84, 0.20),
            (27, 0.50, 0.98, 0.98),
            (28, 0.51, 0.98, 0.20),
        ]:
            landmarks[idx] = _landmark(x, y, visibility)

        result = analyze_posture(landmarks)
        payload = result_to_dict(result)

        self.assertTrue(result.detected)
        self.assertEqual("side", result.view)
        self.assertTrue(result.view_valid)
        self.assertEqual("left", result.side)
        self.assertEqual(3, len(payload["angles"]))
        self.assertEqual(4, len(payload["segment_angles"]))
        self.assertEqual(["E-S", "S-H", "H-K", "K-A"], [item["label"] for item in payload["segment_angles"]])
        self.assertTrue(all(item["angle"] == 0.0 for item in payload["segment_angles"]))
        self.assertEqual(["ear", "shoulder", "hip", "knee", "ankle"], [item["name"] for item in payload["keypoints"]])
        self.assertTrue(payload["profile_complete"])
        self.assertEqual([], payload["missing_profile_parts"])
        self.assertIsInstance(payload["score"], float)

    def test_segment_reference_angle_drives_bad_posture(self):
        landmarks = _blank_landmarks()
        for idx, x, y, visibility in [
            (7, 0.63, 0.26, 0.98),
            (8, 0.64, 0.26, 0.20),
            (11, 0.50, 0.44, 0.98),
            (12, 0.51, 0.44, 0.20),
            (23, 0.50, 0.66, 0.98),
            (24, 0.51, 0.66, 0.20),
            (25, 0.50, 0.84, 0.98),
            (26, 0.51, 0.84, 0.20),
            (27, 0.50, 0.98, 0.98),
            (28, 0.51, 0.98, 0.20),
        ]:
            landmarks[idx] = _landmark(x, y, visibility)

        result = analyze_posture(landmarks)
        payload = result_to_dict(result)

        self.assertEqual("Bad", payload["posture"])
        self.assertFalse(payload["overall_good"])
        es_angle = next(item for item in payload["segment_angles"] if item["name"] == "ear_shoulder")
        self.assertGreater(es_angle["angle"], es_angle["threshold"])
        self.assertLess(payload["score"], 100.0)

    def test_marginal_ear_landmark_drift_is_stabilized(self):
        landmarks = _blank_landmarks()
        for idx, x, y, visibility in [
            (7, 0.54, 0.26, 0.98),
            (8, 0.56, 0.26, 0.20),
            (11, 0.50, 0.44, 0.98),
            (12, 0.51, 0.44, 0.20),
            (23, 0.50, 0.66, 0.98),
            (24, 0.51, 0.66, 0.20),
            (25, 0.50, 0.84, 0.98),
            (26, 0.51, 0.84, 0.20),
            (27, 0.50, 0.98, 0.98),
            (28, 0.51, 0.98, 0.20),
        ]:
            landmarks[idx] = _landmark(x, y, visibility)

        payload = result_to_dict(analyze_posture(landmarks))

        es_angle = next(item for item in payload["segment_angles"] if item["name"] == "ear_shoulder")
        ear = next(item for item in payload["keypoints"] if item["name"] == "ear")
        self.assertEqual(0.0, es_angle["angle"])
        self.assertAlmostEqual(0.50, ear["x"])
        self.assertEqual("Good", payload["posture"])

    def test_segment_angle_uses_green_reference_line_not_local_segment_only(self):
        landmarks = _blank_landmarks()
        for idx, x, y, visibility in [
            (7, 0.63, 0.26, 0.98),
            (8, 0.64, 0.26, 0.20),
            (11, 0.63, 0.44, 0.98),
            (12, 0.64, 0.44, 0.20),
            (23, 0.50, 0.66, 0.98),
            (24, 0.51, 0.66, 0.20),
            (25, 0.50, 0.84, 0.98),
            (26, 0.51, 0.84, 0.20),
            (27, 0.50, 0.98, 0.98),
            (28, 0.51, 0.98, 0.20),
        ]:
            landmarks[idx] = _landmark(x, y, visibility)

        payload = result_to_dict(analyze_posture(landmarks))

        es_angle = next(item for item in payload["segment_angles"] if item["name"] == "ear_shoulder")
        self.assertGreater(es_angle["angle"], es_angle["threshold"])
        self.assertEqual("Bad", payload["posture"])

    def test_missing_required_profile_part_blocks_scoring(self):
        landmarks = _blank_landmarks()
        for idx, x, y, visibility in [
            (7, 0.51, 0.26, 0.98),
            (8, 0.52, 0.26, 0.20),
            (11, 0.50, 0.44, 0.98),
            (12, 0.51, 0.44, 0.20),
            (23, 0.50, 0.66, 0.98),
            (24, 0.51, 0.66, 0.20),
            (25, 0.50, 0.84, 0.98),
            (26, 0.51, 0.84, 0.20),
            (27, 0.50, 0.98, 0.10),
            (28, 0.51, 0.98, 0.20),
        ]:
            landmarks[idx] = _landmark(x, y, visibility)

        result = analyze_posture(landmarks)
        payload = result_to_dict(result)

        self.assertTrue(result.detected)
        self.assertEqual("side", result.view)
        self.assertFalse(payload["profile_complete"])
        self.assertEqual("Incomplete profile", payload["posture"])
        self.assertIn("Ankle", payload["missing_profile_parts"])
        self.assertEqual([], payload["angles"])
        self.assertIsNone(payload["score"])


if __name__ == "__main__":
    unittest.main()
