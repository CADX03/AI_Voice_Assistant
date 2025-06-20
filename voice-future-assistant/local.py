import asyncio
import traceback
from pipeline_manager import PipelineManager
from components.py_audio_source import PyAudioSource
from components.google_cloud_stt import GoogleCloudSTT
from components.google_cloud_stt_rt import GoogleCloudStreamingSTT
from components.gemini_llm import GeminiLLM
from components.google_cloud_tts import GoogleCloudTTS
from components.pygame_audio_sink import PyGameAudioSink
from components.azure_stt import AzureSTT
from components.azure_tts import AzureTTS

##
#  Module to load backend locally, with microphone and speaker from PC, for testing
##

# pipeline config for local testing
LOCAL_CONFIG = {
    "audio_source": PyAudioSource,
    "stt": AzureSTT,
    "llm": GeminiLLM,
    "tts": GoogleCloudTTS,
    "audio_sink": PyGameAudioSink
}

async def run_local_pipeline():
    pipeline = None
    try:
        pipeline = PipelineManager(LOCAL_CONFIG)
        await pipeline.run()
    except SystemExit as e:
        print(str(e))
    except KeyboardInterrupt:
        print("\n\nConversa interrompida pelo utilizador. Adeus!")
    except Exception as e:
        print(f"\n\nErro durante a conversa: {str(e)}")
        print(traceback.format_exc())
    finally:
        if pipeline is not None:
            await pipeline.stop()

def start_local():
    asyncio.run(run_local_pipeline())


