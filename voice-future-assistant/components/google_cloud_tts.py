from google.cloud import texttospeech
from typing import Optional
from components.tts_base import TTSBase
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "api_keys/voice-future-google.json")

class GoogleCloudTTS(TTSBase):
    def __init__(self):
        super().__init__()
        self.client = texttospeech.TextToSpeechClient()
        self.rate_values = {
            "slow": 0.75,
            "medium": 1.0,
            "medium-fast": 1.1,
            "fast": 1.25,
            "x-fast": 1.5
        }
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="pt-PT",
            name="pt-PT-Wavenet-C"
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=self.rate_values.get("medium-fast", 1.0)
        )

    def synthesize(self, text: str) -> bytes:

        synthesis_input = texttospeech.SynthesisInput(text=text)

        response = self.client.synthesize_speech(input=synthesis_input, voice=self.voice, audio_config=self.audio_config)
        return response.audio_content