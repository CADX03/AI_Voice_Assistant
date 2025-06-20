import time
from typing import Optional
import boto3
import tempfile
import os
from pipeline import STT
import requests

os.environ["AWS_SHARED_CREDENTIALS_FILE"] = os.path.join(os.getcwd(), "api_keys/voice-future-aws.json")

class AmazonTranscribe(STT):
    def __init__(self):
        self.client = boto3.client('transcribe', region_name='eu-west-2')
        self.language_code = 'pt-PT'
        self.bucket_name = 'voice-future-recordings-lgp'
        self.chunk_size = 10 * 1024 * 1024  # 10 MB

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        temp_filename = tempfile.mktemp(suffix='.wav')
        with open(temp_filename, 'wb') as f:
            f.write(audio_data)

        
        s3_uri = self._upload_to_s3(temp_filename)
        if not s3_uri:
            os.unlink(temp_filename)
            print("Failed to upload to S3.")
            return None
            
        transcription = self._transcribe_audio(s3_uri)
            
        os.unlink(temp_filename)
        return transcription if transcription else "Desculpe, pode continuar."

        
    def _upload_to_s3(self, file_path: str) -> Optional[str]:
        s3_client = boto3.client('s3', region_name='eu-west-2')
        try:
            object_name = os.path.basename(file_path)
            s3_client.upload_file(file_path, self.bucket_name, object_name)
            return f"s3://{self.bucket_name}/{object_name}"
        except Exception as e:
            print(f"Error with S3: {str(e)}")
            return None
        
    def _transcribe_audio(self, audio_file_uri: str) -> Optional[str]:
        try:
            # Generate a unique transcription job name
            job_name = f"transcription-job-{int(time.time())}"

            # Start the transcription job
            self.client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': audio_file_uri},
                MediaFormat='wav', 
                LanguageCode=self.language_code
            )

            # Wait for the transcription job to complete
            while True:
                response = self.client.get_transcription_job(TranscriptionJobName=job_name)
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                if status in ['COMPLETED', 'FAILED']:
                    break
                time.sleep(0.3)  # Polling interval

            # Check if the transcription was successful
            if status == 'COMPLETED':
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                transcript_response = requests.get(transcript_uri)
                transcript_json = transcript_response.json()
                transcript_text = transcript_json['results']['transcripts'][0]['transcript']
                return transcript_text
            else:
                print("Transcription job failed.")
                return None

        except Exception as e:
            print(f"Error in Amazon Transcribe: {str(e)}")
            return None