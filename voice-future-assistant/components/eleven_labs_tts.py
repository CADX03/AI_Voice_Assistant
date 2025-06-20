import os
from typing import Optional
from elevenlabs import ElevenLabs, play
from dotenv import load_dotenv

load_dotenv()
from components.tts_base import TTSBase

class ElevenLabsTTS(TTSBase):
    def __init__(self):
        super().__init__()
        # Initialize the Eleven Labs client with the API key
        self.client = ElevenLabs(
            api_key=os.environ.get("ELEVEN_LABS_API_KEY")
        )
        self.voice_id = "aLFUti4k8YKvtQGXv0UO"  
        self.model_id = "eleven_multilingual_v2"

    def synthesize(self, text: str) -> Optional[bytes]:
        try:
            # Use the Eleven Labs client to convert text to speech
            audio_chunks = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format="mp3_44100_128",  # Specify the desired audio format
            )
            audio = b"".join(audio_chunks)
            
            print("Transcription successful!")
            return audio  # Return the audio data
        except Exception as e:
            print(f"Error in Eleven Labs TTS: {str(e)}")
            return None