contextBridge.exposeInMainWorld("electronAPI", {
    sendUserMessage: (message) => ipcRenderer.send("user-message", message),
    receiveMessage: (callback) => ipcRenderer.on("bot-response", (_, response) => callback(response)),
    startVideo: () => ipcRenderer.send("start-video"),
    stopVideo: () => ipcRenderer.send("stop-video"),
    startAudio: () => ipcRenderer.send("start-audio"),
    stopAudio: () => ipcRenderer.send("stop-audio"),
    sendAudioToBackend: (audioBlob) => ipcRenderer.send("send-audio", audioBlob),
    minimizeApp: () => ipcRenderer.send("minimize-app"),
    toggleFullscreen: () => ipcRenderer.send("toggle-fullscreen"),
    closeApp: () => ipcRenderer.send("close-app")
});
