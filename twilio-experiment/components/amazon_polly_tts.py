import os
import boto3
from typing import Optional
from pipeline import TTS

os.environ["AWS_SHARED_CREDENTIALS_FILE"] = os.path.join(os.getcwd(), "api_keys/voice-future-aws.json")

class AmazonPolly(TTS):
    def __init__(self):
        self.client = boto3.client('polly', region_name='eu-west-2')
        self.rate_values = {
            "slow": "slow",
            "medium": "medium",
            "fast": "fast",
            "x-fast": "x-fast"
        }
        self.default_voice = "Ines"
        self.default_rate = "medium"

    def synthesize(self, text: str, speech_rate: str = "medium", voice_id: Optional[str] = None) -> bytes:
        """
        Synthesizes speech from text using Amazon Polly.
        """
        voice_id = voice_id or self.default_voice
        rate = self.rate_values.get(speech_rate, self.default_rate)

        # Create SSML text with the specified speech rate
        ssml_text = f"""<speak>
            <prosody rate="{rate}">
                {text}
            </prosody>
        </speak>"""

        try:
            # Call Amazon Polly to synthesize speech
            response = self.client.synthesize_speech(
                Text=ssml_text,
                OutputFormat="mp3",
                VoiceId=voice_id,
                Engine="neural",
                TextType="ssml"
            )

            # Return the audio content as bytes
            return response["AudioStream"].read()

        except Exception as e:
            print(f"Error in Amazon Polly TTS: {str(e)}")
            return b""

    def save_to_file(self, audio_content: bytes, output_filename: str) -> None:
        """
        Saves the synthesized audio content to a file.
        """
        try:
            with open(output_filename, "wb") as audio_file:
                audio_file.write(audio_content)
            print(f"Audio saved to {output_filename}")
        except Exception as e:
            print(f"Error saving audio to file: {str(e)}")