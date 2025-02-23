document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 Chatbot UI loaded!");

    // UI Elements
    const webcam = document.getElementById("webcam");
    const startRecordingBtn = document.getElementById("startRecording");
    const stopRecordingBtn = document.getElementById("stopRecording");
    const sendBtn = document.getElementById("sendBtn");
    const userInput = document.getElementById("userInput");
    const messagesDiv = document.getElementById("messages");
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

    // Unified Start Recording: starts both video and audio
    startRecordingBtn.addEventListener("click", async () => {
        // Start Video Recording
        const videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcam.srcObject = videoStream;
        webcam.style.display = "block";
        window.electronAPI.startVideo();

        // Start Audio Recording
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
    });

 // Unified Stop Recording: stops both video and audio and fetches analysis
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

    // After stopping both, fetch the analysis pointer from the backend.
    fetch("http://127.0.0.1:5000/pointer")
        .then(response => response.json())
        .then(data => {
            // Update the chat UI with the analysis result.
            // You can display it as one message or separate lines for subtext, advice, and reflection.
            rerender.addMessage("Analysis Subtext: " + data.subtext, "bot");
            rerender.addMessage("Advice: " + data.advice, "bot");
            rerender.addMessage("Reflection: " + data.reflection, "bot");
        })
        .catch(error => console.error("❌ Analysis Fetch Error:", error));
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

    sendBtn.addEventListener("click", function () {
        const userMessage = userInput.value.trim();
        if (userMessage === "") return;
    
        // Clear the input field
        userInput.value = "";
    
        // Send the user's message (which will be treated as the subtext) to the backend.
        fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            // Display the user's input as the subtext message.
            rerender.addMessage("Subtext: " + userMessage, "user");
            // Display the returned pointer advice and reflection as the bot's response.
            rerender.addMessage("Advice: " + data.advice + " | Reflection: " + data.reflection, "bot");
        })
        .catch(error => console.error("❌ Chatbot Error:", error));
    });
    
    

    // Receive Chatbot Response from Electron
    window.electronAPI.receiveMessage((response) => {
        rerender.addMessage(response, "bot");
    });

    // Global Window Close (if needed)
    document.getElementById("closeApp").addEventListener("click", () => window.electronAPI.closeApp());
});
