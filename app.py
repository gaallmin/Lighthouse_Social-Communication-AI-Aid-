from flask import Flask, render_template, Response
import cv2
from AVPointer import AVPointerCreator

app = Flask(__name__)
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    av_pointer = AVPointerCreator()
    av_pointer.start_transcribe_thread()
        
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)"""

from flask import Flask, render_template, jsonify, request
import threading
import time

# Import AVPointerCreator class from your main file
from AVPointer import AVPointerCreator

app = Flask(__name__)
av_pointer = AVPointerCreator()

# Start transcription and video processing in separate threads
def start_av_pointer():
    av_pointer.start()

t = threading.Thread(target=start_av_pointer, daemon=True)
t.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/toggle_transcription', methods=['POST'])
def toggle_transcription():
    av_pointer.transcription_enabled = not av_pointer.transcription_enabled
    return jsonify({"transcription_enabled": av_pointer.transcription_enabled})

@app.route('/toggle_face_detection', methods=['POST'])
def toggle_face_detection():
    av_pointer.face_detection_enabled = not av_pointer.face_detection_enabled
    return jsonify({"face_detection_enabled": av_pointer.face_detection_enabled})

@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify({
        "transcription": av_pointer.transcription_text,
        "emotion": av_pointer.dominant_emotion,
        "confidence": av_pointer.confidence
    })

if __name__ == '__main__':
    app.run(debug=True)