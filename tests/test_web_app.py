import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from web import app as web_app


class WebAppContractTests(unittest.TestCase):
    def setUp(self):
        self.client = web_app.app.test_client()

    def tearDown(self):
        web_app._VIDEO_UPLOADS.clear()

    def test_health_exposes_week_1_polish_version(self):
        response = self.client.get("/health")

        self.assertEqual(200, response.status_code)
        self.assertEqual("surf-posture-web", response.json["app"])
        self.assertEqual("week-01-demo-polish-v1", response.json["version"])

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


if __name__ == "__main__":
    unittest.main()
