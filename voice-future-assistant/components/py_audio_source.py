import asyncio
from collections import deque
import pyaudio
import os
import wave
import tempfile
import numpy as np
from typing import Optional
from components.audio_source_base import AudioSourceBase

#NOTE: for this to work, it nedes to have:                
# await asyncio.sleep(0) in capture_audio_clip

# --- Audio Sources ---
class PyAudioSource(AudioSourceBase):
    def __init__(self):
        super().__init__()
        self.format = pyaudio.paInt16 # overwrite abstract class format
        self.pyaudio_obj = pyaudio.PyAudio()
        self.stream = None
        self.start_recording()

    # setup read audio data in a dedicated task (it happens all in the same thread, but tasks are scheduled in a way that they don't block each other)
    def start_recording(self):
        self.stream = self.pyaudio_obj.open(
            format=self.format, 
            channels=self.channels,
            rate=self.rate,
            input=True, 
            frames_per_buffer=self.chunk
        )
        self.running = True
        self.recording_task = asyncio.create_task(self.record_audio_continuously())
        self.monitor_task = asyncio.create_task(self.monitor_audio())

    # continuously read audio data from the stream and store in a buffer
    async def record_audio_continuously(self):
        try:
            while self.running:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.append_to_buffer(data)

                await asyncio.sleep(0) # collect a small bit of sound from stream (if it exists), and iteratively give back control to other tasks, so its not blocking
        except Exception as e:
            print(f"Unexpected error in recording: {str(e)}")

    def get_sample_width(self) -> int:
        return self.pyaudio_obj.get_sample_size(self.format)
    
    async def stop(self):
        await super().stop()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                print("Monitor task cancelled.")
                    
        self.pyaudio_obj.terminate()