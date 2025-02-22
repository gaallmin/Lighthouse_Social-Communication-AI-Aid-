import sounddevice as sd
import numpy as np
import keyboard
from scipy.io.wavfile import write

# Parameters
sample_rate = 44100  # Sample rate in Hz
channels = 2         # Number of audio channels
filename = "output.wav"  # Output filename

# Initialize an empty list to store audio frames
audio_frames = []  # Renamed to avoid conflict

def callback(indata, frame_count, time_info, status):
    """This callback function is called for each audio block."""
    if status:
        print(status)
    audio_frames.append(indata.copy())  # Use the renamed list

# Create a Stream with the callback
with sd.InputStream(samplerate=sample_rate, channels=channels, callback=callback):
    print("Recording... Press 'Esc' to stop.")
    while True:
        if keyboard.is_pressed('Esc'):
            print("Recording stopped.")
            break

# Convert the list of frames into a NumPy array
audio_data = np.concatenate(audio_frames, axis=0)

# Save the recorded data as a WAV file
write(filename, sample_rate, audio_data)
