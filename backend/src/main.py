from talk import *

video_path = "output.mp4"
audio_path = "output.wav"
log_path = "log.csv"

# Usage
video_streamer = VideoStreamer(video_path, audio_path, log_path)
video_streamer.render()

# Process the WAV file
at = AudioToText(audio_path, "tiny")
#language = at.get_language(audio_path)
#print(f"Detected language: {language}")

text = at.transcribe()
video_streamer.append_to_last_row(text)

#print(text)
