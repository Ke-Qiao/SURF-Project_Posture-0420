"""MediaPipe Pose detector wrapper.

Thin layer around ``mp.solutions.pose`` so that the rest of the codebase
never imports MediaPipe directly.
"""

import cv2
import mediapipe as mp

from posture.config import POSE_CONFIG


class PoseDetector:
    """Initialise MediaPipe Pose and expose helpers for detection & drawing."""

    def __init__(self, static_image_mode: bool = False):
        self._mp_pose = mp.solutions.pose
        self._mp_drawing = mp.solutions.drawing_utils

        self._pose = self._mp_pose.Pose(
            static_image_mode=static_image_mode,
            **POSE_CONFIG,
        )

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def process(self, rgb_frame):
        """Run pose detection on an RGB frame.

        Returns the raw MediaPipe results object.
        """
        return self._pose.process(rgb_frame)

    def get_landmarks(self, results):
        """Return the landmark list, or ``None`` if no pose detected."""
        if results and results.pose_landmarks:
            return results.pose_landmarks.landmark
        return None

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def draw_skeleton(self, bgr_frame, results):
        """Draw the full 33-point MediaPipe skeleton onto *bgr_frame*."""
        if results and results.pose_landmarks:
            self._mp_drawing.draw_landmarks(
                bgr_frame,
                results.pose_landmarks,
                self._mp_pose.POSE_CONNECTIONS,
            )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self):
        """Release MediaPipe resources."""
        self._pose.close()
