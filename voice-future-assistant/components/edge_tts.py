

import os
from typing import Optional
import edge_tts
from components.tts_base import TTSBase

# from https://github.com/rany2/edge-tts
# playground to test voices: https://text-to-speech.wingetgui.com/
# there is also a streaming mode for this library, that can be explored
class EdgeTTS(TTSBase):
    def __init__(self):
        super().__init__()
        self.voice = "pt-PT-RaquelNeural" # "pt-PT-RaquelNeural" or "pt-PT-DuarteNeural"
        self.rate = "+15%"
        self.pitch = "+0Hz"
        self.volume = "+0%"

    def synthesize(self, text: str) -> Optional[bytes]:
        try:
            output_path = "temp/edge_tts_output.mp3"
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume,
            )
            communicate.save_sync(output_path)
            with open(output_path, "rb") as f:
                audio_data = f.read()
            os.remove(output_path)
            return audio_data
        except Exception as e:
            print(f"Error using Edge TTS: {e}")
            return None

    def get_output_type(self):
        from pipeline import TTSOutputType
        return TTSOutputType.mp3
