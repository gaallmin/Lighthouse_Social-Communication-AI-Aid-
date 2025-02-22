class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.audioBuffer = [];
        this.isRecording = false;

        this.port.onmessage = (event) => {
            if (event.data === "startRecording") {
                this.isRecording = true;
                this.audioBuffer = []; // Reset buffer
            } else if (event.data === "stopRecording") {
                this.isRecording = false;
                this.port.postMessage({ type: "audioData", buffer: this.audioBuffer });
            }
        };
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (this.isRecording && input.length > 0) {
            this.audioBuffer.push(new Float32Array(input[0])); // Store raw audio
        }
        return true; // Keep processor running
    }
}

registerProcessor("audio-processor", AudioProcessor);

