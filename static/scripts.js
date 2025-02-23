document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 Chatbot UI loaded!");

    // UI Elements
    const sendBtn = document.getElementById("sendBtn");
    const userInput = document.getElementById("userInput");
    const messagesDiv = document.getElementById("messages");
    const recordingPrompt = document.getElementById("recordingPrompt");
    const startRecordingBtn = document.getElementById("startRecording");
    const stopRecordingBtn = document.getElementById("stopRecording");
    const endChatArea = document.getElementById("endChatArea");
    const webcam = document.getElementById("webcam");
    const overlayCanvas = document.getElementById("overlay");
    const minimizeVideoBtn = document.getElementById("minimizeVideo");
    const fullscreenVideoBtn = document.getElementById("fullscreenVideo");

    // Sidebar Tabs Handling
    const sidebarItems = document.querySelectorAll(".sidebar li");
    sidebarItems.forEach(item => {
        item.addEventListener("click", function () {
            sidebarItems.forEach(i => i.classList.remove("active"));
            this.classList.add("active");
            const contentTitle = document.querySelector(".content h2");
            if (this.id === "homeTab") contentTitle.textContent = "Chatbot with Webcam";
            if (this.id === "settingsTab") contentTitle.textContent = "Settings";
            if (this.id === "aboutTab") contentTitle.textContent = "About This App";
        });
    });

    // Global variables for audio recording and overlay analysis interval
    let currentMediaRecorder = null;
    let analysisInterval = null;

    // Setup overlay canvas to match video dimensions
    function setupOverlay() {
        overlayCanvas.width = webcam.videoWidth;
        overlayCanvas.height = webcam.videoHeight;
    }
    webcam.addEventListener("loadedmetadata", setupOverlay);

    // Function to capture current frame and send to backend for analysis
    async function analyzeCurrentFrame() {
        let tempCanvas = document.createElement("canvas");
        tempCanvas.width = webcam.videoWidth;
        tempCanvas.height = webcam.videoHeight;
        let tempCtx = tempCanvas.getContext("2d");
        tempCtx.drawImage(webcam, 0, 0, tempCanvas.width, tempCanvas.height);
        let imageDataUrl = tempCanvas.toDataURL("image/jpeg");
        try {
            let response = await fetch("http://127.0.0.1:5000/uploadFrame", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image: imageDataUrl })
            });
            let analysis = await response.json();
            return analysis;
        } catch (error) {
            console.error("Error analyzing frame:", error);
            return null;
        }
    }

    // Function to draw overlays on the canvas over the video
    function drawOverlays(analysis) {
        if (!analysis) return;
        let ctx = overlayCanvas.getContext("2d");
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        ctx.lineWidth = 2;
        ctx.strokeStyle = "lime";
        ctx.font = "20px Arial";
        ctx.fillStyle = "red";

        if (analysis.boxes && analysis.boxes.length > 0) {
            analysis.boxes.forEach(box => {
                ctx.strokeRect(box.x, box.y, box.w, box.h);
            });
        }
        if (analysis.emotion) {
            ctx.fillText(`${analysis.emotion} (${(analysis.confidence * 100).toFixed(1)}%)`, 10, 30);
        }
    }

    // Step 1: Send initial subtext (only once at the start)
    sendBtn.addEventListener("click", function () {
        let userMessage = userInput.value.trim();
        if (userMessage === "") return;
        userInput.value = "";
        rerender.addMessage("Subtext: " + userMessage, "user");
        // Hide chatbox and show recording prompt area
        document.getElementById("chatbox").style.display = "none";
        recordingPrompt.style.display = "block";
    });

    // Step 2: Start Recording and begin overlay analysis
    startRecordingBtn.addEventListener("click", async () => {
        // Start Video Recording (only when start is pressed)
        try {
            let videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
            webcam.srcObject = videoStream;
            webcam.style.display = "block";
            window.electronAPI.startVideo();
        } catch (error) {
            console.error("Error starting video:", error);
        }
        // Start Audio Recording
        try {
            let audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            let mediaRecorder = new MediaRecorder(audioStream);
            let audioChunks = [];
            mediaRecorder.ondataavailable = (event) => {
                console.log("Audio chunk received:", event.data);
                audioChunks.push(event.data);
            };
            mediaRecorder.onstop = () => {
                console.log("Audio recording stopped. Total chunks:", audioChunks.length);
                let audioBlob = new Blob(audioChunks, { type: "audio/wav" });
                window.electronAPI.sendAudioToBackend(audioBlob);
            };
            window.electronAPI.startAudio();
            mediaRecorder.start();
            currentMediaRecorder = mediaRecorder;
        } catch (error) {
            console.error("Error starting audio:", error);
        }
        // Setup overlay canvas dimensions and start periodic frame analysis (e.g., every 1 second)
        setupOverlay();
        analysisInterval = setInterval(async () => {
            let analysis = await analyzeCurrentFrame();
            drawOverlays(analysis);
        }, 1000);
        // Toggle buttons: hide "Start Recording", show "Stop Recording"
        startRecordingBtn.style.display = "none";
        stopRecordingBtn.style.display = "inline-block";
    });

    // Step 3: Stop Recording, clear overlay analysis, fetch transcription and pointer analysis
    stopRecordingBtn.addEventListener("click", () => {
        // Stop Video Recording
        if (webcam.srcObject) {
            webcam.srcObject.getTracks().forEach(track => track.stop());
            window.electronAPI.stopVideo();
        }
        webcam.style.display = "none";
        // Stop Audio Recording
        if (currentMediaRecorder) {
            currentMediaRecorder.stop();
            window.electronAPI.stopAudio();
            currentMediaRecorder = null;
        }
        // Clear overlay analysis interval and clear overlay canvas
        if (analysisInterval) {
            clearInterval(analysisInterval);
            analysisInterval = null;
        }
        let ctx = overlayCanvas.getContext("2d");
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        // Signal backend to stop recording/transcription
        fetch("http://127.0.0.1:5000/stop_recording", { method: "POST" })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                // Fetch final transcription from backend
                return fetch("http://127.0.0.1:5000/transcribe");
            })
            .then(response => response.json())
            .then(transcriptionData => {
                let transcription = transcriptionData.transcription;
                rerender.addMessage("Subtext: " + transcription, "user");
                // Use transcription to fetch pointer analysis from backend
                return fetch("http://127.0.0.1:5000/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: transcription })
                });
            })
            .then(response => response.json())
            .then(pointerData => {
                rerender.addMessage("Advice: " + pointerData.advice, "bot");
                rerender.addMessage("Reflection: " + pointerData.reflection, "bot");
                // After analysis, remain in recording prompt mode (iteration from Step 2)
                startRecordingBtn.style.display = "inline-block";
                stopRecordingBtn.style.display = "none";
                // Optionally, show End Chat button
                endChatArea.style.display = "block";
            })
            .catch(error => console.error("❌ Error during stop recording sequence:", error));
    });

    // Video Controls: Minimize toggles video visibility
    minimizeVideoBtn.addEventListener("click", () => {
        if (webcam.style.display === "none") {
            webcam.style.display = "block";
        } else {
            webcam.style.display = "none";
        }
    });

    // Video Controls: Fullscreen toggles fullscreen for the video container
    fullscreenVideoBtn.addEventListener("click", () => {
        const videoContainer = document.querySelector(".video-container");
        if (!document.fullscreenElement) {
            videoContainer.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    });

    // End Chat Button: Finalize conversation
    document.getElementById("endChat").addEventListener("click", () => {
        alert("Chat ended. Your conversation history has been saved.");
        // Optionally, navigate to a history page or reset UI for a new conversation.
    });

    // Manual Chat Send Button (if needed)
    sendBtn.addEventListener("click", function () {
        let userMessage = userInput.value.trim();
        if (userMessage === "") return;
        userInput.value = "";
        rerender.addMessage("Subtext: " + userMessage, "user");
        fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            rerender.addMessage("Advice: " + data.advice, "bot");
            rerender.addMessage("Reflection: " + data.reflection, "bot");
        })
        .catch(error => console.error("❌ Chatbot Error:", error));
    });

    // Global Window Close
    document.getElementById("closeApp").addEventListener("click", () => window.electronAPI.closeApp());

    // Listen for responses from Electron (if any)
    if (window.electronAPI && typeof window.electronAPI.receiveMessage === "function") {
      window.electronAPI.receiveMessage((response) => {
          rerender.addMessage(response, "bot");
      });
    } else {
      console.warn("electronAPI.receiveMessage is not available");
    }
});
