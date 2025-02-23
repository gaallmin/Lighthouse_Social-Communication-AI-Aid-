from flask import Flask, send_from_directory
from flask import render_template

import os

from src.talk import *

app = Flask(__name__)

log_path = "log.csv"
log_dir = os.path.dirname(os.path.abspath(log_path))

video_path = "output.mp4"
audio_path = "output.mp3"

@app.route('/')
def index():
    return 'Index Page'

@app.route('/download')
def download_log():
    video_streamer = VideoStreamer(video_path, audio_path, log_path)
    video_streamer.render()
    
    # Process the WAV file
    at = AudioToText(audio_path, "tiny")
    #language = at.get_language(audio_path)
    #print(f"Detected language: {language}")
    
    text = at.transcribe()
    video_streamer.append_to_last_row(text)

    return send_from_directory(log_dir, log_path, as_attachment=True) # sends file over web, pass to chatgpt instead

@app.route('/app')
def hello():
    return render_template('app.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
