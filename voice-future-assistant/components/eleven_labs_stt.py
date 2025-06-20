import os
import tempfile
import requests
from typing import Optional
from pipeline import STT

class ElevenLabsSTT(STT):
    def __init__(self):
        self.api_key = os.environ.get("ELEVEN_LABS_API_KEY")
        self.endpoint = "https://api.elevenlabs.io/v1/speech-to-text"
        self.model_id = "scribe_v1"  # Ensure this is a valid model ID

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        # Save raw audio data to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            temp_audio_file.write(audio_data)
            temp_audio_file_path = temp_audio_file.name

        try:
            # Construct the xi-api-key header
            headers = {
                "xi-api-key": self.api_key.strip()  # Ensure no leading/trailing spaces
            }
            print(f"xi-api-key Header: {headers['xi-api-key']}")  # Debugging the header

            # Prepare the file and data payload
            files = {
                "file": open(temp_audio_file_path, "rb")  # Open the audio file in binary mode
            }
            data = {
                "model_id": self.model_id
            }

            # Send the POST request
            print(f"Sending audio file: {temp_audio_file_path}")
            response = requests.post(self.endpoint, headers=headers, files=files, data=data)
            response.raise_for_status()

            # Parse the transcription response
            transcription = response.json().get("text", "")
            if not transcription:
                print("No transcription found in the response.")
                return None
            print(f"Transcription successful: {transcription}")
            return transcription
        except requests.RequestException as e:
            print(f"Error in Eleven Labs STT: {str(e)}")
            if e.response is not None:
                print(f"Response content: {e.response.text}")
            return None
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_audio_file_path):
                os.remove(temp_audio_file_path)