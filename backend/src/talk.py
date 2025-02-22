import cv2
import whisper
import numpy as np
import wave
import pyaudio
import threading
import csv
from deepface import DeepFace
from datetime import datetime
import os
import time

class AudioToText():
    def __init__(self, audio_location, model_size):
        self.model_size = model_size
        self.audio_location = audio_location

        self.model = whisper.load_model(model_size)

    """
    Gets the language of the audio_location
    """
    def get_language(self, audio_location):
        audio = whisper.load_audio(audio_location)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio, n_mels=self.model.dims.n_mels).to(self.model.device)
        _, probs = self.model.detect_language(mel)
        return max(probs, key=probs.get) # en, ru

    """
    Takes self.model and transcribes the audio based on self.audio_location
    """
    def transcribe(self):
        result = self.model.transcribe(self.audio_location)
        return result["text"]

class VideoStreamer():
    def __init__(self, video_path, audio_path, log_path, default_camera=0):
        self.video_path = video_path
        self.audio_path = audio_path
        self.cap = cv2.VideoCapture(default_camera)
        self.recording = False
        self.stream = None
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.audio_stream = None
        self.wave_file = None
        self.audio_frames = []

        self.audio_stop_event = None
        self.audio_thread = None

        # Verify audio device parameters
        device_info = self.audio.get_default_input_device_info()
        self.format = pyaudio.paInt16
        self.channels = int(1)
        self.rate = int(device_info['defaultSampleRate'])
        self.chunk = 1024

        self.log_path = log_path
        self.log_source = open(log_path, 'w', newline='')
        self.log_writer = csv.writer(self.log_source)
        self.log_writer.writerow(["timestamp", "emotion", "confidence", "transcription"])

        self.starting_time = 0
        self.last_starting_time = 0

        self.current_dominant_emotion = None
        self.current_confidence = -1 

    def record_audio(self, stop_event, file_path):
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(format=self.format, channels=self.channels,
                                rate=self.rate, input=True,
                                frames_per_buffer=self.chunk)
    
            frames = []
            print(f"Audio recording started: {file_path}")
    
            while not stop_event.is_set():
                try:
                    data = stream.read(self.chunk)
                    frames.append(data)
                except Exception as e:
                    print("Error reading audio stream:", e)
                    break
    
            # Write to file INSIDE the thread
            wf = wave.open(file_path, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
    
            stream.stop_stream()
            stream.close()
            audio.terminate()
            print("Audio recording stopped.")
    
        except Exception as e:
            print(f"Audio recording failed: {str(e)}")

    def start_recording(self):
        # Initialize video writer
        #fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        #width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        #height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        #self.stream = cv2.VideoWriter(self.video_path, fourcc, self.fps, (width, height))
        
        # Start audio recording
        self.audio_stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        self.wave_file = wave.open(self.audio_path, 'wb')
        self.wave_file.setnchannels(self.channels)
        self.wave_file.setsampwidth(self.audio.get_sample_size(self.format))
        self.wave_file.setframerate(self.rate)
        self.audio_frames = []

    def stop_recording(self):
        # Stop video
        if self.stream:
            self.stream.release()
            self.stream = None
            
        # Stop audio
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            
        if self.wave_file:
            self.wave_file.writeframes(b''.join(self.audio_frames))
            self.wave_file.close()
            self.wave_file = None

    def render(self):
        frame_count = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            if not self.recording:
                cv2.imshow('Webcam', frame)

            key = cv2.waitKey(1)

            if self.recording:
                self.analyze_faces(frame)
                self.log_emotion()

            if key == ord('q'):
                break
            elif key == ord('s') and self.recording:
                self.recording = False
                #self.stop_recording()
                print("Recording stopped")
                self.audio_stop_event.set()
                self.audio_thread.join()
                self.recording = False

                if self.audio_stop_event:
                    self.audio_stop_event.set()

                # Wait for audio thread to finish writing
                if self.audio_thread and self.audio_thread.is_alive():
                    self.audio_thread.join()
                    
                # Clean up video resources
                if self.stream:
                    self.stream.release()
                    self.stream = None

                self.log_source.close() 
            elif key == ord('r') and not self.recording:
                self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
                self.recording = True
                #self.start_recording()

                self.audio_stop_event = threading.Event()
                 # Start the audio recording thread
                self.audio_thread = threading.Thread(target=self.record_audio, args=(self.audio_stop_event, self.audio_path))
                self.audio_thread.start()

                print("Recording started...")
                self.starting_time = int(frame_count / self.fps)

            frame_count += 1

        self.cap.release()
        cv2.destroyAllWindows()
        self.audio.terminate()
