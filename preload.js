const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
    startVideo: () => ipcRenderer.send("start-video"),
    stopVideo: () => ipcRenderer.send("stop-video"),
    startAudio: () => ipcRenderer.send("start-audio"),
    stopAudio: () => ipcRenderer.send("stop-audio"),
    sendAudioToBackend: (audioBlob) => ipcRenderer.send("send-audio", audioBlob),
    receiveMessage: (callback) => ipcRenderer.on("bot-response", (_, response) => callback(response)),
    minimizeApp: () => ipcRenderer.send("minimize-app"),
    toggleFullscreen: () => ipcRenderer.send("toggle-fullscreen"),
    closeApp: () => ipcRenderer.send("close-app")
});

console.log("Preload script loaded successfully!");
