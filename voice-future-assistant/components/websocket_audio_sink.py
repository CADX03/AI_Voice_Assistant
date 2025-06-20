import asyncio
from typing import Optional
from io import BytesIO
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from components.audio_sink_base import AudioSinkBase
from pipeline import AudioSource, TTSOutputType
import websocket_msg_protocol as WebSocketProtocol
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
import sys
import traceback

class WebSocketAudioSink(AudioSinkBase):
    def __init__(self, audio_source: Optional[AudioSource] = None, websocket: Optional[WebSocket] = None):
        super().__init__(audio_source, isWebsocket=True)
        self.websocket = websocket # websocket connection to send audio data to the client
        self.playback_active = False
        self.playback_task = None

    async def play_audio(self, audio_data: bytes, output_type: TTSOutputType) -> None:
        if not self.websocket:
            print("No WebSocket connection")
            return
        
        try: 
            self.playback_active = True

            # send audio data to client # when we send non text data, we assume its a new sound
            await WebSocketProtocol.send_websocket_audio(self.websocket, audio_data, output_type)
            print("Audio data sent to websocket")

            # calculate clip duration
            duration = self.audio_clip_duration(audio_data, output_type)
            print(f"Audio duration: {duration:.2f} seconds")

            # wait for the duration of the audio clip (done concurrently with other task (hence the new task), and can be cancelled during playblack
            self.playback_task = asyncio.create_task(self.wait_playback(duration))

        except Exception as e:
            print(f"Websocket send error: {str(e)}")
            self.playback_active = False
            await WebSocketProtocol.send_websocket_command(self.websocket, WebSocketProtocol.CommandType.EXIT)
            self.playback_task = None

    # wait for the duration of the audio clip
    async def wait_playback(self, duration: float):
        try:
            await asyncio.sleep(duration)
            print("Playback finished successfully")

            self.playback_active = False

        except asyncio.CancelledError: # if playback is intterrupted prematurely, due to client speaking over it, in stop_playback
            print("Playback interrupted by user speech...")
            self.playback_active = False
            
            await WebSocketProtocol.send_websocket_command(self.websocket, WebSocketProtocol.CommandType.STOP_AUDIO)

            raise # reraise the exception so it reaches play_audio

    # stop current audio playback
    async def stop_playback(self):
        self.playback_active = False
        if self.playback_task:
            self.playback_task.cancel() # cancel the playback task if it is running
            try: 
                await self.playback_task # wait for it to finish cancelling
            except asyncio.CancelledError:
                pass # ignore the exception that is raised when we cancel the playblack task

        await WebSocketProtocol.send_websocket_command(self.websocket, WebSocketProtocol.CommandType.STOP_AUDIO)
        print("Playback task stopped via webksocket")

    # indicates if currently playing audio
    async def is_playing(self) -> bool:
        return self.playback_active

    # stop the audio sink
    async def quit(self):
        await super().quit()
        if self.websocket:
            self.websocket.close() # closes the websocket connection
        if self.playback_task:
            self.playback_task.cancel()
            try:
                await self.playback_task
            except asyncio.CancelledError:
                pass

    #returns clip duration efficiently, or 0 on fail
    def audio_clip_duration(self, audio_data: bytes, output_type: TTSOutputType) -> float:
        try:
            audio_file = BytesIO(audio_data)
            print(f"Audio file size: {len(audio_data)} bytes with output type {output_type}")
            if output_type == TTSOutputType.mp3:
                audio = MP3(audio_file)
            else:  # assume WAV
                audio = WAVE(audio_file)
            return audio.info.length
        except Exception as e:
            print(f"Failed to calculate audio clip duration")
            exc_type, exc_val, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_val, exc_tb)

            # fallback for 16-bit PCM, 16kHz mono
            return len(audio_data) / (16000 * 2)