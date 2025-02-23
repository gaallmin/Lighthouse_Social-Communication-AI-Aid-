from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
import threading
import numpy as np
import cv2
from deepface import DeepFace
from modules.emotion_detection import AVPointerCreator
from modules.open_api import getPointer

app = Flask(__name__, static_url_path='/static', template_folder='templates')
CORS(app)

# Ensure the uploads folder exists for saving images/audio
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create a global instance of AVPointerCreator (handles video, audio, transcription, emotion)
av_pointer = AVPointerCreator()

# Load the face cascade for frame analysis (for /uploadFrame endpoint)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["GET"])
def start_avpointer():
    threading.Thread(target=av_pointer.start, daemon=True).start()
    return jsonify({"message": "AVPointer started"})

@app.route("/uploadFrame", methods=["POST"])
def upload_frame():
    data = request.json.get("image")
    if not data:
        return jsonify({"error": "No image data provided"}), 400

    try:
        # Extract base64 data (expects "data:image/jpeg;base64,..." format)
        image_data = base64.b64decode(data.split(",")[1])
    except Exception as e:
        return jsonify({"error": "Invalid image data", "details": str(e)}), 400

    # Convert image data to a NumPy array and decode it into an OpenCV image
    nparr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    boxes = []
    emotion_text = ""
    confidence = 0.0

    # Convert frame to grayscale and detect faces
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    for (x, y, w, h) in faces:
        boxes.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
        # Crop face region and convert to RGB
        face_roi = frame[y:y+h, x:x+w]
        face_roi_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
        try:
            analysis = DeepFace.analyze(face_roi_rgb, actions=['emotion'], enforce_detection=False)
            emotion_text = analysis[0]['dominant_emotion']
            confidence = analysis[0]['face_confidence']
        except Exception as e:
            print("DeepFace Error:", str(e))
    
    return jsonify({
        "boxes": boxes,
        "emotion": emotion_text,
        "confidence": confidence
    })

@app.route("/stop_recording", methods=["POST"])
def stop_recording():
    # Signal the AVPointerCreator to stop further transcription and face detection.
    av_pointer.transcription_enabled = False
    av_pointer.face_detection_enabled = False

    # Perform a final transcription on the last recorded audio (temp.wav), if it exists.
    temp_file = "temp.wav"
    if os.path.exists(temp_file):
        result = av_pointer.whisper_model.transcribe(temp_file)
        av_pointer.transcription_text = result["text"]
        print("Final transcription:", av_pointer.transcription_text)
    else:
        print("No temp.wav found for final transcription.")
    
    return jsonify({"message": "Recording stopped"})

@app.route("/transcribe", methods=["GET"])
def get_transcription():
    return jsonify({"transcription": av_pointer.transcription_text})

@app.route("/chat", methods=["POST"])
def chat():
    user_subtext = request.json.get("message", None)
    pointer = getPointer(user_subtext)
    # Using dictionary key lookups (pointer is a dict)
    return jsonify({
        "subtext": pointer["subtext"],
        "advice": pointer["advice"],
        "reflection": pointer["reflection"]
    })

@app.route("/pointer", methods=["GET"])
def pointer_endpoint():
    pointer = getPointer()
    return jsonify({
        "subtext": pointer["subtext"],
        "advice": pointer["advice"],
        "reflection": pointer["reflection"]
    })

@app.route("/upload", methods=["POST"])
def upload():
    data = request.json.get("image", None)
    if not data:
        return jsonify({"error": "No image data provided"}), 400

    try:
        image_data = base64.b64decode(data.split(",")[1])
    except Exception as e:
        return jsonify({"error": "Invalid image data"}), 400

    image_path = os.path.join(UPLOAD_FOLDER, "frame.jpg")
    with open(image_path, "wb") as f:
        f.write(image_data)

    try:
        analysis = DeepFace.analyze(image_path, actions=["emotion"], enforce_detection=False)
        emotion = analysis[0]['dominant_emotion']
        confidence = analysis[0]['face_confidence']
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"emotion": emotion, "confidence": confidence})

if __name__ == "__main__":
    app.run(debug=True)
