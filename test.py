import cv2
from deepface import DeepFace
import time
import threading
import pyaudio
import wave
import csv
from datetime import datetime

# ===== Audio Recording Parameters =====
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024

# Global variables for audio recording and emotion logging
audio_thread = None
audio_stop_event = None
is_recording = False
audio_counter = 1  # Used to name audio and CSV files uniquely
emotion_log_file = None
emotion_csv_writer = None
last_emotion_log_time = 0

def record_audio(stop_event, filename):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []
    print(f"Audio recording started: {filename}")
    while not stop_event.is_set():
        try:
            data = stream.read(CHUNK)
        except Exception as e:
            print("Error reading audio stream:", e)
            break
        frames.append(data)
    print("Audio recording stopped.")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # Save the recorded audio to a file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

# ===== Video Capture & Emotion Analysis =====
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Perform video emotion analysis
    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        if isinstance(analysis, list):
            analysis = analysis[0]
        dominant_emotion = analysis.get("dominant_emotion", "No face detected")
        emotion_scores = analysis.get("emotion", {})
        confidence = emotion_scores.get(dominant_emotion, 0)
        
        # Draw bounding box if available
        region = analysis.get("region", {})
        if region:
            x, y, w, h = region.get("x", 0), region.get("y", 0), region.get("w", 0), region.get("h", 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    except Exception as e:
        dominant_emotion = f"Error: {str(e)}"
        confidence = 0

    # Overlay emotion on the frame
    cv2.putText(frame, 
                f"Emotion: {dominant_emotion} ({confidence:.2f}%)",
                (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv2.imshow("Video Emotion Analysis", frame)

    # If currently recording, log the emotion every 0.5 seconds
    current_time = time.time()
    if is_recording and (current_time - last_emotion_log_time >= 0.5):
        if emotion_csv_writer is not None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            emotion_csv_writer.writerow([timestamp, dominant_emotion, confidence])
        last_emotion_log_time = current_time

    # Check for key presses:
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        # Start audio recording and emotion logging if not already recording
        if not is_recording:
            is_recording = True
            audio_stop_event = threading.Event()
            audio_filename = f"recorded_audio_{audio_counter}.wav"
            emotion_log_filename = f"emotion_log_session_{audio_counter}.csv"
            audio_counter += 1
            
            # Start the audio recording thread
            audio_thread = threading.Thread(target=record_audio, args=(audio_stop_event, audio_filename))
            audio_thread.start()
            
            # Open the emotion log file for this session
            emotion_log_file = open(emotion_log_filename, 'w', newline='')
            emotion_csv_writer = csv.writer(emotion_log_file)
            emotion_csv_writer.writerow(["timestamp", "emotion", "confidence"])
            last_emotion_log_time = current_time  # Reset the logging timer

    elif key == ord('t'):
        # Stop audio recording and close emotion log file if recording is active
        if is_recording:
            audio_stop_event.set()
            audio_thread.join()
            is_recording = False
            if emotion_log_file:
                emotion_log_file.close()
                emotion_log_file = None
                emotion_csv_writer = None

cap.release()
cv2.destroyAllWindows()

# If still recording upon exit, ensure the audio thread is stopped and file closed.
if is_recording:
    audio_stop_event.set()
    audio_thread.join()
    if emotion_log_file:
        emotion_log_file.close()
