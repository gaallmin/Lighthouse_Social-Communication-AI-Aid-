document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 Chatbot UI loaded!");

    // UI Elements
    const webcam = document.getElementById("webcam");
    const startWebcamBtn = document.getElementById("startWebcam");
    const stopWebcamBtn = document.getElementById("stopWebcam");
    const startAudioBtn = document.getElementById("startAudio");
    const stopAudioBtn = document.getElementById("stopAudio");
    const sendBtn = document.getElementById("sendBtn");
    const userInput = document.getElementById("userInput");
    const messagesDiv = document.getElementById("messages");

    // Video-specific control buttons (for video only)
    const minimizeVideoBtn = document.getElementById("minimizeVideo");
    const fullscreenVideoBtn = document.getElementById("fullscreenVideo");

    // 🚀 Sidebar Tabs Handling
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

    // 🚀 Start Webcam (Video recording)
    startWebcamBtn.addEventListener("click", async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcam.srcObject = stream;
        webcam.style.display = "block"; // Show video element
        window.electronAPI.startVideo(); // Notify main process (if needed)
    });

    // 🚀 Stop Webcam
    stopWebcamBtn.addEventListener("click", () => {
        if (webcam.srcObject) {
            webcam.srcObject.getTracks().forEach(track => track.stop());
            window.electronAPI.stopVideo();
        }
        webcam.style.display = "none";
    });

    // 🚀 Video Controls: Minimize (hide) and Fullscreen (for video container)
    minimizeVideoBtn.addEventListener("click", () => {
        // Toggle video visibility only
        if (webcam.style.display === "none") {
            webcam.style.display = "block";
        } else {
            webcam.style.display = "none";
        }
    });

    fullscreenVideoBtn.addEventListener("click", () => {
        const videoContainer = document.querySelector(".video-container");
        if (!document.fullscreenElement) {
            videoContainer.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    });

    // 🚀 Start Audio Recording
    startAudioBtn.addEventListener("click", async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
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
    });

    // 🚀 Stop Audio Recording
    stopAudioBtn.addEventListener("click", () => {
        window.electronAPI.stopAudio();
    });

    // 🚀 Send Chat Message
    sendBtn.addEventListener("click", function () {
        const userMessage = userInput.value.trim();
        if (userMessage === "") return;

        // Send message via Electron API (if used) and update UI
        window.electronAPI.sendUserMessage(userMessage);
        rerender.addMessage(userMessage, "user");
        userInput.value = "";

        fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => rerender.addMessage(data.response, "bot"))
        .catch(error => console.error("❌ Chatbot Error:", error));
    });

    // 🚀 Receive Chatbot Response from Electron
    window.electronAPI.receiveMessage((response) => {
        rerender.addMessage(response, "bot");
    });

    // (Optional) If you still want global window controls for closing the app:
    document.getElementById("closeApp").addEventListener("click", () => window.electronAPI.closeApp());
});
