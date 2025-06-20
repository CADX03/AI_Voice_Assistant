from abc import ABC, abstractmethod
import asyncio
import traceback
from typing import Optional
from pipeline import AudioSource, AudioSink, TTSOutputType

# base class for audio sink, that can be used to output audio to different sinks, like speakers, websites, etc.
class AudioSinkBase(AudioSink):
    def __init__(self, audio_source: Optional[AudioSource] = None, isWebsocket: bool = False):
        self.audio_source = audio_source
        self.is_speaking = False
        self.interruption_delay = 1 # seconds to wait before stopping playback if user starts speaking
        self.isWebsocket = isWebsocket # flag tos ignal if we are using a websocket connection or not, to handle updates to frontend

    # setup source of audio data, can be microphone, website, voip api, etc.
    @abstractmethod
    def play_audio(self, audio_data: bytes, output_type: TTSOutputType) -> None:
        pass
    
    @abstractmethod
    def stop_playback(self):
        pass

    @abstractmethod
    def is_playing(self) -> bool:
        pass
    
    async def output_audio(self, audio_data: bytes, output_type: TTSOutputType) -> None:
        try:
            #load response audio playback
            self.is_speaking = True
            await self.play_audio(audio_data, output_type)
            
            if self.audio_source:
                speech_start_time = None
                while await self.is_playing() and self.is_speaking: # while playback is active
                    if await self.audio_source.detect_speech(): # if we detect new speech from user
                        # if user only started speaking now, we start a timer
                        if speech_start_time is None:
                            speech_start_time = asyncio.get_event_loop().time()
                            print("User speech detected during playback...")
                        # if user has been talking for more than x seconds, we stop playback, and let him talk
                        elif asyncio.get_event_loop().time() - speech_start_time > self.interruption_delay:
                            print("Stopping playback due to client interruption...")
                            await self.stop_playback()
                            self.is_speaking = False
                            print("Chatbot interrupted by user speech")
                            break
                    else: # if user is not talking, we reset the timer, and wait for a bit to check again
                        speech_start_time = None
                    await asyncio.sleep(0.1)
            self.is_speaking = False

        except Exception as e:
            print(f"Error to play the audio: {str(e)}")
            traceback.print_exc()
    
    async def stop(self):
        print("Stopping call received")
        if self.is_speaking:
            print("Stopping playback...")
            await self.stop_playback()
            self.is_speaking = False

    async def quit(self):
        await self.stop()
