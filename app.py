from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import base64
import threading

from modules.emotion_detection import AVPointerCreator
from modules.open_api import getPointer
from deepface import DeepFace

# Create Flask app, specifying template and static folders
app = Flask(__name__, static_url_path='/static', template_folder='templates')
CORS(app)

# Ensure the uploads folder exists for saving images/audio
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create a global instance of AVPointerCreator (handles video, audio, transcription, emotion)
av_pointer = AVPointerCreator()

# Serve the main page (index.html)
@app.route("/")
def index():
    return render_template("index.html")

# Start the AVPointer process (video/audio capture) in a separate thread
@app.route("/start", methods=["GET"])
def start_avpointer():
    threading.Thread(target=av_pointer.start, daemon=True).start()
    return jsonify({"message": "AVPointer started"})

@app.route("/stop_recording", methods=["POST"])
def stop_recording():
    av_pointer.transcription_enabled = False
    av_pointer.face_detection_enabled = False
    return jsonify({"message": "Recording stopped"})


# Return the latest transcription from the AVPointer process
@app.route("/transcribe", methods=["GET"])
def get_transcription():
    return jsonify({"transcription": av_pointer.transcription_text})

# Chat API: Return conversation pointers generated via OpenAI
@app.route("/chat", methods=["POST"])
def chat():
    user_subtext = request.json.get("message", None)
    pointer = getPointer(user_subtext)
    # Use dictionary key lookups since pointer is a dict
    return jsonify({
        "subtext": pointer["subtext"],
        "advice": pointer["advice"],
        "reflection": pointer["reflection"]
    })

# Alternate endpoint to get conversation pointers
@app.route("/pointer", methods=["GET"])
def pointer():
    pointer = getPointer()
    return jsonify({
        "subtext": pointer.subtext,
        "advice": pointer.advice,
        "reflection": pointer.reflection
    })

# Upload endpoint: Accept a base64-encoded image (snapshot from video) and perform emotion analysis
@app.route("/upload", methods=["POST"])
def upload():
    data = request.json.get("image", None)
    if not data:
        return jsonify({"error": "No image data provided"}), 400

    try:
        # Expect data format "data:image/jpeg;base64,..."
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
