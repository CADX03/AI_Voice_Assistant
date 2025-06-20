import os
from typing import Optional
import azure.cognitiveservices.speech as speechsdk
from components.tts_base import TTSBase
import tempfile
import io

os.environ["AZURE_CREDENTIALS_PATH"] = os.path.join(os.getcwd(), "api_keys/voice-future-azure.json")

class AzureTTS(TTSBase):
    def __init__(self):
        super().__init__()
        self.region = "westeurope"
        # Get path from environment variable
        credentials_path = os.environ.get("AZURE_CREDENTIALS_PATH")

        if not credentials_path or not os.path.exists(credentials_path):
            raise FileNotFoundError("Azure credentials file not found or AZURE_CREDENTIALS_PATH not set.")

        # Read the subscription key (expected to be a plain-text key)
        with open(credentials_path, 'r') as f:
            self.subscription = f.read().strip()

        self.speech_config = speechsdk.SpeechConfig(subscription=self.subscription, region="westeurope")
        self.voice_name = "pt-PT-FernandaNeural"
        self.speech_config.speech_synthesis_voice_name = self.voice_name

        # Define speaking rate mappings
        self.rate_values = {
            "slow": "-25.00%",
            "medium": "0%",
            "fast": "22.00%",
            "x-fast": "50.00%"
        }

        self.speaking_rate = self.rate_values.get("fast", 1.0)
        #self.speaking_rate = "medium"

    def synthesize(self, text: str, output_filename="output.mp3") -> bytes:
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )

        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=audio_config)

        ssml = f"""
        <speak version="1.0" xml:lang="pt-PT">
            <voice name="{self.voice_name}" style="cheerful">
                <prosody rate="{self.speaking_rate}" pitch="+2%" volume="default">{text}</prosody>
            </voice>
        </speak>
        """

        result = synthesizer.speak_ssml_async(ssml).get()

        #result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            #with open(output_filename, "rb") as f:
            #    audio_bytes = f.read()
            os.remove(output_filename)
            return result.audio_data
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_message = f"Speech synthesis canceled: {cancellation_details.reason}"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_message += f"\nError details: {cancellation_details.error_details}"
            raise RuntimeError(error_message)
