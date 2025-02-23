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

// ✅ Basic Chatbot Logic
ipcMain.on("user-message", (event, message) => {
    console.log("User: " + message);

    let botResponse = "I don't understand.";

    if (message.toLowerCase().includes("hello")) {
        botResponse = "Hello! How can I assist you today?";
    } else if (message.toLowerCase().includes("webcam")) {
        botResponse = "Your webcam should be working!";
    }

    event.reply("bot-response", botResponse);
});

// ✅ Step 6: Handle Window Control Events (Minimize, Maximize, Close)
ipcMain.on("minimize-app", () => {
    win.minimize();
});

ipcMain.on("toggle-fullscreen", () => {
  console.log("Toggling Fullscreen Mode");
  win.setFullScreen(!win.isFullScreen());
});

ipcMain.on("close-app", () => {
    app.quit();
});

// ✅ Start Electron App
app.whenReady().then(createWindow);
