import cv2
import whisper
import ffmpeg
import numpy as np

import wave
import pyaudio

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

#class VideoStreamer():
#    def setup_cv2_video_writer(self, file_path):
#        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
#        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#        return cv2.VideoWriter(file_path, fourcc, fps, (width, height))
#
#    def __init__(self, video_path, audio_path, default_camera=0):
#        self.video_path = video_path
#        self.audio_path = audio_path
#        self.cap = cv2.VideoCapture(0)
#        self.recording = False
#        self.stream = self.setup_cv2_video_writer(self.video_path)
#
#        self.audio = pyaudio.PyAudio()
#        self.audio_stream = None
#        self.wave_file = None
#        self.audio_frames = []
#
#        # Audio parameters
#        self.format = pyaudio.paInt16
#        self.channels = 1
#        self.rate = 44100
#        self.chunk = 1024
#
#    def start_recording(self):
#        self.audio_stream = self.audio.open(
#            format=self.format,
#            channels=self.channels,
#            rate=self.rate,
#            input=True,
#            frames_per_buffer=self.chunk
#        )
#        self.audio_frames = []
#        self.wave_file = wave.open(self.audio_path, 'wb')
#        self.wave_file.setnchannels(self.channels)
#        self.wave_file.setsampwidth(self.audio.get_sample_size(self.format))
#        self.wave_file.setframerate(self.rate)
#
#    def stop_recording(self):
#        # Stop video recording
#        self.stream.release()
#
#        # Stop audio recording
#        if self.audio_stream:
#            self.audio_stream.stop_stream()
#            self.audio_stream.close()
#        if self.wave_file:
#            self.wave_file.writeframes(b''.join(self.audio_frames))
#            self.wave_file.close()
#
#    """
#    Takes in a video frame from the camera and outputs the split video
#    """
#    def render(self):
#        frame_count = 0
#        recording_count = [-1, -1]
#        recording_enabled = [False, False]
#        while True:
#            ret, frame = self.cap.read() # Read a frame from the webcam
#            # Perform your ML processing here on 'frame'
#            cv2.imshow('Webcam', frame) # Display the frame
#            pressed_key = cv2.waitKey(1)
#            if pressed_key == ord('q'):
#                print("Exiting")
#                break
#            elif pressed_key == ord('s'):
#                self.recording = False
#                self.stop_recording()
#                #if not recording_enabled[1]:
#                #    recording_count[1] = frame_count
#                #    recording_enabled[1] = True
#                print("Releasing frames")
#            elif pressed_key == ord('r'): # start record
#                self.recording = True
#                self.start_recording()
#                #if not recording_enabled[0]:
#                #    recording_count[0] = frame_count
#                #    recording_enabled[0] = True
#                print("Writing frames")
#                self.stream.write(frame)
#            frame_count += 1
#        self.cap.release()
#        cv2.destroyAllWindows()
#
#    def get_video_path(self):
#        return self.video_path
#
#
#video_streamer = VideoStreamer("output.mp4", "output.wav")
#video_streamer.render()
#
#audio_location = "../res/russian-example.mp3"
#at = AudioToText(audio_location, "tiny")
#language = at.get_language(audio_location)
#print(f"Detected language: {language}") 
#
#text = at.transcribe()
#print(text)

class VideoStreamer():
    def __init__(self, video_path, audio_path, default_camera=0):
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

        # Verify audio device parameters
        device_info = self.audio.get_default_input_device_info()
        self.format = pyaudio.paInt16
        self.channels = int(1)
        self.rate = int(device_info['defaultSampleRate'])
        self.chunk = 1024

    def start_recording(self):
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.stream = cv2.VideoWriter(self.video_path, fourcc, fps, (width, height))
        
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
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            cv2.imshow('Webcam', frame)
            key = cv2.waitKey(1)

            if key == ord('q'):
                break
            elif key == ord('s') and self.recording:
                self.recording = False
                self.stop_recording()
                print("Recording stopped")
            elif key == ord('r') and not self.recording:
                self.recording = True
                self.start_recording()
                print("Recording started...")

            if self.recording:
                # Write video frame
                self.stream.write(frame)
                # Capture audio data
                data = self.audio_stream.read(self.chunk)
                self.audio_frames.append(data)

        self.stop_recording()
        self.cap.release()
        cv2.destroyAllWindows()
        self.audio.terminate()

# Usage
video_streamer = VideoStreamer("output.mp4", "output.wav")
video_streamer.render()

# Process the WAV file
at = AudioToText("output.wav", "tiny")
language = at.get_language("output.wav")
print(f"Detected language: {language}")
text = at.transcribe()
print(text)
