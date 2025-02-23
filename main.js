const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");
const axios = require("axios");
const FormData = require("form-data");

// Global variables for recording state
let win;
let recordingVideo = false;
let recordingAudio = false;
let audioChunks = [];

// Create the BrowserWindow
function createWindow() {
  win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1200,
    minHeight: 800,
    maxWidth: 1200,
    maxHeight: 800,
    frame: false,
    transparent: true,
    hasShadow: false,
    fullscreenable: true,
    resizable: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  win.loadFile(path.join(__dirname, "templates", "index.html"));
  win.loadURL("http://127.0.0.1:5000");

}

// IPC: Start Video Recording
ipcMain.on("start-video", () => {
  recordingVideo = true;
  console.log("Video recording started");
});

// IPC: Stop Video Recording
ipcMain.on("stop-video", () => {
  recordingVideo = false;
  console.log("Video recording stopped");
});

// IPC: Start Audio Recording
ipcMain.on("start-audio", () => {
  recordingAudio = true;
  console.log("Audio recording started");
  audioChunks = [];
});

// IPC: Stop Audio Recording & Send to Flask
ipcMain.on("stop-audio", async () => {
  recordingAudio = false;
  console.log("Audio recording stopped");

  if (audioChunks.length > 0) {
    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    const audioPath = path.join(__dirname, "temp_audio.wav");
    fs.writeFileSync(audioPath, Buffer.from(await audioBlob.arrayBuffer()));

    const formData = new FormData();
    formData.append("audio", fs.createReadStream(audioPath));

    axios.post("http://127.0.0.1:5000/transcribe", formData, {
      headers: formData.getHeaders()
    })
    .then(response => console.log("Transcription:", response.data.transcription))
    .catch(err => console.error("Error sending audio:", err));
  }
});

app.whenReady().then(createWindow);
