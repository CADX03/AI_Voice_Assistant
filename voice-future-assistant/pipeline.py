from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum

class TTSOutputType(str, Enum):
    mp3 = 'mp3'
    wav = 'wav'

# generate audio bytes
class AudioSource(ABC):
    # get audio in bytes (from website, microphone, voip api)
    @abstractmethod
    async def get_audio(self) -> bytes:
        pass

    #stop getting audio
    @abstractmethod
    async def stop(self):
        pass

#convert speech to text
class STT(ABC):
    @abstractmethod
    #convert audio in bytes to text
    async def transcribe(self, audio: bytes) -> Optional[str]:
        pass

#process text and generate responses
#returns 
# - bool: True if last response of conversation
# - str: the response text
# - str: json block with end of conversation info, if it is the end of conversation
class LLM(ABC):
    @abstractmethod
    #do the thing
    async def process(self, text: str) -> tuple[bool, str, str]:
        pass

#convert text to speech
class TTS(ABC):
    @abstractmethod
    #do the thing
    def synthesize(self, text: str) -> Optional[tuple[bytes,str]]:
        pass

#send audio back to source
class AudioSink(ABC):
    @abstractmethod
    #send audio bytes to website, speaker, voip api,..
    async def output_audio(self, audio: bytes, output_type: TTSOutputType) -> None:
        pass

    @abstractmethod
    #stop playing audio
    async def stop(self):
        pass

# any additional cleanup of pipeline, if needed
# useful to signal end of conversation to frontend, and do some cleanup
class Finish(ABC):
    @abstractmethod
    async def finish(self):
        pass