import os
import tempfile
from google.cloud import speech
from google.cloud import storage
from typing import Optional
from pipeline import STT


### 
# NOTE: Soon to be deprecated in favour of GoogleCloudStreamingSTT. Streaming gives faster results
###

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "api_keys/voice-future-google.json")

class GoogleCloudSTT(STT):
    def __init__(self):
        self.client = speech.SpeechClient()
        self.encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        self.sample_rate_hertz = 16000
        self.language_code = 'pt-PT'
        self.bucket_name = 'voice-future-recordings'
        self.chunk_size = 10 * 1024 * 1024  # 10 MB

    def transcribe(self, audio_data: bytes) -> Optional[str]:

        temp_filename = tempfile.mktemp(suffix='.wav')
        with open(temp_filename, 'wb') as f:
            f.write(audio_data)

        file_size = os.path.getsize(temp_filename)
        if file_size > self.chunk_size:
            gcs_uri = self._upload_to_gcs(temp_filename)
            if not gcs_uri:
                os.unlink(temp_filename)
                print("Failed to upload to GCS.")
                return None
            
            transcription = self._transcribe_audio(gcs_uri)
        else:
            transcription = self._transcribe_audio(temp_filename)

        os.unlink(temp_filename)
        return transcription if transcription else "Desculpe, pode continuar."

    def _upload_to_gcs(self, file_path: str) -> Optional[str]:
        storage_client = storage.Client()
        try:
            # NOTE: No need to keep checking if bucket already exists, i think?
            # try:
            #     bucket = storage_client.get_bucket(self.bucket_name)
            #     print(f"Using existing bucket: {self.bucket_name}")
            # except Exception:
            #     print(f"Bucket {self.bucket_name} not found. Creating it now...")
            #     bucket = storage_client.create_bucket(self.bucket_name)
            #     print(f"Bucket {self.bucket_name} created successfully.")
            bucket = storage_client.bucket(self.bucket_name)
            object_name = os.path.basename(file_path)
            blob = bucket.blob(object_name)
            print(f"Uploading file to gs://{self.bucket_name}/{object_name}...")

            blob.upload_from_filename(file_path)
            return f"gs://{self.bucket_name}/{object_name}"
        except Exception as e:
            print(f"Error with GCS: {str(e)}")
            return None

    def _transcribe_audio(self, audio_file_uri: str) -> Optional[str]:
        try:
            # print(f"Starting transcription for: {audio_file_uri}")

            if audio_file_uri.startswith("gs://"):
                audio = speech.RecognitionAudio(uri=audio_file_uri)
            else:
                with open(audio_file_uri, "rb") as audio_file:
                    content = audio_file.read()
                audio = speech.RecognitionAudio(content=content)

            config = speech.RecognitionConfig(
                encoding=self.encoding,
                sample_rate_hertz=self.sample_rate_hertz,
                language_code=self.language_code,
                speech_contexts=[
                    speech.SpeechContext(
                        phrases=[
                            "arroba", "ponto", "traço", "underscore",
                            "gmail.com", "hotmail.com", "outlook.com", "saposp.pt",  # common domains in PT
                            "email", "endereço de email",  # give context
                            "nome arroba dominio ponto com",  # generic structure
                            "joao ponto silva ponto 1507 arroba gmail ponto com",  # examples
                            "cliente ponto suporte arroba empresa ponto pt"
                        ],
                        boost=20.0 # boost recognition of these patterns
                    )
                ]
            )

            response = self.client.recognize(config=config, audio=audio)
            transcription_text = "".join(result.alternatives[0].transcript for result in response.results)

            if not transcription_text:
                print("No transcription results returned.")
                return "Não percebi o que disse. Repita em poucas palavras, sem pedir desculpa ou confirmar que vai repetir. Começe a falar logo."
        

            print(f"Transcription successful: {transcription_text}")
            return transcription_text

        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            return None
