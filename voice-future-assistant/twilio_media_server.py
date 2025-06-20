import base64
import json
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from pipeline_manager import PipelineManager
from components.twilio_media_audio_source import TwilioMediaAudioSource
from components.twilio_media_audio_sink import TwilioMediaAudioSink
from components.google_cloud_stt import GoogleCloudSTT
from components.gemini_llm import GeminiLLM
from components.google_cloud_tts import GoogleCloudTTS

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/twilio-media")
async def twilio_media_stream(websocket: WebSocket):
    await websocket.accept()
    print("Twilio Media Stream WebSocket connected.")
    # Set up the pipeline config for Twilio Media Streams
    config = {
        "audio_source": lambda: TwilioMediaAudioSource(websocket),
        "stt": GoogleCloudSTT,
        "llm": GeminiLLM,
        "tts": GoogleCloudTTS,
        "audio_sink": lambda audio_source=None: TwilioMediaAudioSink(audio_source, websocket),
    }
    pipeline = PipelineManager(config)
    try:
        await pipeline.run()
    except Exception as e:
        print(f"Twilio pipeline error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await pipeline.stop()
        if websocket.client_state.value == 1:  # WebSocketState.CONNECTED
            await websocket.close()
        print("Twilio Media Stream WebSocket closed.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
