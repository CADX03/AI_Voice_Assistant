from abc import ABC, abstractmethod
import asyncio
import traceback
from typing import Optional
from pipeline import TTS
from pipeline import TTSOutputType

# base class for audio sink, that can be used to output audio to different sinks, like speakers, websites, etc.
class TTSBase(TTS):
    def __init__(self, output_type=TTSOutputType.mp3):
        self.output_type = output_type

    # setup source of audio data, can be microphone, website, voip api, etc.
    @abstractmethod
    def synthesize(self, text: str) -> Optional[tuple[bytes,str]]:
        pass
    
    def get_output_type(self) -> str:
        return self.output_type
