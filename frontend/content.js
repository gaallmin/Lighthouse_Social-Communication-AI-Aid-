// Chrome Extension Content Script for Zoom Tone Detector
// This script injects an overlay onto Zoom Web to display real-time tone analysis and provide conversation guidance.

// Load lamejs dynamically
const script = document.createElement("script");
script.src = chrome.runtime.getURL("libs/lame.min.js");
document.head.appendChild(script);

script.onload = function () {
    console.log("lamejs loaded successfully!");
};

// Prompt user for context if not set
window.onload = function() {
    console.log("Extension loaded. Waiting for user to enable webcam.");
    
    // Create a button to enable webcam manually
    const webcamButton = document.createElement("button");
    webcamButton.innerText = "Enable Webcam";
    webcamButton.style.position = "fixed";
    webcamButton.style.bottom = "20px";
    webcamButton.style.left = "20px";
    webcamButton.style.padding = "10px";
    webcamButton.style.backgroundColor = "#28a745";
    webcamButton.style.color = "white";
    webcamButton.style.border = "none";
    webcamButton.style.borderRadius = "5px";
    webcamButton.style.cursor = "pointer";
    webcamButton.style.zIndex = "10002";
    document.body.appendChild(webcamButton);
    
    webcamButton.addEventListener("click", function() {
        console.log("Requesting webcam and microphone access...");
        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            .then((stream) => {
                console.log("Webcam and Microphone access granted.");

                // Display webcam preview
                const videoElement = document.createElement("video");
                videoElement.srcObject = stream;
                videoElement.autoplay = true;
                videoElement.style.position = "fixed";
                videoElement.style.bottom = "10px";
                videoElement.style.right = "10px";
                videoElement.style.width = "200px";
                videoElement.style.height = "150px";
                videoElement.style.border = "2px solid white";
                videoElement.style.borderRadius = "10px";
                videoElement.style.zIndex = "10001";
                document.body.appendChild(videoElement);
            })
            .catch((err) => console.error("Webcam/Microphone access denied:", err));
    });
    
    setTimeout(() => {
        let context = localStorage.getItem("interactionContext");
        if (!context || context === "Casual Meeting") {
            context = prompt("What is the context of your interaction? (e.g., Serious Meeting, Friends, Casual Chat)") || "General";
            localStorage.setItem("interactionContext", context);
            chrome.runtime.sendMessage({ action: "updateContext", context: context }); // Send context to popup
            console.log("User selected context:", context);
        }
        
        let contextElement = document.getElementById("context");
        if (contextElement) {
            contextElement.innerText = context;
        } else {
            console.error("Context element not found!");
        }
    }, 500); // Small delay to ensure the DOM is ready
};

// Create an overlay div
toneOverlay = document.createElement("div");
toneOverlay.id = "tone-detector-overlay";
toneOverlay.style.position = "fixed";
toneOverlay.style.bottom = "20px";
toneOverlay.style.right = "20px";
toneOverlay.style.background = "rgba(0, 0, 0, 0.9)";
toneOverlay.style.color = "white";
toneOverlay.style.padding = "15px";
toneOverlay.style.borderRadius = "10px";
toneOverlay.style.fontSize = "16px";
toneOverlay.style.zIndex = "10000";
toneOverlay.style.width = "300px";
toneOverlay.style.boxShadow = "0px 0px 10px rgba(255, 255, 255, 0.5)";
toneOverlay.innerHTML = `
    <p><strong>📝 Context:</strong> <span id="context"></span></p>
    <p><strong>😊 Emotion:</strong> <span id="emotion">Loading...</span></p>
    <p><strong>📊 Confidence:</strong> <span id="confidence">Loading...</span></p>
    <p><strong>💡 Suggestion:</strong> <span id="suggestion">Loading...</span></p>
    <button id="recordButton" style="width:100%; padding:8px; margin-top:10px; cursor:pointer; background-color:#28a745; color:white; border:none; border-radius:5px;">Start Recording</button>
`;
document.body.appendChild(toneOverlay);

// Send stored context to popup on request
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "getContext") {
        sendResponse({ context: localStorage.getItem("interactionContext") || "General" });
    }
});

// Function to update the overlay with detected emotions
function updateOverlay(emotion, confidence, suggestion) {
    const context = localStorage.getItem("interactionContext") || "General";
    document.getElementById("context").innerText = context;
    document.getElementById("emotion").innerText = emotion || "Unknown";
    document.getElementById("confidence").innerText = confidence ? confidence + "%" : "-";
    document.getElementById("suggestion").innerText = suggestion || "No suggestions available.";

    // Save values for popup
    chrome.storage.local.set({ context, emotion, confidence, suggestion });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "toggleRecording") {
        isRecording = !isRecording;
        document.getElementById("recordButton").innerText = isRecording ? "Stop Recording" : "Start Recording";
        document.getElementById("recordButton").style.backgroundColor = isRecording ? "#dc3545" : "#28a745";

        // Save recording status
        chrome.storage.local.set({ isRecording });
    }
});

let isRecording = false;
let mediaRecorder;
let recordedChunks = [];

document.getElementById("recordButton").addEventListener("click", function() {
    isRecording = !isRecording;
    chrome.runtime.sendMessage({ action: "toggleRecording" });
    document.getElementById("recordButton").innerText = isRecording ? "Stop Recording" : "Start Recording";
    document.getElementById("recordButton").style.backgroundColor = isRecording ? "#dc3545" : "#28a745";
});
