import os
import tempfile
from typing import Optional
import azure.cognitiveservices.speech as speechsdk
from pipeline import STT

os.environ["AZURE_CREDENTIALS_PATH"] = os.path.join(os.getcwd(), "api_keys/voice-future-azure.json")

class AzureSTT(STT):
    def __init__(self):
        self.region = "westeurope"
        self.language = "pt-PT"

        # Get path from environment variable
        credentials_path = os.environ.get("AZURE_CREDENTIALS_PATH")

        if not credentials_path or not os.path.exists(credentials_path):
            raise FileNotFoundError("Azure credentials file not found or AZURE_CREDENTIALS_PATH not set.")

        # Read the subscription key (expected to be a plain-text key)
        with open(credentials_path, 'r') as f:
            self.subscription = f.read().strip()

        self.speech_config = speechsdk.SpeechConfig(subscription=self.subscription, region=self.region)
        self.speech_config.speech_recognition_language = self.language

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        temp_filename = tempfile.mktemp(suffix=".wav")
        with open(temp_filename, 'wb') as f:
            f.write(audio_data)

        try:
            audio_input = speechsdk.AudioConfig(filename=temp_filename)
            recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_input)

            result = recognizer.recognize_once_async().get()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"Azure Transcription successful: {result.text}")
                return result.text

            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("Azure STT: No speech recognized.")
                return "Não percebi o que disse. Repita em poucas palavras, sem pedir desculpa ou confirmar que vai repetir. Começe a falar logo."

            else:
                print(f"Azure STT: Recognition failed with reason: {result.reason}")
                return None

        except Exception as e:
            print(f"Azure STT error: {e}")
            return None

        finally:
            os.unlink(temp_filename)
