import sys
import cv2
import os
import csv
import whisper
import pyaudio
import wave
import threading
import time
import numpy as np
from deepface import DeepFace
from open_api import getPointer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QTextEdit, QListWidget, 
    QLabel, QLineEdit, QFrame
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt

# Current working directory
CWD = os.getcwd()

# Conversation data filepath
CONVO_FILEPATH = os.path.join(CWD, "convo_data.csv")

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Whisper works best with 16kHz
CHUNK = 1024

class AVPointerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # Initialize AVPointer components
        self.face_detection_enabled = False
        self.transcription_enabled = False
        self.transcription_text = ""
        self.dominant_emotion = ""
        self.confidence = 0.0
        
        self.whisper_model = whisper.load_model("tiny")
        self.audio = pyaudio.PyAudio()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        
        self.transcription_thread = threading.Thread(target=self.transcribe_audio, daemon=True)
        self.transcription_thread.start()
        
        # Start video feed
        self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30 ms
    
    def initUI(self):

        self.setWindowTitle("Lighthouse Chatbot")
        self.setGeometry(100, 100, 900, 600)
        
        # Main Container
        main_widget = QHBoxLayout()
        self.setLayout(main_widget)

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setContentsMargins(10, 10, 10, 10)

        # Logo
        logo_label = QLabel(self)
        pixmap = QPixmap("lighthouse_logo.png")  # Replace with actual logo path
        logo_label.setPixmap(pixmap)
        logo_label.setScaledContents(True)
        logo_label.setFixedSize(100, 100)

        # Sidebar Buttons
        home_button = QPushButton("🏠 Home")
        
        #home_button.setStyleSheet("background-color : ##3A5A6F;") 
        history_button = QPushButton("History")
        stats_button = QPushButton("ℹ️ Personal Stats")
        settings_button = QPushButton("⚙️ Settings")

        # Styling buttons
        for button in [home_button, history_button, stats_button, settings_button]:
            button.setFixedHeight(40)

        # Adding widgets to sidebar
        sidebar.addWidget(logo_label, alignment=Qt.AlignCenter)
        sidebar.addWidget(home_button)
        sidebar.addWidget(history_button)
        sidebar.addWidget(stats_button)
        sidebar.addWidget(settings_button)
        sidebar.addStretch()

        # Vertical separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        # Chat Section Layout
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(10, 10, 10, 10)

        # Title Bar
        title_label = QLabel("Chatbot with Webcam")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background-color: #F0F0F0; border-bottom: 2px solid #CCC;")
        title_label.setAlignment(Qt.AlignLeft)

        chat_layout.addWidget(title_label)

        # Video Feed
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet("background-color: black;")
        chat_layout.addWidget(self.video_label)

        # Chat Display Area (QTextEdit)
        self.chatbox = QTextEdit()
        self.chatbox.setReadOnly(True)
        chat_layout.addWidget(self.chatbox)

        # Input Bar
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("I'm speaking to...")
        get_pointer_button = QPushButton("Get Pointer")
        get_pointer_button.setFixedHeight(30)
        get_pointer_button.clicked.connect(self.button_clicked)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(get_pointer_button)

        chat_layout.addLayout(input_layout)

        # Add layouts to main layout
        main_widget.addLayout(sidebar, 1)
        main_widget.addWidget(separator)
        main_widget.addLayout(chat_layout, 3)
    
    def button_clicked(self):
        print("Button Clicked")
        self.face_detection_enabled = not self.face_detection_enabled
        self.transcription_enabled = not self.transcription_enabled

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
                self.chatbox.append(pointer.choices[0].message.content)
    
    def update_frame(self):
        ret, frame = self.video.read()
        if ret:
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if self.face_detection_enabled:
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    face_roi = frame[y:y+h, x:x+w]
                    face_roi_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                    
                    try:
                        analyse = DeepFace.analyze(face_roi_rgb, actions=['emotion'], enforce_detection=False)
                        self.dominant_emotion = analyse[0]['dominant_emotion']
                        self.confidence = analyse[0]['face_confidence']
                        cv2.putText(frame, self.dominant_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    except Exception as e:
                        print("DeepFace Error:", str(e))
            
            cv2.putText(frame, "Transcription:", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, self.transcription_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qimg))
    
    def closeEvent(self, event):
        self.video.release()
        self.transcription_enabled = False
        cv2.destroyAllWindows()
        event.accept()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AVPointerApp()
    window.show()
    sys.exit(app.exec_())