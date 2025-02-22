import cv2
from deepface import DeepFace
from datetime import datetime
import csv
import os
import time

log_file = 'face_log.csv'
if not os.path.exists(log_file):
    with open(log_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'emotion', 'confidence'])

cap = cv2.VideoCapture(0) # initialising webcam capture
last_log_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        if isinstance(analysis, list):
            analysis = analysis[0]
        dominant_emotion = analysis.get('dominant_emotion',0)
        emotion_scores = analysis.get("emotion",{})
        confidence = emotion_scores.get(dominant_emotion, 0)
    except Exception as e:
        dominant_emotion = "Error:" + str(e)
        confidence = 0 
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Log the timestamp, emotion, and confidence to the CSV file
    with open(log_file, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, dominant_emotion, confidence])

    # Overlay the dominant emotion and its confidence on the video frame
    cv2.putText(frame, 
                f"Emotion: {dominant_emotion} ({confidence:.2f}%)",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
                cv2.LINE_AA)

    # Display the frame
    cv2.imshow("Real-time Emotion Recognition", frame)

    current_time = time.time()
    if current_time - last_log_time >= 0.5:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, dominant_emotion, confidence])
        last_log_time = current_time

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()