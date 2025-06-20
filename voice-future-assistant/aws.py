import boto3
import os
import time
import tempfile
import pygame
import urllib.request
import json
import pyaudio
import wave
import sys
import numpy as np
import threading

is_chatbot_speaking = False
speech_filename = None
audio_content = None
pyaudio_Object = None
is_recording = False

def detect_speech(threshold=700, consecutive_frames=3):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    
    global audio_content, pyaudio_Object
    if audio_content is None:
        try:
            pyaudio_Object = pyaudio.PyAudio()
            audio_content = pyaudio_Object.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
        except Exception as e:
            print(f"Error initializing audio stream: {str(e)}")
            return False
    
    try:
        frames_above_threshold = 0
        
        for _ in range(consecutive_frames):
            data = audio_content.read(CHUNK, exception_on_overflow=False)
            
            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_level = np.abs(audio_data).max()
            
            if audio_level > threshold:
                frames_above_threshold += 1
            else:
                frames_above_threshold = 0
                
        return frames_above_threshold >= consecutive_frames
        
    except Exception as e:
        print(f"Error detecting speech: {str(e)}")
        audio_content = None  
        return False

def is_speaking():
    global is_chatbot_speaking
    try:
        if is_chatbot_speaking and pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            return True
        else:
            return False
    except:
        return is_chatbot_speaking

def stop_speech():
    global is_chatbot_speaking
    is_chatbot_speaking = False
    
    try:
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            
        time.sleep(0.1)
    except Exception as e:
        print(f"Error stopping speech: {str(e)}")

def text_to_speech(text, speech_rate="medium", voice_id="Ines", region_name='eu-west-2'):
    global is_chatbot_speaking, speech_filename
    
    try:
        is_chatbot_speaking = False
        
        rate_values = {
            "slow": "slow",
            "medium": "medium", 
            "fast": "fast",
            "x-fast": "x-fast"
        }
        
        rate = rate_values.get(speech_rate, "medium")
        
        polly_client = boto3.client('polly', region_name=region_name)
        
        ssml_text = f"""<speak>
            <prosody rate="{rate}">
                {text}
            </prosody>
        </speak>"""
        
        response = polly_client.synthesize_speech(
            Text=ssml_text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine='neural',
            TextType='ssml'  
        )
        
        if speech_filename and os.path.exists(speech_filename):
            try:
                os.unlink(speech_filename)
            except:
                pass
            speech_filename = None
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_filename = temp_file.name
            temp_file.write(response['AudioStream'].read())
        
        speech_filename = temp_filename
        
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except:
            pass
        
        if not pygame.get_init():
            pygame.init()
            
        time.sleep(0.2)
        
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
        time.sleep(0.1)
        
        try:
            pygame.mixer.music.load(temp_filename)
            is_chatbot_speaking = True
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy() and is_chatbot_speaking:
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Error playing audio: {str(e)}")
        
        try:
            pygame.mixer.quit()
        except:
            pass
        
        if os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
                speech_filename = None
            except:
                pass
        
        is_chatbot_speaking = False
        
    except Exception as e:
        print(f"TTS conversion failed: {str(e)}")
        print(text)
        is_chatbot_speaking = False

def speech_to_text(region_name='eu-west-2'):
    global is_recording, audio_content, pyaudio_Object
    is_recording = True
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    try:
        print("Starting audio recording...")
        if not record_audio(temp_filename):
            print("Recording failed or was cancelled.")
            return None
        
        s3_uri = upload_to_s3(temp_filename, region_name=region_name)
        if not s3_uri:
            print("Failed to upload to S3.")
            return None
        
        transcription = transcribe_audio(s3_uri, region_name=region_name)
        return transcription
        
    finally:
        is_recording = False
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
            print(f"Deleted temporary file: {temp_filename}")

def record_audio(output_file, max_seconds=15, silence_timeout=2.5):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    
    global audio_content, pyaudio_Object
    
    if audio_content is None:
        pyaudio_Object = pyaudio.PyAudio()
        audio_content = pyaudio_Object.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    try:
        print("\nListening... (Press Ctrl+C to stop recording)")
        
        buffer_size = int(0.5 * RATE / CHUNK)
        ring_buffer = []
        
        for _ in range(buffer_size):
            data = audio_content.read(CHUNK, exception_on_overflow=False)
            ring_buffer.append(data)
        
        frames = list(ring_buffer)
        silent_chunks = 0
        speech_detected = False
        max_chunks = int(RATE / CHUNK * max_seconds)
        silence_threshold = 500
        
        min_speech_chunks = int(0.3 * RATE / CHUNK)
        speech_chunks = 0
        
        for i in range(0, max_chunks):
            data = audio_content.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            audio_data = wave.struct.unpack(f"{CHUNK}h", data)
            audio_level = max(abs(x) for x in audio_data)
            
            if audio_level >= silence_threshold:
                speech_chunks += 1
                silent_chunks = 0
                speech_detected = True
            else:
                silent_chunks += 1
                if speech_detected and speech_chunks > min_speech_chunks and silent_chunks > int(silence_timeout * RATE / CHUNK):
                    print("Silence detected after speech, stopping recording.")
                    break
            
            if i % 10 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()
            
            if i % 20 == 0 and i > 0: 
                if not speech_detected or speech_chunks <= min_speech_chunks: 
                    return False
                else: 
                    stop_speech()

        print("\nRecording complete.")
                
        if not speech_detected or speech_chunks <= min_speech_chunks:
            print("No meaningful speech detected.")
            return False
        
        wf = wave.open(output_file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio_Object.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return True
    
    except KeyboardInterrupt:
        print("\nRecording stopped by user.")
        return False
    except Exception as e:
        print(f"\nRecording error: {str(e)}")
        return False

def upload_to_s3(file_path, bucket_name='voice-future-recordings', object_name=None, region_name='eu-west-2'):
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    s3_client = boto3.client('s3', region_name=region_name)
    
    try:
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"Using existing bucket: {bucket_name}")
        except Exception as e:
            if 'Not Found' in str(e) or 'NoSuchBucket' in str(e):
                print(f"Bucket {bucket_name} not found. Creating it now in {region_name}...")
                
                if region_name == 'us-east-1':
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region_name}
                    )
                print(f"Bucket {bucket_name} created successfully in {region_name}.")
            else:
                raise e
        
        print(f"Uploading file to s3://{bucket_name}/{object_name}...")
        s3_client.upload_file(file_path, bucket_name, object_name)
        return f"s3://{bucket_name}/{object_name}"
    except Exception as e:
        print(f"Error with S3: {str(e)}")
        return None

def transcribe_audio(audio_file_uri, region_name='eu-west-2', language_code='pt-PT'):
    transcribe = boto3.client('transcribe', region_name=region_name)
    
    job_name = f"transcription-job-{int(time.time())}"
    
    try:
        print(f"Starting transcription job: {job_name}")
        print(f"Media URI: {audio_file_uri}")
        
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': audio_file_uri},
            MediaFormat='wav',
            LanguageCode=language_code
        )
        
        print("Waiting for transcription to complete...")
        while True:
            response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            if status in ['COMPLETED', 'FAILED']:
                break
                
            print("Transcription in progress...")
            time.sleep(2)
        
        if status == 'COMPLETED':
            transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
            
            print(f"Fetching transcript from: {transcript_uri}")
            with urllib.request.urlopen(transcript_uri) as response:
                transcript_json = json.loads(response.read())
                
            transcription_text = transcript_json['results']['transcripts'][0]['transcript']
            print(f"Transcription successful: {transcription_text}")
            return transcription_text
        else:
            print(f"Transcription failed: {response['TranscriptionJob']['FailureReason']}")
            return "Desculpe, pode prosseguir onde estava."
            
    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        return None

def cleanup():
    global audio_content, pyaudio_Object, is_recording
    
    stop_speech()
    
    if not is_recording and audio_content is not None:
        try:
            audio_content.stop_stream()
            audio_content.close()
            audio_content = None
        except:
            pass
    
    if not is_recording and pyaudio_Object is not None:
        try:
            pyaudio_Object.terminate()
            pyaudio_Object = None
        except:
            pass
    
    if speech_filename and os.path.exists(speech_filename):
        try:
            os.unlink(speech_filename)
        except:
            pass