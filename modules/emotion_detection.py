import cv2
import os
import csv
import whisper
import pyaudio
import wave
import threading
import time
from deepface import DeepFace
from modules.open_api import getPointer

# Current working directory
CWD = os.getcwd()

# Conversation data filepath
CONVO_FILEPATH = os.path.join(CWD,"convo_data.csv")

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Whisper works best with 16kHz
CHUNK = 1024

# Class to create AVPointer - Audio-Visual Pointer for Conversations
class AVPointerCreator():
    # Toggle variables
    def __init__(self):
        self.face_detection_enabled = False  # Start with face detection enabled
        self.transcription_enabled = False   # Start with transcription enabled
        self.transcription_text = ""  # Store last transcribed text
        self.stop_transcription = False  # Control flag for transcription
        self.dominant_emotion = ""  # Store last dominant emotion
        self.confidence = 0.0  # Store last emotion confidence

        # Write header to conversation data file
        with open(CONVO_FILEPATH, "w", newline="\n") as csv_file:
            fieldnames = ["time", "transcription", "emotion", "confidence"]
            self.writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            self.writer.writeheader()

        # Load Whisper model (tiny for better speed)
        self.whisper_model = whisper.load_model("tiny")

        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()

        # Load OpenCV face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    # Function to continuously transcribe audio
    def transcribe_audio(self):
        while True:
            if not self.transcription_enabled:
                stop_transcription = True
                continue  # Skip recording if transcription is disabled

            stop_transcription = False
            stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                                frames_per_buffer=CHUNK)
            frames = []

            while self.transcription_enabled:  # Keep recording if transcription is on
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
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            # Transcribe with Whisper
            result = self.whisper_model.transcribe("temp.wav")
            self.transcription_text = result["text"]
            print(f"Transcription: {self.transcription_text}")

            with open(CONVO_FILEPATH, "a", newline="\n") as csv_file:
                fieldnames = ["time", "transcription", "emotion", "confidence"]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writerow({"time": time.time(), "transcription": self.transcription_text, "emotion": self.dominant_emotion, "confidence": self.confidence})

                pointer = getPointer()
                print(pointer.choices[0].message.content)

    def start_transcribe_thread(self):
        # Start transcription thread
        transcription_thread = threading.Thread(target=self.transcribe_audio, daemon=True)
        transcription_thread.start()

    def start_video_thread(self):
        # Open webcam
        video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not video.isOpened():
            raise IOError("Cannot open webcam")

        while video.isOpened():
            _, frame = video.read()

            if self.face_detection_enabled:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

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
                        self.dominant_emotion = analyse[0]['dominant_emotion']
                        self.confidence = analyse[0]['face_confidence']

                        # Display text on frame
                        cv2.putText(frame, self.dominant_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    except Exception as e:
                        print("DeepFace Error:", str(e))

            # Display real-time transcription on screen
            cv2.putText(frame, "Transcription:", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, self.transcription_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Show frame
            cv2.imshow("Emotion Detection & Speech Transcription", frame)

            # Key press detection
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Quit on "q"
                break
            elif key == ord('d'):  # Toggle face detection and transcription on "d"
                self.face_detection_enabled = not self.face_detection_enabled
                self.transcription_enabled = not self.transcription_enabled
                print(f"Face Detection: {'Enabled' if self.face_detection_enabled else 'Disabled'}")
                print(f"Transcription: {'Enabled' if self.transcription_enabled else 'Disabled'}")
                    
        # Cleanup
        video.release()
        cv2.destroyAllWindows()
        self.audio.terminate()

    def start(self):
        self.start_transcribe_thread()
        self.start_video_thread()
