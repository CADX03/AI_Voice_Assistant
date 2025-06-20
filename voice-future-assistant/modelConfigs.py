# Module for mapping configuration indexes in the frontend to respective APIs and classes in backend

# STT imports
from components.google_cloud_stt import GoogleCloudSTT
from components.google_cloud_stt_rt import GoogleCloudStreamingSTT
from components.amazon_transcribe_stt import AmazonTranscribe
from components.eleven_labs_stt import ElevenLabsSTT
from components.azure_stt import AzureSTT
from components.faster_whisper_default_stt import FasterWhisperDefaultSTT
from components.faster_whisper_north_ai_stt import FasterWhisperMyNorthAISTT

# LLM imports
from components.gemini_llm import GeminiLLM

# TTS imports
from components.google_cloud_tts import GoogleCloudTTS
from components.amazon_polly_tts import AmazonPolly
from components.eleven_labs_tts import ElevenLabsTTS
from components.chatgpt_llm import AzureGPT4oLLM
from components.azure_tts import AzureTTS
from components.gpt4o_tts import AzureOpenAIRealtimeTTS
from components.piper_tts import PiperTTS
from components.edge_tts import EdgeTTS

# add new API components here vvvvvv
COMPONENT_MAPPINGS = {
    "stt": [
        GoogleCloudSTT,
        AmazonTranscribe,
        ElevenLabsSTT,
        AzureSTT,
        FasterWhisperDefaultSTT,
        FasterWhisperMyNorthAISTT
        # add other STT
    ],

    "llm": [
        GeminiLLM,
        AzureGPT4oLLM
        # Add other LLM
    ],

    "tts": [
        GoogleCloudTTS,
        AmazonPolly,
        ElevenLabsTTS,
        AzureTTS,
        PiperTTS,
        EdgeTTS
        # Add other TTS
    ]
}

TOTAL_STT = len(COMPONENT_MAPPINGS["stt"])
TOTAL_LLM = len(COMPONENT_MAPPINGS["llm"])
TOTAL_TTS = len(COMPONENT_MAPPINGS["tts"])

# default model components
MODEL_MAPPINGS = {
    "default": {
        "stt": GoogleCloudSTT,
        "llm": GeminiLLM,
        "tts": ElevenLabsTTS
    }
}

# #####################
# IGNORE FOR NOW
# #####################

# if we want to support multiple languages in the future, its the language that must define the APIs available for it
# are we ever going to use this?
LANGUAGE_MAPPINGS = {
    "pt": {
        "stt": None,
        "llm": None,
        "tts": None
    },
    "en": {
        "stt": None,
        "llm": None,
        "tts": None
    },
    # Other languages
}
