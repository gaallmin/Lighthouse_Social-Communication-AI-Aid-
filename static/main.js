const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");

let win; // Declare the window variable globally

function createWindow() {
  win = new BrowserWindow({
      width: 1200,           // ✅ Set exact width
      height: 800,           // ✅ Set exact height
      minWidth: 1200,        // ✅ Prevents shrinking
      minHeight: 800,        // ✅ Prevents shrinking
      maxWidth: 1200,        // ✅ Prevents stretching
      maxHeight: 800,        // ✅ Prevents stretching
      frame: false,          // ✅ Removes default window border
      transparent: true,     // ✅ Ensures full transparency
      hasShadow: false,      // ✅ Removes any unwanted shadows
      fullscreenable: true, // ✅ Prevents fullscreen mode
      resizable: true,      // ✅ Prevents manual resizing
      webPreferences: {
          preload: path.join(__dirname, "preload.js"),
          nodeIntegration: false,
          contextIsolation: true
      }
  });

  win.loadFile("index.html");
}

// ✅ Start Video Recording
ipcMain.on("start-video", () => {
    recordingVideo = true;
    console.log("Video recording started");
});

// ✅ Stop Video Recording
ipcMain.on("stop-video", () => {
    recordingVideo = false;
    console.log("Video recording stopped");
});

// ✅ Start Audio Recording
ipcMain.on("start-audio", () => {
    recordingAudio = true;
    console.log("Audio recording started");
    audioChunks = [];
});

// ✅ Stop Audio Recording & Send to Flask
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
            headers: { "Content-Type": "multipart/form-data" }
        })
        .then(response => console.log("Transcription:", response.data.transcription))
        .catch(err => console.error("Error sending audio:", err));
    }
});

// ✅ Handle Frame Sending (Only When Video is Recording)
ipcMain.on("send-frame", (event, imageData) => {
    if (recordingVideo) {
        axios.post("http://127.0.0.1:5000/upload", { image: imageData })
            .then(response => console.log("Emotion Detected:", response.data))
            .catch(err => console.error("Error sending frame:", err));
    }
});

app.whenReady().then(createWindow);