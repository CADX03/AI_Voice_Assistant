import {useRef, useImperativeHandle, forwardRef } from 'react'
import * as Constants from '../constants/index.ts'
import * as WebSocketMsgProtocol from '../utils/WebSocketMsgProtocol.ts';

//// # 
/// DataStreamer component
//// # 

interface DataStreamerHandle {
    startStreaming: () => void;
    stopStreaming: () => void; // stop streaming audio to backend, but not disconnect
    sendData: (data: WebSocketMsgProtocol.BackendMessage) => void; // additional data that isn't directly related to audio, send to backend
}

interface DataStreamerProps {
    signalEndConversation: () => void;
    config?: Constants.ConfigParams | null;
    onData?: (data: WebSocketMsgProtocol.ProcessedMessage) => void; // callback function when data is received from backend, that isn't related to audio streaming, to present on frontend
}

//// # 
// set backend URL
//// #
const getBackendUrl = () => {
  // Use VITE_BACKEND_URL if defined (set during build or runtime)
  const envBackendUrl = import.meta.env.VITE_BACKEND_URL;
  if (envBackendUrl) {
    return envBackendUrl;
  }

  // Fallback for local development
  if (import.meta.env.MODE === 'development') {
    return 'ws://localhost:8000/ws/call';
  }

  // Fallback for production (assumes backend is hosted at the same origin)
  const { protocol, host } = window.location;
  const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
  return `${wsProtocol}//${host}/ws/call`;
};

const BACKEND_URL = getBackendUrl();
console.log('Using backend URL:', BACKEND_URL);

//// # 
// actual component related
//// #
const DataStreamer = forwardRef<DataStreamerHandle, DataStreamerProps>(({ 
  signalEndConversation, 
  config,
  onData }, ref) => {

    // NOTE: both useRef and useState remember their values between renders, but useRef does not trigger a re-render when its value changes, while useState does.
    // reference variables
    const socketRef = useRef<WebSocket | null>(null); // websocket connection to backend
    const contextRef = useRef<AudioContext | null>(null); // context for audio processing (input and output) // NOTE: only close this at end or it breaks audio input and output
    const streamRef = useRef<MediaStream | null>(null); // microphone input stream from user in browser, sent to backend
    const processorRef = useRef<AudioWorkletNode | null>(null); // audio processor (converts audio to PCM format) from mic to backend
    const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null); // For playback in browser
    const pcmBufferRef = useRef<Uint8Array>(new Uint8Array(0)); // buffer to store audio data from mic, so we only send data to backend when we have a chunk of x bytes expected by backend
    
    //chatbot response handling logic
    const pendingAudioRef = useRef<ArrayBuffer | null>(null); // Store initial chatbot audio, before user presses mic
    const conversationStarted = useRef(false); // flag to check if conversation has started
    const isEnded = useRef(false); // flag to check if conversation has ended, so not to allow reconnection

    // data variables
    const sampleRate = 16000; // sample rate for audio processing
    const chunkSize = 2048; // chunk size for audio processing
    let incomingAudioMimeType = "audio/mp3"; // audio type, can be changed by backend with metadata message, but default is mp3

    // Expose startStreaming and stopStreaming funcs to parent via ref
    useImperativeHandle(ref, () => ({
        connect,
        startStreaming,
        stopStreaming,
        disconnect,
        sendData
    }));

    // send additional data to backend, that isn't directly related to audio streaming
    const sendData = (data: WebSocketMsgProtocol.BackendMessage) => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(
          JSON.stringify({ type: 'data', payload: data }));
      }
    };

    //connect to backend service
    const connect = () => {
      if (socketRef.current || isEnded.current) {
        return
      }

      // create websocket connection to backend
      const socket = new WebSocket(BACKEND_URL);
      socket.binaryType = "arraybuffer";
      socketRef.current = socket;
    
      // Handle WebSocket messages (mic and playback)
      socket.onopen = () => {
        console.log('WebSocket connected');
        if (config) {
          console.log('Sending config to backend:', config);
          WebSocketMsgProtocol.sendWebsocketConfigMsg(socket, config); // send config to backend
        }
      }
      socket.onmessage = handleIncomingMessage;
      socket.onclose = () => console.log('WebSocket closed')
      socket.onerror = (error) => { console.error('WebSocket error:', error)}
    }

    // disconnect from backend service
    // if passive mode, only close the connection, but dont stop streaming

    const disconnect = (passive: boolean = false) => {
      if (!passive) {
        stopStreaming();

        // disable audioContext
        if (contextRef.current) {
          contextRef.current.close();
          contextRef.current = null;
        }

        pendingAudioRef.current = null;
        conversationStarted.current = false;
      }

      // close websocket connection
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.close();
      }
      socketRef.current = null;
      console.log('WebSocket disconnected');
    }

    // AudioContext: https://developer.mozilla.org/en-US/docs/Web/API/AudioContext
    // Stream input audio: https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/createMediaStreamSource
    // start detecting audio from microphone
    // data is streamed to backend in raw PCM format
    // TODO: later, backend should support direct streaming of PCM format to TTS service, so we dont need to do synchronous requests in wav format!!

    const startStreaming = async () => {
      // Ensure connection if not already open
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        connect(); 
      }

      try {
          // prompt user for microphone access
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          streamRef.current = stream;
          
          // NOTE: this sample rate should be matched with the streaming rate in the backend!!
          const context = new AudioContext({ sampleRate: sampleRate });
          contextRef.current = context;

          // load low-level audio processor from separate file
          // AudioWorklets run on their own thread for low-latency and "better control of audio stream"?
          await context.audioWorklet.addModule("/PCMProcessor.js");
          const processor = new AudioWorkletNode(context, "pcm-processor"); // load the processor defined in PCMProcessor.js
          processorRef.current = processor;

          const source = context.createMediaStreamSource(stream);
          pcmBufferRef.current = new Uint8Array(0);

          //send audioWorklet data over websocket
          processor.port.onmessage = handleOutgoingMessage
          
          source.connect(processor)

          // Play initial audio (if its first time) when audioContext initialized
          if (!conversationStarted.current && pendingAudioRef.current) {
            const audioBuffer = await context.decodeAudioData(pendingAudioRef.current);
            playAudio(audioBuffer);
            pendingAudioRef.current = null; // Clear after playing
            conversationStarted.current = true; // set flag to true, so we dont store the initial audio again
          }

        } catch (err) {
        console.error("Audio streaming error:", err);
      }
    };

    //stop detecting audio from microphone
    const stopStreaming = () => {
      if (processorRef.current) {
        processorRef.current.disconnect();
        processorRef.current = null
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      // pcmBufferRef.current = new Uint8Array(0);
    };

    // handle outgoing audio data from mic to backend
    const handleOutgoingMessage = (e: MessageEvent) => {
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) return;

      const newChunk = new Uint8Array(e.data);
      const oldBuffer = pcmBufferRef.current;
      const combined = new Uint8Array(oldBuffer.length + newChunk.length);
      combined.set(oldBuffer);
      combined.set(newChunk, oldBuffer.length);
      pcmBufferRef.current = combined;

      // send only data over websocket when x amount of bytes (chunk) is reached
      while (pcmBufferRef.current.length >= chunkSize) {
        const chunkToSend = pcmBufferRef.current.slice(0, chunkSize);
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.send(chunkToSend);
        }

        pcmBufferRef.current = pcmBufferRef.current.slice(chunkSize);
      }
    }

    // handle incoming audio data from backend to frontend
    const handleIncomingMessage = async (e: MessageEvent) => {

      // receiving string message from backend
      if (typeof e.data === "string") { 
          const message = JSON.parse(e.data);

          if (message.type === 'error') {
            console.error('Error from backend:', message.payload);
            return;
          }
          // update audio bytes type from backend
          if (message.type === 'audio' && message.payload?.type === 'audio_metadata') {
            incomingAudioMimeType = message.payload.mime_type || "audio/mp3";
            return;
          }
          // logs data unrelated to audio streaming, to be presented on frontend
          if (message.type === 'data' && onData) {
            const processed = WebSocketMsgProtocol.processWebsocketDataMsg(message.payload);
            if (processed) {
              onData(processed);
            }
            return;
          // data related to audio streaming
          } else if (message.type === 'command') {
              const cmd_type = message.payload.value

              if (cmd_type === 'STOP_AUDIO') {
                stopPlayback();
                console.log('Audio stopped');
                return;
              } else if (cmd_type === 'EXIT') {
                  isEnded.current = true;
                  disconnect(true);
                  console.log('Exit signal from backend');
                  signalEndConversation();
                  return;
              }
          } else {
            console.error('Unknown JSON message from backend:', message);
            return;
          }
  
      // receiving audio data from TTS service ( assuming its mp3 data)
      } else { 
        const audioBlob = new Blob([e.data], { type: incomingAudioMimeType });
        const arrayBuffer = await audioBlob.arrayBuffer();

        // if no audiocontext found
        if (!contextRef.current) {
          // if player hasn't pressed the mic button for the first time yet, store the initial audio from chatbot, to play when the user presses the mic button
          if (!conversationStarted.current) {
            pendingAudioRef.current = arrayBuffer;
          } else {
            console.error('AudioContext not initialized');
          }
            return;
        }

        try {
          const audioBuffer = await contextRef.current.decodeAudioData(arrayBuffer);
          playAudio(audioBuffer);
          // Debug the message received
        } catch (err) {
          console.error('Error decoding audio data:', err);
        }
      }
    }

    // Stream output audio: https://developer.mozilla.org/en-US/docs/Web/API/AudioBuffer
    // play audio clip in browser
    const playAudio = (audioBuffer: AudioBuffer) => {
      stopPlayback(); // Stop any existing playback
      if (!contextRef.current) {
        console.error('AudioContext not available for playback');
        return;
      }
      sourceNodeRef.current = contextRef.current.createBufferSource();
      sourceNodeRef.current.buffer = audioBuffer;
      sourceNodeRef.current.connect(contextRef.current.destination);
      sourceNodeRef.current.onended = () => {
        sourceNodeRef.current = null;
        // console.log('Audio playback finished naturally');
      };
      sourceNodeRef.current.start();
      // console.log('Audio playback started');
    };
  
    // stop audio playback in browser
    const stopPlayback = () => {
      if (sourceNodeRef.current) {
        sourceNodeRef.current.stop();
        sourceNodeRef.current.disconnect();
        sourceNodeRef.current = null;
        // console.log('Audio playback stopped manually');
      }
    };

    //page render elements
    return null // dont need to render anything in page, just logic
  }
);

export default DataStreamer