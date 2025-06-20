import * as Constants from '../constants/index.ts'

export interface ProcessedMessage {
    type: 'text_stt' | 'text_tts' | 'text_output' | 'timestamp_stt' | 'timestamp_llm' | 'timestamp_tts';
    value: string;
}
  
//data from backend, that isn't related to audio streaming, formats that payload can assume
export interface BackendMessage {
    type: 'text' | 'timestamp';
    subtype: 'stt' | 'tts' | 'output' | 'llm';
    value: string | number;
}
  
export function processWebsocketDataMsg(message: BackendMessage): ProcessedMessage | null {
  switch (message.type) {
    case 'text':
      switch (message.subtype) {
        case 'stt':
          return { type: 'text_stt', value: `STT: ${message.value}` };
        case 'tts':
          return { type: 'text_tts', value: `TTS: ${message.value}` };
        case 'output':
          return { type: 'text_output', value: `Output: ${message.value}` };
        default:
          console.warn(`Unknown text subtype: ${message.subtype}`);
          return null;
      }
    case 'timestamp':
      const formattedTime = typeof message.value === 'number' 
        ? `${message.value.toFixed(2)}s`
        : String(message.value);
      switch (message.subtype) {
        case 'stt':
          return { type: 'timestamp_stt', value: `STT Timestamp: ${formattedTime}` };
        case 'llm':
          return { type: 'timestamp_llm', value: `LLM Timestamp: ${formattedTime}` };
        case 'tts':
          return { type: 'timestamp_tts', value: `TTS Timestamp: ${formattedTime}` };
        default:
          console.warn(`Unknown timestamp subtype: ${message.subtype}`);
          return null;
      }
    default:
      console.warn(`Unknown message type: ${message.type}`);
      return null;
  }
}

export function sendWebsocketConfigMsg(websocket: WebSocket, config: Constants.ConfigParams) {
  if (!websocket || websocket.readyState !== WebSocket.OPEN) {
    console.error('WebSocket is not open. Cannot send config message.');
    return;
  }

  // Send the config message
  const configMessage = {
    type: 'config',
    payload: config
  }
  
  websocket.send(JSON.stringify(configMessage));
}