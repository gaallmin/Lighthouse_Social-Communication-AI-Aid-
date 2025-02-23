document.addEventListener("DOMContentLoaded", function () {

    console.log("window.electronAPI is:", window.electronAPI);
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

    // Global variable to store the audio MediaRecorder instance
    let currentMediaRecorder = null;
    
    // Step 1: Send Initial Subtext
    sendBtn.addEventListener("click", function () {
        const userMessage = userInput.value.trim();
        if (userMessage === "") return;
        // Clear input and display user's subtext in chat
        userInput.value = "";
        rerender.addMessage("Subtext: " + userMessage, "user");
        // Hide chatbox and show the recording prompt area
        document.getElementById("chatbox").style.display = "none";
        recordingPrompt.style.display = "block";
    });
    
    // Step 2: Start Recording (record audio and video)
    startRecordingBtn.addEventListener("click", async () => {
        // Start Video Recording
        try {
            const videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
            webcam.srcObject = videoStream;
            webcam.style.display = "block";
            window.electronAPI.startVideo();
        } catch (error) {
            console.error("Error starting video:", error);
        }
    
        // Start Audio Recording
        try {
            const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(audioStream);
            let audioChunks = [];
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
                window.electronAPI.sendAudioToBackend(audioBlob);
            };
            window.electronAPI.startAudio();
            mediaRecorder.start();
            currentMediaRecorder = mediaRecorder;
        } catch (error) {
            console.error("Error starting audio:", error);
        }
    
        // Toggle recording buttons: hide "Start Recording", show "Stop Recording"
        startRecordingBtn.style.display = "none";
        stopRecordingBtn.style.display = "inline-block";
    });
    
    // Step 3: Stop Recording & Process Analysis
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
    
        // Signal backend to stop recording/transcription
        fetch("http://127.0.0.1:5000/stop_recording", { method: "POST" })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                // Now fetch the transcription from the backend
                return fetch("http://127.0.0.1:5000/transcribe");
            })
            .then(response => response.json())
            .then(transcriptionData => {
                const transcription = transcriptionData.transcription;
                // Display the transcription in chat
                rerender.addMessage("Subtext: " + transcription, "user");
                // Use the transcription to fetch pointer analysis from backend
                return fetch("http://127.0.0.1:5000/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: transcription })
                });
            })
            .then(response => response.json())
            .then(pointerData => {
                // Display pointer analysis in chat
                rerender.addMessage("Advice: " + pointerData.advice, "bot");
                rerender.addMessage("Reflection: " + pointerData.reflection, "bot");
                // After analysis, remain in recording mode (iteration from Step 2)
                // Keep chatbox hidden and keep showing the recording prompt.
                // Toggle recording buttons back: show "Start Recording", hide "Stop Recording"
                startRecordingBtn.style.display = "inline-block";
                stopRecordingBtn.style.display = "none";
                // (Optionally, if you want to show an "End Chat" button after at least one cycle)
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
        const userMessage = userInput.value.trim();
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
    
//     // Listen for responses from Electron (if any)
//     window.electronAPI.receiveMessage((response) => {
//         rerender.addMessage(response, "bot");
//     });
});
