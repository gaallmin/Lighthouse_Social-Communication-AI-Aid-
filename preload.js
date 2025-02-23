const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electron", {
    sendMessage: (message) => ipcRenderer.send("user-message", message),
    receiveMessage: (callback) => ipcRenderer.on("bot-response", (_event, data) => callback(data)),
    minimizeApp: () => ipcRenderer.send("minimize-app"),
    toggleFullscreen: () => ipcRenderer.send("toggle-fullscreen"),
    closeApp: () => ipcRenderer.send("close-app")
});