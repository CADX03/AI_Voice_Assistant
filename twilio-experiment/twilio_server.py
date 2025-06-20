from flask import Flask, request, send_from_directory, make_response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client 
import os
import requests
import sys
import time

# Get the absolute path to the parent directory (LGP_12)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add voice-future-assistant to sys.path
sys.path.append(os.path.join(base_dir, 'voice-future-assistant'))

from components.gemini_llm import GeminiLLM
from components.azure_tts import AzureTTS
from components.eleven_labs_tts import ElevenLabsTTS
from components.azure_tts import AzureTTS
from components.google_cloud_tts import GoogleCloudTTS
from components.chatgpt_llm import AzureGPT4oLLM
app = Flask(__name__)

# Directory to store audio files
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

TWILIO_SENDER_PHONE_NUMBER = os.environ.get("TWILIO_SENDER_PHONE_NUMBER")

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    print("Warning: TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set. SMS sending will be disabled.")


tts = AzureTTS()

def warmup_services(llm):
    try:
        print("Warming up GeminiLLM and TTS...")
        # Dummy LLM call
        llm.process("Olá")
        try:
            tts.synthesize("Olá")
        except Exception as e:
            print(f"TTS warmup error: {e}")
        print("Warmup complete.")
    except Exception as e:
        print(f"Warmup failed: {e}")

import redis
import pickle

default_redis_url = "redis://localhost:6379/0"
redis_url = os.environ.get("REDIS_URL", default_redis_url)
redis_client = redis.from_url(redis_url)

REDIS_PREFIX = 'call_conversation:'

def get_llm_from_redis(call_sid):
    key = f"{REDIS_PREFIX}{call_sid}"
    data = redis_client.hget(key, "conversation_history")
    llm = GeminiLLM()
    if data:
        llm.conversation_history = pickle.loads(data)
    return llm

def save_llm_to_redis(call_sid, llm, resume=None):
    key = f"{REDIS_PREFIX}{call_sid}"
    redis_client.hset(key, mapping={
        "conversation_history": pickle.dumps(llm.conversation_history),
        "resume": resume or "",
        "transcript": ""
    })

def append_transcript_client(call_sid, text):
    transcript = "client: " + text + "\n"
    key = f"{REDIS_PREFIX}{call_sid}"
    redis_client.hset(key, mapping={
        "transcript": transcript
    })

def append_transcript_llm(call_sid, text):
    transcript = "llm: " + text +"\n"
    key = f"{REDIS_PREFIX}{call_sid}"
    redis_client.hset(key, mapping={
        "transcript": transcript
    })

def delete_llm_from_redis(call_sid):
    redis_client.delete(f"{REDIS_PREFIX}{call_sid}")

greeting_played = {}

@app.route("/twilio/voice", methods=['POST'])
def handle_twilio_voice():
    """Handle incoming Twilio webhook requests for voice calls."""
    call_sid = request.form.get("CallSid")
    transcription = request.form.get("SpeechResult")  # Transcription from Twilio's <Gather>
    print(call_sid)
    print(transcription)

    llm_duration_server = 0.0
    tts_duration_server = 0.0

    if transcription != None:
        append_transcript_client(call_sid, transcription)
    response = VoiceResponse()
    # Create and persist LLM conversation context now to avoid delay on first user input
    llm = get_llm_from_redis(call_sid)
    if llm.conversation_history == [] or llm.conversation_history is None:
        print("new conversation (greeting phase)")
        save_llm_to_redis(call_sid, llm)
        warmup_services(llm)

    if not transcription:
        # First interaction: Greet the user and start the conversation
        append_transcript_llm(call_sid, "greeting")
        greeting = llm.process("INtroduza-se ao cliente")
        greeting_audio = tts.synthesize(greeting)
        greeting_path = os.path.join(AUDIO_DIR, "greeting.mp3")
        with open(greeting_path, "wb") as f:
            f.write(greeting_audio)
        gather = response.gather(
            input="speech",
            action="/twilio/voice",
            speechTimeout="auto",
            language="pt-PT"
        )
        gather.play("https://twilio-backend-fragrant-brook-169.fly.dev/audio/greeting.mp3")
        flask_response = make_response(str(response))
        flask_response.headers['X-LLM-Duration'] = str(llm_duration_server) 
        flask_response.headers['X-TTS-Duration'] = str(tts_duration_server) 
        return flask_response

    try:
        start_llm = time.perf_counter()
        # Process the transcription using LLM
        last_message_flag, response_text, json = llm.process(transcription)
        end_llm = time.perf_counter()
        llm_duration_server = end_llm - start_llm
        # Save updated conversation state to Redis after each interaction
        save_llm_to_redis(call_sid, llm)
        if not response_text:
            response_text = "I'm sorry, I couldn't process your request. Could you repeat that?"
            
        if last_message_flag:
            response = VoiceResponse()
            # Goodbye message before hangup
            goodbye_text = "Obrigado pelo seu contacto. Tenha um excelente dia!"
            append_transcript_llm(call_sid, goodbye_text)
            start_tts_goodbye = time.perf_counter()
            goodbye_audio = tts.synthesize(goodbye_text)
            end_tts_goodbye = time.perf_counter()
            tts_duration_server = end_tts_goodbye - start_tts_goodbye
            if goodbye_audio:
                goodbye_filename = "goodbye.mp3"
                goodbye_path = os.path.join(AUDIO_DIR, goodbye_filename)
                with open(goodbye_path, "wb") as f:
                    f.write(goodbye_audio)
                response.play("https://twilio-backend-fragrant-brook-169.fly.dev/audio/goodbye.mp3")
            else:
                response.say(goodbye_text)
            response.hangup()
            save_llm_to_redis(call_sid, llm, resume=json)
            print(json)
            flask_response = make_response(str(response))
            flask_response.headers['X-LLM-Duration'] = str(llm_duration_server)
            flask_response.headers['X-TTS-Duration'] = str(tts_duration_server)
            return flask_response

        # Generate a response using TTS
        append_transcript_llm(call_sid, response_text)
        start_tts_regular = time.perf_counter()
        synthesized_audio = tts.synthesize(response_text)
        end_tts_regular = time.perf_counter()
        tts_duration_server = end_tts_regular - start_tts_regular
        if not synthesized_audio:
            response_text = "Lamento, ocorreu um problema ao gerar a resposta áudio. Pode repetir?"
            response = VoiceResponse()
            response.say(response_text)
            flask_response = make_response(str(response))
            flask_response.headers['X-LLM-Duration'] = str(llm_duration_server) # LLM duration is available
            flask_response.headers['X-TTS-Duration'] = str(tts_duration_server) # TTS duration of the failed attempt
            return flask_response
        # Save the synthesized audio to a file
        audio_filename = "response.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        with open(audio_path, "wb") as f:
            f.write(synthesized_audio)

        # Respond to Twilio with the audio file URL
        public_audio_url = f"https://twilio-backend-fragrant-brook-169.fly.dev/audio/{audio_filename}"
        response = VoiceResponse()
        gather_response = response.gather(
            input="speech",
            action="/twilio/voice",  # Redirect back to this endpoint for the next input
            speechTimeout="auto",
            language="pt-PT",        # Language for STT
            bargeIn=True
        )
        gather_response.play(public_audio_url)
        flask_response = make_response(str(response))
        flask_response.headers['X-LLM-Duration'] = str(llm_duration_server)
        flask_response.headers['X-TTS-Duration'] = str(tts_duration_server)
        return flask_response

    except Exception as e:
        print(f"Error processing Twilio voice request: {e}")
        response = VoiceResponse()
        response.say("An error occurred while processing your request. Please try again later.")
        flask_response = make_response(str(response))
        if llm_duration_server > 0:
            flask_response.headers['X-LLM-Duration'] = str(llm_duration_server)
        if tts_duration_server > 0: 
            flask_response.headers['X-TTS-Duration'] = str(tts_duration_server)
        return flask_response
@app.route("/audio/<filename>", methods=['GET'])
def serve_audio(filename):
    """Serve the audio file to Twilio."""
    return send_from_directory(AUDIO_DIR, filename)

@app.route("/twilio/call-status", methods=["POST"])
def call_status_callback():
    call_sid = request.form.get("CallSid")
    call_status = request.form.get("CallStatus")

    client_phone_number = request.form.get("From") 

    print(f"Call status update received: CallSid={call_sid}, CallStatus={call_status}, From={client_phone_number}")

    print(f"CallSid: {call_sid}, CallStatus: {call_status}")
    if call_status == "completed":
        delete_llm_from_redis(call_sid)
        print(f"Cleaned up conversation for CallSid: {call_sid}")

        if twilio_client and client_phone_number and TWILIO_SENDER_PHONE_NUMBER:
            feedback_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSePVGPXnMtGjqAL8d1pF1b6fq416BhPSxWOraa_UdyfSW1q5w/viewform?usp=sharing&ouid=114674244786666919488" 
            message_body = f"Obrigado pela sua chamada! Gostaríamos de ouvir o seu feedback: {feedback_form_url}"
            try:
                message = twilio_client.messages.create(
                    to=client_phone_number,
                    from_=TWILIO_SENDER_PHONE_NUMBER,
                    body=message_body
                )
                print(f"Sent feedback SMS to {client_phone_number}, Message SID: {message.sid}")
            except Exception as e:
                print(f"Error sending SMS to {client_phone_number}: {e}")
        elif not twilio_client:
            print("Twilio client not initialized. Cannot send SMS.")
        elif not client_phone_number:
            print("Client phone number not available from call status. Cannot send SMS.")
        elif not TWILIO_SENDER_PHONE_NUMBER:
            print("TWILIO_SENDER_PHONE_NUMBER (for sending SMS) not set in environment. Cannot send SMS.")

    return ("", 204)

if __name__ == "__main__":
    app.run(port=8000, debug=True)