#https://www.kaggle.com/datasets/melsmm/posture-keypoints-detection?resource=download

#in terminal:
pip uninstall numpy -y
pip install "numpy<2"

#update matplotlib:
pip uninstall matplotlib -y
pip install matplotlib==3.7.5


#Quick test first
python -c "import numpy; print(numpy.__version__)"

#run this file not in terminal
#run in main.py
import cv2
import mediapipe as mp

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Start webcam
cap = cv2.VideoCapture(0)

while True:

    success, frame = cap.read()
    if not success:
        break

    # Convert to RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process pose
    results = pose.process(rgb)

    posture = "No detection"

    if results.pose_landmarks:

        # Draw skeleton
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        # Extract landmarks
        landmarks = results.pose_landmarks.landmark

        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]

        left_hip = landmarks[23]
        right_hip = landmarks[24]

        # Posture features
        shoulder_diff = abs(left_shoulder.y - right_shoulder.y)

        torso_slant = abs(
            (left_shoulder.x + right_shoulder.x) / 2 -
            (left_hip.x + right_hip.x) / 2
        )

        # Simple posture classification
        if shoulder_diff > 0.05:
            posture = "Bad: Uneven Shoulders"

        elif torso_slant > 0.10:
            posture = "Bad: Slouching"

        else:
            posture = "Good Posture"

        # Show values (debug)
        cv2.putText(frame, f"S:{shoulder_diff:.3f} T:{torso_slant:.3f}",
                    (30, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 2)

    # Display posture result
    cv2.putText(frame, posture,
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2)

    cv2.imshow("SURF Posture Detection", frame)

    # Exit with ESC
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()