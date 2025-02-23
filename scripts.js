document.addEventListener("DOMContentLoaded", function () {
    console.log("Chatbot UI loaded!");

    const webcam = document.getElementById("webcam");
    const startWebcamBtn = document.getElementById("startWebcam");
    const sendBtn = document.getElementById("sendBtn");
    const userInput = document.getElementById("userInput");
    const messagesDiv = document.getElementById("messages");

    // Sidebar Tabs
    const sidebarItems = document.querySelectorAll(".sidebar li");
    sidebarItems.forEach(item => {
        item.addEventListener("click", function () {
            sidebarItems.forEach(i => i.classList.remove("active"));
            this.classList.add("active");

            if (this.id === "homeTab") {
                document.querySelector(".content h2").textContent = "Chatbot with Webcam";
            } else if (this.id === "settingsTab") {
                document.querySelector(".content h2").textContent = "Settings";
            } else if (this.id === "aboutTab") {
                document.querySelector(".content h2").textContent = "About This App";
            }
        });
    });

    function addMessage(text, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.textContent = text;
        msgDiv.classList.add("message");
    
        if (sender === "user") {
            msgDiv.classList.add("user-message");
        } else {
            msgDiv.classList.add("bot-message");
        }
    
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to latest message
    }

    // Start Webcam
    startWebcamBtn.addEventListener("click", function () {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                webcam.srcObject = stream;
                webcam.style.display = "block"; // Show webcam when started
            })
            .catch(err => {
                console.error("Error accessing webcam:", err);
            });
    });

    // Send Message to Chatbot
    function sendMessage() {
        const userMessage = userInput.value.trim();
        if (userMessage === "") return;

        addMessage(userMessage, "user");
        window.electron.sendMessage(userMessage);
        userInput.value = "";
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            event.preventDefault(); // Prevents adding a new line in input
            sendMessage();
        }
    });

    // Receive Chatbot Response from Electron
    window.electron.receiveMessage((response) => {
        addMessage(response, "bot");
    });

    // 🚀 Handle Window Controls (Minimize, Fullscreen, Close)
    const minimizeBtn = document.getElementById("minimizeApp");
    const fullscreenBtn = document.getElementById("fullscreenApp");
    const closeBtn = document.getElementById("closeApp");

    if (minimizeBtn) {
        minimizeBtn.addEventListener("click", function () {
            console.log("✅ Minimize button clicked!");
            window.electron.minimizeApp();
        });
    }

    if (fullscreenBtn) {
        fullscreenBtn.addEventListener("click", function () {
            console.log("✅ Fullscreen button clicked!");
            window.electron.toggleFullscreen();
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", function () {
            console.log("✅ Close button clicked!");
            window.electron.closeApp();
        });
    }
});