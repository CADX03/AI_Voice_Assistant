import asyncio
import os
import tempfile
import pygame
from typing import Optional
from pipeline import AudioSource, TTSOutputType
from components.audio_sink_base import AudioSinkBase

class PyGameAudioSink(AudioSinkBase):
    def __init__(self, audio_source: Optional[AudioSource] = None):
        super().__init__(audio_source)
        pygame.mixer.init(
            frequency=44100, 
            size=-16, 
            channels=2, 
            buffer=2048
        )
        self.temp_filename = None
    
    #playback audio data
    async def play_audio(self, audio_data: bytes, output_type: TTSOutputType) -> None:
        #create temp file to incoming audio data
        self.temp_filename = tempfile.mktemp(suffix=f"'.{output_type}'")
        with open(self.temp_filename, 'wb') as temp_file:
            temp_file.write(audio_data)

        #load response audio playback
        pygame.mixer.music.load(self.temp_filename)
        pygame.mixer.music.play()

        # cleanup temp file
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)
    
    # stop current audio playback
    async def stop_playback(self):
        pygame.mixer.music.stop()

        if self.temp_filename and os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)
            self.temp_filename = None

    # check if audio is currently playing
    async def is_playing(self) -> bool:
        return pygame.mixer.music.get_busy()
    
    # stop the audio sink
    async def quit(self):
        await super().quit()
        pygame.mixer.quit()

