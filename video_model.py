import cv2
from deepface import DeepFace
from datetime import datetime
import csv
import os
import time


log_file = "face_log.csv"

if not os.path.exists(log_file):
    with open(log_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "emotion", "confidence"])

# Initialize webcam capture
cap = cv2.VideoCapture(0)


last_log_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    log_this_frame = False  # Flag to check if logging should occur

    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        if isinstance(analysis, list):
            analysis = analysis[0]
        
        # Get dominant emotion and its confidence score
        dominant_emotion = analysis.get("dominant_emotion", "No face detected")
        emotion_scores = analysis.get("emotion", {})
        confidence = emotion_scores.get(dominant_emotion, 0)
        
        log_this_frame = True
        region = analysis.get("region", {})
        if region:
            x, y, w, h = region.get("x", 0), region.get("y", 0), region.get("w", 0), region.get("h", 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    except Exception as e:
        dominant_emotion = f"Error: {str(e)}"
        confidence = 0

    cv2.putText(frame, 
                f"Emotion: {dominant_emotion} ({confidence:.2f}%)",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
                cv2.LINE_AA)

    cv2.imshow("Real-time Emotion Recognition", frame)

    # Log the result every half second only if there's no error.
    current_time = time.time()
    if current_time - last_log_time >= 0.5:
        if log_this_frame:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, dominant_emotion, confidence])
        last_log_time = current_time

    # Press 'q' to exit the loop.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
