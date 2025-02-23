import cv2
import os
import csv
import whisper
import pyaudio
import wave
import threading
import time
from deepface import DeepFace
from open_api import getPointer

# Load OpenCV face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Load Whisper model (small for better speed)
whisper_model = whisper.load_model("tiny")

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Whisper works best with 16kHz
CHUNK = 1024

# Current working directory
CWD = os.getcwd()

# Conversation data filepath
CONVO_FILEPATH = os.path.join(CWD,"convo_data.csv")

# Write header to conversation data file
with open(CONVO_FILEPATH, "w", newline="\n") as csv_file:
    fieldnames = ["time", "transcription", "emotion", "confidence"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Toggle variables
face_detection_enabled = True  # Start with face detection enabled
transcription_enabled = True   # Start with transcription enabled
transcription_text = ""  # Store last transcribed text
stop_transcription = False  # Control flag for transcription

# Function to continuously transcribe audio
def transcribe_audio():
    global transcription_text, stop_transcription

    while True:
        if not transcription_enabled:
            stop_transcription = True
            continue  # Skip recording if transcription is disabled

        stop_transcription = False
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        frames = []

        while transcription_enabled:  # Keep recording if transcription is on
            data = stream.read(CHUNK)
            frames.append(data)

            # Stop recording if transcription is turned off
            if stop_transcription:
                break

        stream.stop_stream()
        stream.close()

        # Skip transcription if it was stopped
        if stop_transcription:
            continue

        # Save recorded audio to a temporary file
        wf = wave.open("temp.wav", "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # Transcribe with Whisper
        result = whisper_model.transcribe("temp.wav")
        transcription_text = result["text"]
        print(f"Transcription: {transcription_text}")

        with open(CONVO_FILEPATH, "a", newline="\n") as csv_file:
            fieldnames = ["time", "transcription", "emotion", "confidence"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writerow({"time": time.time(), "transcription": transcription_text, "emotion": dominant_emotion, "confidence": confidence})

            pointer = getPointer()
            print(pointer.choices[0].message.content)


# Start transcription thread
transcription_thread = threading.Thread(target=transcribe_audio, daemon=True)
transcription_thread.start()

# Open webcam
video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not video.isOpened():
    raise IOError("Cannot open webcam")

while video.isOpened():
    _, frame = video.read()

    if face_detection_enabled:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in faces:
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Crop and convert face to RGB
            face_roi = frame[y:y+h, x:x+w]
            face_roi_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)

            try:
                # Analyze emotions
                analyse = DeepFace.analyze(face_roi_rgb, actions=['emotion'], enforce_detection=False)

                # Get dominant emotion
                dominant_emotion = analyse[0]['dominant_emotion']
                confidence = analyse[0]['face_confidence']

                # Display text on frame
                cv2.putText(frame, dominant_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            except Exception as e:
                print("DeepFace Error:", str(e))

    # Display real-time transcription on screen
    cv2.putText(frame, "Transcription:", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, transcription_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Show frame
    cv2.imshow("Emotion Detection & Speech Transcription", frame)

    # Key press detection
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Quit on "q"
        break
    elif key == ord('d'):  # Toggle face detection and transcription on "d"
        face_detection_enabled = not face_detection_enabled
        transcription_enabled = not transcription_enabled
        print(f"Face Detection: {'Enabled' if face_detection_enabled else 'Disabled'}")
        print(f"Transcription: {'Enabled' if transcription_enabled else 'Disabled'}")
            
# Cleanup
video.release()
cv2.destroyAllWindows()
audio.terminate()

