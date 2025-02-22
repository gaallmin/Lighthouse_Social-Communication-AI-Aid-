import cv2
from deepface import DeepFace
from datetime import datetime
import csv
import os
import time

import whisper
import numpy as np
import wave
import pyaudio

from talk import *
from video_model import *

video_path = "output.mp4"
audio_path = "output.wav"
log_path = "log.csv"

# Usage
video_streamer = VideoStreamer(video_path, audio_path, log_path)
video_streamer.render()

# Process the WAV file
at = AudioToText(audio_path, "tiny")
language = at.get_language(audio_path)
print(f"Detected language: {language}")
text = at.transcribe()

video_streamer.append_audio_to_log(text)

print(text)
