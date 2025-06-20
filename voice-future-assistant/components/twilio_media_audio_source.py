import asyncio
from fastapi import WebSocket
from typing import Optional
from pipeline import AudioSource
from components.audio_source_base import AudioSourceBase

class TwilioMediaAudioSource(AudioSourceBase):
    def __init__(self, websocket: Optional[WebSocket] = None):
        super().__init__()
        self.websocket = websocket
        self.audio_queue = asyncio.Queue()
        self.running = True
        self.recording_task = asyncio.create_task(self.record_audio_continuously())
        self.monitor_task = asyncio.create_task(self.monitor_audio())

    async def record_audio_continuously(self):
        try:
            while self.running:
                if not self.websocket:
                    await asyncio.sleep(0.1)
                    continue
                try:
                    # Wait for media events from Twilio
                    data = await self.websocket.receive_text()
                    message = json.loads(data)
                    event_type = message.get('event')
                    if event_type == 'media':
                        audio_b64 = message['media']['payload']
                        audio_bytes = base64.b64decode(audio_b64)
                        await self.audio_queue.put(audio_bytes)
                    elif event_type == 'stop':
                        self.running = False
                        break
                except Exception as e:
                    print(f"TwilioMediaAudioSource receive error: {e}")
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"TwilioMediaAudioSource error: {e}")

    async def get_audio(self) -> bytes:
        # Get the next audio chunk from the queue
        try:
            audio_bytes = await self.audio_queue.get()
            return audio_bytes
        except Exception as e:
            print(f"TwilioMediaAudioSource get_audio error: {e}")
            return b""

    async def stop(self):
        self.running = False
        if self.recording_task:
            self.recording_task.cancel()
            try:
                await self.recording_task
            except asyncio.CancelledError:
                print("Recording task cancelled.")
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                print("Monitor task cancelled.")
        self.audio_queue = asyncio.Queue()

    def start_recording(self):
        self.running = True
        self.recording_task = asyncio.create_task(self.record_audio_continuously())
        self.monitor_task = asyncio.create_task(self.monitor_audio())

    def get_sample_width(self):
        # Twilio sends 16-bit PCM audio
        return 2
