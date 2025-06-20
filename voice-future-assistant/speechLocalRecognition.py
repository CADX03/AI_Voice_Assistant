import os
import time
import tempfile
import pygame
import sys
import wave
import pyaudio
import speech_recognition as sr
from gtts import gTTS
import pyttsx3

def text_to_speech(text, voice_name="pt-PT", speech_rate="medium", language_code="pt-PT"):
    """Convert text to speech using either gTTS or pyttsx3 and play it using pygame."""
    try:
        # Map speech rates to numeric values
        rate_values = {
            "slow": 0.75,
            "medium": 1.0,
            "fast": 1.25,
            "x-fast": 1.5
        }
        
        rate = rate_values.get(speech_rate, 1.0)
        
        # Try to use gTTS first (online)
        try:
            tts = gTTS(text=text, lang=language_code.split('-')[0], slow=(rate < 1.0))
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
                tts.save(temp_filename)
            
            # Adjust playback speed for 'fast' and 'x-fast' (gTTS only supports normal/slow)
            # This is handled by pygame's playback speed - not implemented here
            
            # Play the audio file using pygame
            pygame.mixer.init()
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            pygame.mixer.quit()
            os.unlink(temp_filename)
            
        except Exception as e:
            print(f"gTTS failed, falling back to pyttsx3: {str(e)}")
            
            # Fallback to pyttsx3 (offline)
            engine = pyttsx3.init()
            
            # Set voice - note that voice selection is system-dependent
            voices = engine.getProperty('voices')
            # Try to find a Portuguese voice
            pt_voice = None
            for voice in voices:
                if 'portuguese' in voice.name.lower() or 'portugal' in voice.name.lower():
                    pt_voice = voice.id
                    break
            
            if pt_voice:
                engine.setProperty('voice', pt_voice)
            
            # Set speaking rate
            engine_rate = engine.getProperty('rate')
            engine.setProperty('rate', int(engine_rate * rate))
            
            # Speak the text
            engine.say(text)
            engine.runAndWait()
        
    except Exception as e:
        print(f"Error in text-to-speech conversion: {str(e)}")
        print(text)

def record_audio(output_file, max_seconds=10, silence_timeout=1):
    """Record audio from microphone to a file with auto-stop on silence."""
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    
    audio = pyaudio.PyAudio()
    
    try:
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        
        print("\nListening... (Press Ctrl+C to stop recording)")
        
        frames = []
        silent_chunks = 0
        max_chunks = int(RATE / CHUNK * max_seconds)
        silence_threshold = 500  
        
        for i in range(0, max_chunks):
            data = stream.read(CHUNK)
            frames.append(data)
            
            audio_data = wave.struct.unpack(f"{CHUNK}h", data)
            audio_level = max(abs(x) for x in audio_data)
            
            if audio_level < silence_threshold:
                silent_chunks += 1
                if silent_chunks > int(silence_timeout * RATE / CHUNK):
                    print("Silence detected, stopping recording.")
                    break
            else:
                silent_chunks = 0
                
            if i % 10 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()
                
        print("\nRecording complete.")
        
        stream.stop_stream()
        stream.close()
        
        wf = wave.open(output_file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return True
    
    except KeyboardInterrupt:
        print("\nRecording stopped by user.")
        return False
    except Exception as e:
        print(f"\nError during recording: {str(e)}")
        return False
    finally:
        audio.terminate()

def transcribe_audio(audio_file_path, language_code='pt-PT'):
    """Transcribe audio using SpeechRecognition library with multiple engines."""
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file_path) as source:
            print(f"Processing audio file: {audio_file_path}")
            # Adjust for ambient noise and record
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)
            
        # Try multiple recognition engines in order of preference
        transcription_text = None
        errors = []
        
        # 1. Try Google Speech Recognition (requires internet)
        try:
            print("Attempting Google Speech Recognition...")
            transcription_text = recognizer.recognize_google(
                audio_data, 
                language=language_code
            )
        except sr.RequestError as e:
            errors.append(f"Google Speech Recognition service error: {e}")
        except sr.UnknownValueError:
            errors.append("Google Speech Recognition could not understand audio")
        
        # 2. If Google fails and Sphinx is available, try Sphinx (offline)
        if transcription_text is None:
            try:
                # Sphinx uses different language codes
                sphinx_lang = 'pt' if language_code.startswith('pt') else language_code
                print("Attempting Sphinx Recognition (offline)...")
                transcription_text = recognizer.recognize_sphinx(
                    audio_data,
                    language=sphinx_lang
                )
            except (sr.UnknownValueError, LookupError) as e:
                errors.append(f"Sphinx error: {e}")
        
        # 3. Try other providers if needed (Whisper, etc.)
        
        if transcription_text:
            print(f"Transcription successful: {transcription_text}")
            return transcription_text
        else:
            print("No transcription results returned. Errors:")
            for error in errors:
                print(f"- {error}")
            return None
            
    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        return None

def speech_to_text():
    """Record audio and transcribe it using local/online recognition."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    try:
        print("Starting audio recording...")
        if not record_audio(temp_filename):
            print("Recording failed or was cancelled.")
            return None
        
        # Process the audio file directly with SpeechRecognition
        transcription = transcribe_audio(temp_filename)
        return transcription
        
    finally:
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
            print(f"Deleted temporary file: {temp_filename}")

def listen_and_recognize(language_code='pt-PT', timeout=5, phrase_time_limit=None):
    """Use SpeechRecognition to listen directly from microphone and recognize."""
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("\nAdjusting for ambient noise... Please wait.")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("\nListening... (Speak now)")
            
            # Listen for audio input
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                print("Recording complete. Processing...")
            except sr.WaitTimeoutError:
                print("Listening timed out. No speech detected.")
                return None
            
        # Try to recognize using Google's speech recognition
        try:
            print("Recognizing...")
            text = recognizer.recognize_google(audio, language=language_code)
            print(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None
            
    except Exception as e:
        print(f"Error in speech recognition: {str(e)}")
        return None

# Alternative direct listening function that can be used instead of the record+transcribe flow
def quick_speech_to_text():
    """Directly listen and transcribe without saving to file."""
    return listen_and_recognize(timeout=5, phrase_time_limit=10)