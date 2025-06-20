import asyncio
from collections import deque
import wave

from fastapi import WebSocket
from components.audio_source_base import AudioSourceBase
from typing import Optional
from pipeline import AudioSource

#NOTE: for this to work, it nedes to have:                
# await asyncio.sleep(self.chunk / self.rate) in capture_audio_clip

class WebSocketAudioSource(AudioSourceBase):
    def __init__(self, websocket: Optional[WebSocket] = None):
        super().__init__()
        self.websocket = websocket
        self.bytes_per_sample = 2 # assuming frontend sends 16-bit PCM (16bit -> self.bytes_per_sample bytes)
        self.start_recording()

    def start_recording(self):
        self.running = True
        self.recording_task = asyncio.create_task(self.record_audio_continuously())
        self.monitor_task = asyncio.create_task(self.monitor_audio())

    async def record_audio_continuously(self):
        try:
            while self.running:
                # Get whatever data is available from the WebSocket
                if not self.websocket:
                    print("No WebSocket connection")
                    await asyncio.sleep(0.1)  # wait for a bit if no websocket is available
                    continue

                try:
                    data = await self.websocket.receive_bytes()

                    # split data into chunks of self.chunk size
                    for i in range(0, len(data), self.chunk * self.bytes_per_sample):
                        chunk = data[i:i + self.chunk * self.bytes_per_sample]
                        if len(chunk) == self.chunk * self.bytes_per_sample:
                            self.append_to_buffer(chunk)

                        elif len(chunk) > 0:
                            # pad incomplete chunks with silence
                            padded_chunk = bytearray(chunk) + bytearray(self.chunk * self.bytes_per_sample - len(chunk))
                            self.append_to_buffer(bytes(padded_chunk))

                    await asyncio.sleep(0.01)  # collect a small bit of sound from stream (if it exists), and iteratively give back control to other tasks, so its not blocking

                except Exception as e:
                    # print(f"Websocket receive error: {str(e)}")
                    await asyncio.sleep(0.5)  # wait for a bit if there was an error

        except Exception as e:
            print(f"Websocket error in recording: {str(e)}")

    def get_sample_width(self):
        return self.bytes_per_sample
    
    async def stop(self):
        await super().stop()
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                print("Monitor task cancelled.")
        self.buffer.clear()  # flush it