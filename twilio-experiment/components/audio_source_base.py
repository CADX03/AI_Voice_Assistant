import asyncio
from abc import ABC, abstractmethod
from collections import deque
import wave
import tempfile
import os
import numpy as np
from typing import Optional, List
from pipeline import AudioSource
import torch 
import torchaudio

# base class for audio source, that can be used to get audio from different sources
# handles buffer management, speech detection, clip capture, WAV creation
class AudioSourceBase(AudioSource):

    # setup source of audio data, can be microphone, website, voip api, etc.
    # NOTE: start_recording() must be called in the init of the derived class, for system to work
    @abstractmethod
    def start_recording(self):
        pass
    
    @abstractmethod
    def get_sample_width(self):
        pass

    def __init__(self):
        # audio format constants
        self.channels = 1
        self.rate = 16000
        self.chunk = 512

        # speech detection thresholds
        self.noise_threshold = 5000
        self.silence_threshold = 500 # silence threshold
        self.consecutive_frames = 1
        self.max_seconds = 15 # max recording time
        self.silence_timeout = 1 # seconds of silence before stopping
        self.min_speech_chunks = int(0.2 * self.rate / self.chunk) # minimum speech chunks to consider speech detected (0.2 seconds of audio)
        self.pre_buffer_seconds = 0.5 # seconds of audio to pre-buffer before starting audio clip
        
        #buffer and state
        self.buffer = deque(maxlen=int(self.rate / self.chunk * (self.max_seconds + 1)))  # buffer to store audio data at all times # it has enough space for max_chunks + 1 seconds of audio data
        self.running = False # flag to break up recording continuously
        self.recording_task = None # task that records audio continuously, needed to shut it down at the end

        # Event-based state
        self.speech_start_event = asyncio.Event() # event to signal when speech starts
        self.speech_stop_event = asyncio.Event() # event to signal when speech stops
        self.current_speech_start = None
        self.current_speech_end = None

        try: 
            # Prefer CPU for VAD unless GPU is specifically needed and configured
            self.vad_model, self.vad_utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                                            model='silero_vad',
                                                            force_reload=False, # Set to True first time or for updates
                                                            onnx=False) # Set to True if using ONNX runtime

            (self.get_speech_timestamps,
             self.save_audio,
             self.read_audio,
             self.VADIterator,
             self.collect_chunks) = self.vad_utils

            self.vad_threshold = 0.3
            print("Silero VAD model loaded successfully.")
        except Exception as e:
            print(f"Error loading Silero VAD model: {e}")
            self.vad_model = None 
            
    async def get_audio(self) -> bytes:
        # Check for speech
        if not await self.detect_speech():
            return b""  
        
        print("Speech detected, start capturing clip...")
        # record audio with silence detection
        temp_filename = tempfile.mktemp(dir=f'{os.getcwd()}/temp', suffix='.wav')

        frames = await self.capture_audio_clip()
        if not frames:
            print("Capturing clip failed or was cancelled.")
            return b""

        # write the clip to a temp file
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.get_sample_width())
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        print(f"Audio clip saved to {temp_filename}")
        # read the recorded audio data bytes, formatted for wav, and delete the temp file, send as bytes to stt api
        with open(temp_filename, 'rb') as f:
            audio_data = f.read()

        os.unlink(temp_filename)
        return audio_data

    #extract audio clip from the continuously filled buffer
    async def capture_audio_clip(self) -> Optional[bytes]:
        print("\nListening... (Press Ctrl+C to stop recording)")
        try: 
            # wait for speech to start
            await self.speech_start_event.wait()
            start_timestamp = self.current_speech_start
            # print(f"Speech started at timestamp {start_timestamp}")
            self.speech_start_event.clear()  # Reset for next capture

            # wait for speech to end
            await self.speech_stop_event.wait()
            end_timestamp = self.current_speech_end
            # print(f"Speech stopped at timestamp {end_timestamp}")
            self.speech_stop_event.clear()  # reset for next capture

            #extract clip from buffer, between start and end timestamps
            pre_buffer_start = start_timestamp - self.pre_buffer_seconds
            frames = []
            found_start = False

            for data, timestamp in self.buffer:
                if timestamp >= pre_buffer_start and not found_start:
                    found_start = True
                if found_start and timestamp <= end_timestamp:
                    if len(data) == self.chunk * self.get_sample_width():
                        frames.append(data)
                elif timestamp > end_timestamp:
                    break

            if len(frames) < self.min_speech_chunks:
                print("Not enough audio captured")
                return None

            print(f"Captured {len(frames)} chunks, total duration: {len(frames) * self.chunk / self.rate:.2f} seconds")
            return frames
        
        except KeyboardInterrupt:
            print("\nRecording stopped by user.")
            return False
        except Exception as e:
            print(f"\nRecording error: {str(e)}")
            return False
        
    # helper to append data with timestamp
    def append_to_buffer(self, data):
        timestamp = asyncio.get_event_loop().time()
        self.buffer.append((data, timestamp))
    
    # return if speech is present, based on when start_event is called from monitor_audio
    async def detect_speech(self) -> bool:
        # Wait for the speech start event
        await self.speech_start_event.wait()
        return True
    
    # continuously monitor the audio stream for speech detection, updating the speech start and stop events
    async def monitor_audio(self):
        if not self.vad_model:
            print("Silero VAD not loaded, falling back to basic energy detection (or implement fallback).")
            return
        
        silent_chunks = 0
        speech_active = False
        silence_start_time = None
        vad_state = None 
        
        while self.running:
            if not self.buffer:
                await asyncio.sleep(0.1) 
                continue
            
            try:
                data, timestamp = self.buffer[-1] 
                if len(data) != self.chunk * self.get_sample_width():
                    print(f"Skipping invalid chunk size: {len(data)}")
                    await asyncio.sleep(0.01)
                    continue

                audio_int16 = np.frombuffer(data, dtype=np.int16)
                audio_float32 = audio_int16.astype(np.float32) / 32768.0 # Normalize to [-1, 1]
                audio_tensor = torch.from_numpy(audio_float32)

                
                speech_prob = self.vad_model(audio_tensor, self.rate).item()

                is_speech = speech_prob >= self.vad_threshold

                
                if is_speech and not speech_active:
                    speech_active = True
                    self.current_speech_start = timestamp
                    self.speech_start_event.set()
                    silent_chunks = 0
                    silence_start_time = None

                elif not is_speech and speech_active:
                    if silence_start_time is None:
                        silence_start_time = timestamp

                    if (timestamp - silence_start_time) >= self.silence_timeout:
                        speech_active = False
                        self.current_speech_end = timestamp
                        self.speech_stop_event.set()
                        silent_chunks = 0
                        silence_start_time = None
                    else:
                        silent_chunks += 1 
                
                elif is_speech and speech_active:
                    silent_chunks = 0
                    silence_start_time = None
                
            except Exception as e:
                print(f"Monitor audio error: {str(e)}")
                await asyncio.sleep(0.01) 
                continue

            await asyncio.sleep(0.01)  
        
    async def stop(self):
        self.running = False
        if self.recording_task: 
            await asyncio.sleep(0.1)  # Give task a chance to exit
            self.recording_task.cancel()
            try:
                await self.recording_task
            except asyncio.CancelledError:
                print("Recording task cancelled.")