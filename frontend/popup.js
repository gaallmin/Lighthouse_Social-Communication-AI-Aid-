document.addEventListener("DOMContentLoaded", function () {
    chrome.storage.local.get(["context", "emotion", "confidence", "suggestion", "isRecording"], (data) => {
        document.getElementById("context").innerText = data.context || "General";
        document.getElementById("emotion").innerText = data.emotion || "Loading...";
        document.getElementById("confidence").innerText = data.confidence ? data.confidence + "%" : "-";
        document.getElementById("suggestion").innerText = data.suggestion || "No suggestions available";

        const recordButton = document.getElementById("recordButton");
        recordButton.innerText = data.isRecording ? "Stop Recording" : "Start Recording";
        recordButton.style.backgroundColor = data.isRecording ? "#dc3545" : "#28a745";
    });

    document.getElementById("recordButton").addEventListener("click", function () {
        chrome.runtime.sendMessage({ action: "toggleRecording" });
    });
});
