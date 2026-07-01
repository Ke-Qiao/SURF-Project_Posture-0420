import unittest

from posture.yolo_pose import build_yolo_pose_json


class YoloPoseExportTests(unittest.TestCase):
    def test_build_yolo_pose_json_contains_pixel_and_normalized_labels(self):
        payload = build_yolo_pose_json(
            {
                "keypoints": [
                    {"name": "ear", "x": 0.50, "y": 0.20, "visibility": 0.98},
                    {"name": "shoulder", "x": 0.50, "y": 0.35, "visibility": 0.97},
                    {"name": "hip", "x": 0.50, "y": 0.55, "visibility": 0.96},
                    {"name": "knee", "x": 0.50, "y": 0.75, "visibility": 0.95},
                    {"name": "ankle", "x": 0.50, "y": 0.92, "visibility": 0.94},
                ],
            },
            image_width=200,
            image_height=100,
            image_filename="sample.jpg",
        )

        self.assertEqual("yolo-pose-json-v1", payload["format"])
        self.assertEqual(["ear", "shoulder", "hip", "knee", "ankle"], payload["keypoint_names"])
        self.assertEqual([5, 3], payload["keypoint_shape"])
        self.assertEqual("ok", payload["status"])
        annotation = payload["annotations"][0]
        self.assertEqual([100.0, 20.0, 2], annotation["keypoints"][0])
        self.assertEqual([0.5, 0.2, 2], annotation["keypoints_normalized"][0])
        self.assertTrue(annotation["yolo_pose_label"].startswith("0 "))
        self.assertEqual(20, len(annotation["yolo_pose_label"].split()))

    def test_missing_keypoints_returns_empty_annotation(self):
        payload = build_yolo_pose_json({}, image_width=200, image_height=100, image_filename="missing.jpg")

        self.assertEqual("no_valid_pose", payload["status"])
        self.assertEqual([], payload["annotations"])


if __name__ == "__main__":
    unittest.main()
