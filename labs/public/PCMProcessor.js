
// conversion of audio from Float32 to Int16 PCM (pulse-code modulation), 
// digital audio format that is uncompressed and lossless, low latency, support for streaming direcly into APIs like google TTS - "LINEAR16"
class PCMProcessor extends AudioWorkletProcessor {
    process(inputs) {
      const input = inputs[0]; // audio input from microphone

      if (input.length > 0) {
        const channelData = input[0]; // mono audio input

        // convert float32 to int16 PCM data
        const pcmBuffer = new Int16Array(channelData.length);
        for (let i = 0; i < channelData.length; i++) {
          const s = Math.max(-1, Math.min(1, channelData[i]));
          pcmBuffer[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        //send PCM data to main thread
        this.port.postMessage(pcmBuffer.buffer, [pcmBuffer.buffer]);
      }
      return true;
    }
  }
  
  // assign name to the processor
  registerProcessor("pcm-processor", PCMProcessor);