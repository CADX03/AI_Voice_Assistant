import asyncio
from fastapi import WebSocket
from typing import Optional
from pipeline import AudioSource, AudioSink
from components.audio_sink_base import AudioSinkBase
import base64

class TwilioMediaAudioSink(AudioSinkBase):
    def __init__(self, audio_source: Optional[AudioSource] = None, websocket: Optional[WebSocket] = None):
        super().__init__(audio_source)
        self.websocket = websocket
        self.playback_active = False
        self.playback_task = None

    async def play_audio(self, audio_data: bytes):
        if not self.websocket:
            print("No WebSocket connection for TwilioMediaAudioSink")
            return
        try:
            self.playback_active = True
            # Twilio expects base64-encoded audio payloads in 'media' events
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            message = {
                'event': 'media',
                'media': {
                    'payload': audio_b64
                }
            }
            await self.websocket.send_json(message)
        except Exception as e:
            print(f"TwilioMediaAudioSink play_audio error: {e}")
        finally:
            self.playback_active = False

    async def is_playing(self) -> bool:
        return self.playback_active

    async def stop_playback(self):
        self.playback_active = False

    async def quit(self):
        await super().quit()
        if self.websocket:
            await self.websocket.close()
        if self.playback_task:
            self.playback_task.cancel()
            try:
                await self.playback_task
            except asyncio.CancelledError:
                pass
