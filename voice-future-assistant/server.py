from contextlib import asynccontextmanager
import json
import traceback
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
from pipeline_manager import PipelineManager
from components.websocket_audio_source import WebSocketAudioSource
from components.websocket_audio_sink import WebSocketAudioSink
from components.websocket_finish import WebSocketFinish

from modelConfigs import COMPONENT_MAPPINGS, MODEL_MAPPINGS, LANGUAGE_MAPPINGS, TOTAL_STT, TOTAL_LLM, TOTAL_TTS
import websocket_msg_protocol as WebSocketProtocol

##
#  Module to load backend as a server, that can be accessed via WebSocket, to support LABS frontend page
##

### start FastAPI server
@asynccontextmanager
async def lifespan(app: FastAPI):
    # nothing to do on server setup
    yield

    # on server shutdown
    # for connection in connections:
    #     await connection.close()
    
app = FastAPI(lifespan=lifespan)

### Add CORS middleware (for WebSocket connections if the frontend and backend are on different domains)
origins = [
    "http://localhost:5173",  # Local development
    "https://voice-future-labs.fly.dev",  # Production frontend domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/call") # endpoint for websocket connection
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Wait for api config message from frontend
    frontend_config = None
    try:
        data = await websocket.receive_text()
        message = json.loads(data)
        if message.get('type') == 'config':
            frontend_config = message.get('payload', {})
        else:
            print(f"Expected config message, received: {message}")
    except Exception as e:
        print(f"Error receiving config: {e}")

    final_stt, final_llm, final_tts = await setup_apis_from_config(websocket, frontend_config)
    
    # configure pipeline with WebSocket components, and apis from frontend config (or default if not provided in frontend)
    config = {
        "audio_source": lambda: WebSocketAudioSource(websocket),
        "stt": final_stt,
        "llm": final_llm,
        "tts": final_tts,
        "audio_sink": lambda audio_source=None: WebSocketAudioSink(audio_source, websocket),
        "finish": lambda: WebSocketFinish(websocket)
    }

    pipeline = PipelineManager(config)

    try:
        await pipeline.run()
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()

    finally:
        await pipeline.stop()
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
        print("WebSocket connection closed")


#setup configs based on frontend config, or default if not provided or invalid
async def setup_apis_from_config(websocket, config):

    final_stt = MODEL_MAPPINGS["default"]["stt"]
    final_llm = MODEL_MAPPINGS["default"]["llm"]
    final_tts = MODEL_MAPPINGS["default"]["tts"]

    print(isinstance(config, dict))
    if not isinstance(config, dict):
        await WebSocketProtocol.send_websocket_error(websocket, "No valid configuration provided, using default")
        print("no valid config provided, using default")
        return final_stt, final_llm, final_tts
    
    if ("stt" in config and isinstance(config["stt"], int) and 0 <= config["stt"] < TOTAL_STT):
        final_stt = COMPONENT_MAPPINGS["stt"][config["stt"]]
    else:
        await WebSocketProtocol.send_websocket_error(websocket, "Invalid STT configuration or none provided, resetting to default")
        print("invalid stt config or none provided, resetting to default")
    
    if ("llm" in config and isinstance(config["llm"], int) and 0 <= config["llm"] < TOTAL_LLM):
        final_llm = COMPONENT_MAPPINGS["llm"][config["llm"]]
    else:
        await WebSocketProtocol.send_websocket_error(websocket, "Invalid LLM configuration or none provided, resetting to default")
        print("invalid llm config or none provided, resetting to default")

    if ("tts" in config and isinstance(config["tts"], int) and 0 <= config["tts"] < TOTAL_TTS):
        final_tts = COMPONENT_MAPPINGS["tts"][config["tts"]]
    else:
        await WebSocketProtocol.send_websocket_error(websocket, "Invalid TTS configuration or none provided, resetting to default")
        print("invalid tts config or none provided, resetting to default")
    
    print(f"STT: {final_stt}, LLM: {final_llm}, TTS: {final_tts}")
    return final_stt, final_llm, final_tts

# Health check endpoint, for debug
@app.get("/health")
async def health_check():
    return {"status": "ok"}