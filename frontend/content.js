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
    let context = localStorage.getItem("interactionContext");
    
    if (!context || context === "Casual Meeting") {
        context = prompt("What is the context of your interaction? (e.g., Serious Meeting, Friends, Casual Chat)");
        if (context) {
            localStorage.setItem("interactionContext", context);
            chrome.runtime.sendMessage({ action: "updateContext", context: context }); // Send context to popup
            console.log("User selected context:", context);
        }
    }

    // Wait until the overlay is added before updating the context
    setTimeout(() => {
        let contextElement = document.getElementById("context");
        if (contextElement) {
            contextElement.innerText = context || "General";
        } else {
            console.error("Context element not found!");
        }
    }, 100); // Small delay to ensure the DOM is ready
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

// Function to update the overlay with detected emotions
function updateOverlay(emotion, confidence, suggestion) {
    const context = localStorage.getItem("interactionContext") || "General";
    document.getElementById("context").innerText = context;
    document.getElementById("emotion").innerText = emotion || "Unknown";
    document.getElementById("confidence").innerText = confidence ? confidence + "%" : "-";
    document.getElementById("suggestion").innerText = suggestion || "No suggestions available.";
}

// Retrieve stored context
function getContext() {
    return localStorage.getItem("interactionContext") || "General";
}

// Set context from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "setContext") {
        localStorage.setItem("interactionContext", message.context);
        console.log("Updated context:", message.context);
        updateOverlay("", "", ""); // Refresh overlay with new context
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

// Capture Zoom Web Audio & Send to Whisper API
function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(async (stream) => {
            mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            recordedChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const webmBlob = new Blob(recordedChunks, { type: "audio/webm" });
                console.log("Recording stopped. Converting to MP3...");
                const mp3Blob = await convertToMP3(webmBlob);
                await saveRecording(mp3Blob);
            };

            mediaRecorder.start();
            isRecording = true;
            console.log("Recording started...");
        })
        .catch((err) => console.error("Error accessing microphone:", err));
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        console.log("Recording stopped.");
    }
}

// Listen for messages from the popup to start/stop recording
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "toggleRecording") {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }
});
