from types import SimpleNamespace
import unittest

from posture.batch_classifier import (
    CATEGORY_INCOMPLETE,
    CATEGORY_SITTING,
    CATEGORY_STANDING,
    classify_landmarks,
    summarize_rows,
)


def _landmark(x=0.0, y=0.0, visibility=0.95):
    return SimpleNamespace(x=x, y=y, visibility=visibility)


def _blank_landmarks():
    return [_landmark(0.0, 0.0, 0.0) for _ in range(33)]


class BatchClassifierTests(unittest.TestCase):
    def test_none_landmarks_are_incomplete(self):
        result = classify_landmarks(None)

        self.assertEqual(CATEGORY_INCOMPLETE, result.category)
        self.assertEqual(1.0, result.confidence)

    def test_extended_lower_body_is_standing(self):
        landmarks = _blank_landmarks()
        landmarks[11] = _landmark(0.48, 0.30)
        landmarks[12] = _landmark(0.52, 0.30)
        landmarks[23] = _landmark(0.50, 0.52)
        landmarks[24] = _landmark(0.52, 0.52)
        landmarks[25] = _landmark(0.50, 0.74)
        landmarks[26] = _landmark(0.52, 0.74)
        landmarks[27] = _landmark(0.50, 0.94)
        landmarks[28] = _landmark(0.52, 0.94)

        result = classify_landmarks(landmarks)

        self.assertEqual(CATEGORY_STANDING, result.category)
        self.assertGreaterEqual(result.confidence, 0.6)

    def test_bent_lower_body_is_sitting(self):
        landmarks = _blank_landmarks()
        landmarks[11] = _landmark(0.48, 0.30)
        landmarks[12] = _landmark(0.52, 0.30)
        landmarks[23] = _landmark(0.50, 0.55)
        landmarks[24] = _landmark(0.52, 0.55)
        landmarks[25] = _landmark(0.70, 0.58)
        landmarks[26] = _landmark(0.72, 0.58)
        landmarks[27] = _landmark(0.70, 0.82)
        landmarks[28] = _landmark(0.72, 0.82)

        result = classify_landmarks(landmarks)

        self.assertEqual(CATEGORY_SITTING, result.category)
        self.assertIn("sitting", result.reason)

    def test_summary_counts_rows(self):
        summary = summarize_rows(
            [
                {"category": CATEGORY_STANDING, "media_type": "image"},
                {"category": CATEGORY_SITTING, "media_type": "image"},
                {"category": CATEGORY_INCOMPLETE, "media_type": "video"},
            ]
        )

        self.assertEqual(3, summary["total"])
        self.assertEqual(1, summary["counts"][CATEGORY_STANDING])
        self.assertEqual(2, summary["media_counts"]["image"])


if __name__ == "__main__":
    unittest.main()
