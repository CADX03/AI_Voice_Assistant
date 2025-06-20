from enum import Enum
import json
from starlette.websockets import WebSocketState
from pipeline import TTSOutputType
# module to define the websocket message protocol
# for sending messages to the client via websocket

# NOTE: three types of messages are defined:
# 1. command: for sending commands to the client - "EXIT", "STOP_AUDIO"
# 2. data: for sending data to the client (e.g., text, timestamp, audio_metadata, etc.)
    # "data" type messages can be further divided into:
    # 2.1 text: for sending text results from processes - "stt","tts","output"
    # 2.2 timestamp: for sending timestamps-"stt","llm","tts"

# 3. binary: for sending binary data (e.g., audio data)

class TextType(str, Enum):
    STT = "stt"
    TTS = "tts"
    OUTPUT = "output"

class TimestampType(str, Enum):
    STT = "stt"
    LLM = "llm"
    TTS = "tts"

class CommandType(str, Enum):
    EXIT = "EXIT"
    STOP_AUDIO = "STOP_AUDIO"

## "command" type messages ('EXIT', 'STOP_AUDIO', etc)
async def send_websocket_command(websocket, command: CommandType):
    if websocket and websocket.client_state == WebSocketState.CONNECTED:
        structured_msg = {
            "type": "command", 
            "payload": {
                "value": command
            }
        }
        await websocket.send_text(json.dumps(structured_msg))
        print(f"Command sent to websocket")

## "data" type messages (text, timestamp, etc)
## "type" is the subtype of the data (stt, tts, output, etc)
async def send_websocket_text(websocket, type: TextType, message: str):
    if websocket and websocket.client_state == WebSocketState.CONNECTED:
        structured_msg = {
            "type": "data", 
            "payload": {
                "type": "text",
                "subtype": type,
                "value": message
            }
        }
        await websocket.send_text(json.dumps(structured_msg))
        print(f"Text sent to websocket")

## "type" is the subtype of the timestamp (stt, llm, tts, etc)
async def send_websocket_timestamp(websocket, type: TimestampType, number: float):
    if websocket and websocket.client_state == WebSocketState.CONNECTED:
        structured_msg = {
            "type": "data", 
            "payload": {
                "type": "timestamp",
                "subtype": type,
                "value": number
            }
        }
        await websocket.send_text(json.dumps(structured_msg))
        # print(f"Number sent to websocket: {structured_msg}")

## binary messages (audio data)
async def send_websocket_audio(websocket, audio_data: bytes, audio_type: TTSOutputType):
    if websocket and websocket.client_state == WebSocketState.CONNECTED:
        structured_msg = {
            "type": "audio",
            "payload": {
                "type": "audio_metadata",
                "mime_type": f"audio/{audio_type}"
            }
        }
        await websocket.send_text(json.dumps(structured_msg)) # metadata with audio type before sending audio
        await websocket.send_bytes(audio_data)
        print(f"Audio bytes sent to websocket")

async def send_websocket_error(websocket, error_message: str):
    if websocket and websocket.client_state == WebSocketState.CONNECTED:
        structured_msg = {
            "type": "error", 
            "payload": {
                "value": error_message
            }
        }
        await websocket.send_text(json.dumps(structured_msg))
        print(f"Error sent to websocket")