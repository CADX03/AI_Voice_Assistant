import os
import queue
import threading
import time
import asyncio
from google.cloud import speech
from typing import Optional, Callable, Iterator, List, Dict, Any
from pipeline import STT

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "api_keys/voice-future-google.json")

class GoogleCloudStreamingSTT(STT):
    def __init__(self):
        self.client = speech.SpeechClient()
        self.encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        self.sample_rate_hertz = 16000
        self.language_code = 'pt-PT'
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=self.encoding,
                sample_rate_hertz=self.sample_rate_hertz,
                language_code=self.language_code,
                enable_automatic_punctuation=True,
            ),
            interim_results=True,
        )
        self.streaming_active = False
        self.audio_queue = queue.Queue()
        self.streaming_thread = None
        self.latest_transcript = ""
        self.on_final_result = None
        self.on_interim_result = None
        
        # For silence detection
        self.last_speech_time = time.time()
        self.silence_threshold = 1.0  # 1 second of silence before triggering response
        self.processing_interim = False
        
        # Useful for LLM integration
        self.partial_transcripts = []
        self.final_transcript = ""

    def start_streaming(self, 
                       on_final_result: Optional[Callable[[str], None]] = None,
                       on_interim_result: Optional[Callable[[str], None]] = None):
        """Starts the recgnition process"""
        if self.streaming_active:
            return
        
        self.streaming_active = True
        self.on_final_result = on_final_result
        self.on_interim_result = on_interim_result
        self.partial_transcripts = []
        self.final_transcript = ""
        self.last_speech_time = time.time()
        self.processing_interim = False
        
        self.streaming_thread = threading.Thread(target=self._stream_recognition)
        self.streaming_thread.daemon = True
        self.streaming_thread.start()
        
    def stop_streaming(self) -> str:
        """Return the final transcription"""
        if not self.streaming_active:
            return self.latest_transcript
        
        self.streaming_active = False
        self.audio_queue.put(None)  
        if self.streaming_thread:
            self.streaming_thread.join(timeout=5)
            self.streaming_thread = None
            
        return self.latest_transcript
    
    def process_audio_chunk(self, audio_chunk: bytes):
        """Processes audio in real time"""
        if self.streaming_active:
            self.audio_queue.put(audio_chunk)
            
            current_time = time.time()
            elapsed_silence = current_time - self.last_speech_time
            
            # Debug current state
            if self.partial_transcripts:
                print(f"[DEBUG] Current partial transcript: {' '.join(self.partial_transcripts)}")
                print(f"[DEBUG] Elapsed silence: {elapsed_silence:.2f}s (threshold: {self.silence_threshold}s)")
            
            if (elapsed_silence >= self.silence_threshold and 
                self.partial_transcripts and 
                not self.processing_interim):
                
                self.processing_interim = True
                
                interim_text = " ".join(self.partial_transcripts)
                print(f"\n[DEBUG] Sending interim text to LLM: \"{interim_text}\"\n")
                
                if self.on_interim_result and interim_text:
                    self.on_interim_result(interim_text)
    
    def _stream_recognition(self):
        def generate_requests() -> Iterator[speech.StreamingRecognizeRequest]:
            while self.streaming_active:
                # Get the next audio chunk from the queue
                audio_chunk = self.audio_queue.get()
                
                # If None received, the stream is done
                if audio_chunk is None:
                    break
                
                # First request contains the configuration
                if not hasattr(generate_requests, "first_request_sent"):
                    yield speech.StreamingRecognizeRequest(
                        streaming_config=self.streaming_config
                    )
                    generate_requests.first_request_sent = True
                
                # Following requests contain audio data
                yield speech.StreamingRecognizeRequest(audio_content=audio_chunk)
        
        try:
            responses = self.client.streaming_recognize(config=self.streaming_config, requests=generate_requests())
            
            for response in responses:
                if not response.results:
                    continue
                
                # Update last speech time whenever we receive a response
                self.last_speech_time = time.time()
                
                # Get the result
                result = response.results[0]
                transcript = result.alternatives[0].transcript
                
                # Handle interim results
                if not result.is_final:
                    print(f"[DEBUG] New interim result: \"{transcript}\"")
                    # If this is an update to the existing partial transcript
                    if self.partial_transcripts:
                        self.partial_transcripts[-1] = transcript
                    else:
                        self.partial_transcripts.append(transcript)
                    
                    # Reset the processing flag so we can process this chunk after silence
                    self.processing_interim = False
                
                # Handle final results
                else:
                    self.latest_transcript = transcript
                    self.final_transcript = transcript
                    
                    print(f"\n[DEBUG] FINAL TRANSCRIPT: \"{transcript}\"\n")
                    print(f"[DEBUG] Sending final text to LLM")
                    
                    # Clear partial transcripts as we now have a final one
                    self.partial_transcripts = []
                    
                    # Reset the processing flag
                    self.processing_interim = False
                    
                    if self.on_final_result:
                        self.on_final_result(transcript)
                        
        except Exception as e:
            print(f"Error in streaming recognition: {str(e)}")
    
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """        
        Handles both batch mode and streaming mode depending on the current state.
        - If streaming is active, it audio in real time
        - If streaming is not active, it audio in batch mode
        """
        if self.streaming_active:
            # When streaming is active, just feed the audio chunk and return any available transcript
            self.process_audio_chunk(audio_data)
            
            # Check if we have a final transcript
            if self.final_transcript:
                transcript = self.final_transcript
                self.final_transcript = ""  # Clear it to avoid returning it again
                print(f"[DEBUG] Returning final transcript from transcribe(): \"{transcript}\"")
                return transcript
            
            return None  # Nothing final yet
        else:
            # Legacy batch mode processing
            try:
                audio = speech.RecognitionAudio(content=audio_data)
                config = speech.RecognitionConfig(
                    encoding=self.encoding,
                    sample_rate_hertz=self.sample_rate_hertz,
                    language_code=self.language_code
                )

                response = self.client.recognize(config=config, audio=audio)
                transcription_text = "".join(result.alternatives[0].transcript for result in response.results)
                
                if transcription_text:
                    print(f"Transcription successful: {transcription_text}")
                    return transcription_text
                else:
                    print("No transcription results returned.")
                    return "Não percebi o que disse. Repita em poucas palavras, sem pedir desculpa ou confirmar que vai repetir. Começe a falar logo."
            
            except Exception as e:
                print(f"Error in transcription: {str(e)}")
                return None