// Log when the background script starts
console.log("Background script loaded.");

// Inject content script when the user navigates to Zoom Web
chrome.webNavigation.onCompleted.addListener((details) => {
    chrome.scripting.executeScript({
        target: { tabId: details.tabId },
        files: ["content.js"]
    });
}, { url: [{ hostContains: "zoom.us" }] });

// Handle messages from popup or content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "toggleRecording") {
        console.log("Toggling recording...");
        // Send a message to content.js to handle recording
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { action: "toggleRecording" });
        });
    }
});
