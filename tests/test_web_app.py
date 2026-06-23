import io
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from web import app as web_app


class WebAppContractTests(unittest.TestCase):
    def setUp(self):
        self.client = web_app.app.test_client()

    def tearDown(self):
        web_app._VIDEO_UPLOADS.clear()
        web_app._BATCH_EXPORTS.clear()
        web_app._WEBCAM_LATEST.clear()
        web_app._WEBCAM_CAPTURES.clear()
        web_app._WEBCAM_CAPTURE_ZIPS.clear()
        web_app._WEBCAM_CAPTURE_TOKEN = ""

    def capture_payload(self):
        return {
            "collector": "fengshuo",
            "subject_id": "subject_001",
            "label": "good",
            "notes": "unit test",
            "reference": {
                "points": {
                    "ear": {"x": 0.4, "y": 0.2},
                    "shoulder": {"x": 0.42, "y": 0.35},
                    "hip": {"x": 0.43, "y": 0.55},
                    "knee": {"x": 0.44, "y": 0.75},
                    "ankle": {"x": 0.45, "y": 0.92},
                },
                "angles": {
                    "ear_shoulder_hip": 175.0,
                    "shoulder_hip_knee": 178.0,
                    "hip_knee_ankle": 176.0,
                },
                "source": "unit-test",
                "updated_at": "2026-06-23T00:00:00Z",
            },
        }

    def test_health_exposes_week_2_profile_gate_version(self):
        response = self.client.get("/health")

        self.assertEqual(200, response.status_code)
        self.assertEqual("surf-posture-web", response.json["app"])
        self.assertEqual("week-02-profile-gate-v1", response.json["version"])

    def test_load_video_returns_json_stream_url(self):
        response = self.client.post(
            "/api/load-video",
            data={"file": (io.BytesIO(b"fake video bytes"), "demo.mp4")},
            content_type="multipart/form-data",
        )

        self.assertEqual(200, response.status_code)
        self.assertIn("token", response.json)
        self.assertIn("/stream/video/", response.json["stream_url"])
        self.assertIn("/stream/video-json/", response.json["json_stream_url"])

    def test_video_json_missing_token_returns_ndjson_error(self):
        response = self.client.get("/stream/video-json/missing-token")

        self.assertEqual(404, response.status_code)
        self.assertEqual("application/x-ndjson", response.mimetype)
        self.assertIn(b"Video file not found.", response.data)

    def test_video_json_endpoint_uses_json_frame_stream(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            token = "unit-video"
            web_app._VIDEO_UPLOADS[token] = Path(tmp.name)
            with patch.object(web_app, "_json_frame_stream", return_value=iter(['{"ok":true}\n'])):
                response = self.client.get(f"/stream/video-json/{token}")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/x-ndjson", response.mimetype)
        self.assertEqual(b'{"ok":true}\n', response.data)

    def test_batch_analyze_requires_source_or_files(self):
        response = self.client.post("/api/batch-analyze", data={})

        self.assertEqual(400, response.status_code)
        self.assertIn("Choose uploaded files", response.json["error"])

    def test_batch_analyze_rejects_unknown_teacher_source(self):
        response = self.client.post("/api/batch-analyze", data={"teacher_source": "unknown"})

        self.assertEqual(400, response.status_code)
        self.assertIn("Unsupported teacher source", response.json["error"])

    def test_batch_analyze_accepts_uploaded_files(self):
        payload = {
            "token": "unit-batch",
            "summary": {"total": 1, "counts": {"standing": 1, "sitting": 0, "incomplete": 0}},
            "rows": [],
            "row_count": 1,
            "download_url": "/api/batch-download/unit-batch",
        }
        with patch.object(web_app, "_create_batch_export", return_value=payload):
            response = self.client.post(
                "/api/batch-analyze",
                data={"files": (io.BytesIO(b"fake image bytes"), "demo.jpg")},
                content_type="multipart/form-data",
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual("/api/batch-download/unit-batch", response.json["download_url"])

    def test_batch_download_missing_token_returns_404(self):
        response = self.client.get("/api/batch-download/missing")

        self.assertEqual(404, response.status_code)
        self.assertIn("Batch export not found", response.json["error"])

    def test_webcam_capture_requires_latest_frame(self):
        response = self.client.post("/api/webcam-capture", json=self.capture_payload())

        self.assertEqual(409, response.status_code)
        self.assertIn("No webcam frame", response.json["error"])

    def test_webcam_capture_rejects_missing_metadata(self):
        response = self.client.post("/api/webcam-capture", json={})

        self.assertEqual(400, response.status_code)
        self.assertIn("collector", response.json["error"])

    def test_webcam_capture_rejects_missing_reference(self):
        payload = self.capture_payload()
        payload["reference"] = {}

        response = self.client.post("/api/webcam-capture", json=payload)

        self.assertEqual(400, response.status_code)
        self.assertIn("reference skeleton", response.json["error"])

    def test_webcam_capture_rejects_incomplete_profile(self):
        web_app._WEBCAM_LATEST.update(
            {
                "original_jpeg": b"original",
                "annotated_jpeg": b"annotated",
                "result": {
                    "posture": "Incomplete profile",
                    "score": None,
                    "side": "left",
                    "view": "side",
                    "view_valid": True,
                    "profile_complete": False,
                    "missing_profile_parts": ["Ankle"],
                    "angles": [],
                },
                "stored_at": time.time(),
            }
        )

        response = self.client.post("/api/webcam-capture", json=self.capture_payload())

        self.assertEqual(409, response.status_code)
        self.assertIn("Ankle", response.json["error"])

    def test_webcam_capture_reaches_zip_download(self):
        web_app._WEBCAM_LATEST.update(
            {
                "original_jpeg": b"original",
                "annotated_jpeg": b"annotated",
                "result": {
                    "posture": "Good",
                    "score": 100.0,
                    "side": "left",
                    "view": "side",
                    "view_valid": True,
                    "profile_complete": True,
                    "missing_profile_parts": [],
                    "angles": [
                        {"name": "ear_shoulder_hip", "angle": 175.5},
                        {"name": "shoulder_hip_knee", "angle": 178.0},
                        {"name": "hip_knee_ankle", "angle": 176.0},
                    ],
                },
                "stored_at": time.time(),
            }
        )

        payload = None
        for _ in range(web_app.WEBCAM_CAPTURE_TARGET):
            response = self.client.post("/api/webcam-capture", json=self.capture_payload())
            self.assertEqual(200, response.status_code)
            payload = response.json

        self.assertIsNotNone(payload)
        self.assertTrue(payload["ready"])
        self.assertEqual(web_app.WEBCAM_CAPTURE_TARGET, payload["count"])
        self.assertIn("/api/webcam-captures-download/", payload["download_url"])

        download = self.client.get(payload["download_url"])
        self.assertEqual(200, download.status_code)
        with zipfile.ZipFile(io.BytesIO(download.data)) as exported:
            names = set(exported.namelist())
            self.assertIn("original/01-original.jpg", names)
            self.assertIn("mediapipe/01-mediapipe.jpg", names)
            self.assertIn("manifest.csv", names)
            self.assertIn("reference.json", names)
            self.assertIn("summary.md", names)
            self.assertEqual(b"original", exported.read("original/01-original.jpg"))
            self.assertEqual(b"annotated", exported.read("mediapipe/01-mediapipe.jpg"))
            manifest = exported.read("manifest.csv").decode("utf-8")
            self.assertIn("collector,subject_id,true_label", manifest)
            self.assertIn("fengshuo,subject_001,good", manifest)
            reference_json = exported.read("reference.json").decode("utf-8")
            self.assertIn('"source": "unit-test"', reference_json)
        download.close()

    def test_webcam_capture_rejects_stale_cached_frame(self):
        web_app._WEBCAM_LATEST.update(
            {
                "original_jpeg": b"original",
                "annotated_jpeg": b"annotated",
                "result": {},
                "stored_at": time.time() - web_app.WEBCAM_LATEST_MAX_AGE_SECONDS - 1,
            }
        )

        response = self.client.post("/api/webcam-capture", json=self.capture_payload())

        self.assertEqual(409, response.status_code)
        self.assertIn("stale", response.json["error"])

    def test_webcam_capture_download_missing_token_returns_404(self):
        response = self.client.get("/api/webcam-captures-download/missing")

        self.assertEqual(404, response.status_code)
        self.assertIn("Webcam capture export not found", response.json["error"])

    def test_webcam_capture_reset_clears_count(self):
        web_app._WEBCAM_CAPTURES.append({"index": 1})

        response = self.client.post("/api/webcam-captures-reset")

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.json["count"])
        self.assertEqual([], web_app._WEBCAM_CAPTURES)


if __name__ == "__main__":
    unittest.main()
