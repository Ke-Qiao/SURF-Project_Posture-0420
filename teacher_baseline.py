"""Teacher-provided SURF posture detection baseline.

This file preserves the original webcam-first baseline logic from the teacher's
reference material. It only wraps the snippet in ``main()`` so it can be run as
a normal script:

    .venv/bin/python teacher_baseline.py

Press ESC to exit the camera window.
"""

from __future__ import annotations

import cv2
import mediapipe as mp


def main() -> None:
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        posture = "No detection"

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
            )

            landmarks = results.pose_landmarks.landmark

            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_hip = landmarks[23]
            right_hip = landmarks[24]

            shoulder_diff = abs(left_shoulder.y - right_shoulder.y)

            torso_slant = abs(
                (left_shoulder.x + right_shoulder.x) / 2
                - (left_hip.x + right_hip.x) / 2
            )

            if shoulder_diff > 0.05:
                posture = "Bad: Uneven Shoulders"
            elif torso_slant > 0.10:
                posture = "Bad: Slouching"
            else:
                posture = "Good Posture"

            cv2.putText(
                frame,
                f"S:{shoulder_diff:.3f} T:{torso_slant:.3f}",
                (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

        cv2.putText(
            frame,
            posture,
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.imshow("SURF Posture Detection", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    pose.close()


if __name__ == "__main__":
    main()
