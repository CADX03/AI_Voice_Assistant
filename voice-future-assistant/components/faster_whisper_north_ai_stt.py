import os
import tempfile
import torch
from typing import Optional
from faster_whisper import WhisperModel
from pipeline import STT

#benchmarks for faster-whisper custom pt models: https://github.com/TigreGotico/stt-benchmarks/blob/dev/README.md
# this is the best performing model
class FasterWhisperMyNorthAISTT(STT):
    def __init__(self):
        self.language = "pt"
        self.device = "cuda" if torch.cuda.is_available() else "cpu" # automatically use gpu if available
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        self.model_size = "Jarbas/faster-whisper-small-pt-MyNorthAI" # can be "Jarbas/faster-whisper-small-pt-MyNorthAI", "Jarbas/faster-whisper-medium-pt-MyNorthAI","Jarbas/faster-whisper-large-v3-pt-MyNorthAI" , among others (these are northAI specific models)
        self.beam_size = 1 # higher is better, but slower
        print(f"Loading Whisper model '{self.model_size}' on {self.device} ({self.compute_type})")

        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            # integrates the Silero VAD model to filter out parts of the audio without speech:
            segments, info = self.model.transcribe(
                tmp_path,
                beam_size=self.beam_size,
                language=self.language,
                vad_filter=True
            )

            result = " ".join([segment.text for segment in segments])
            print(f"Whisper transcription: {result}")
            return result
        
        except Exception as e:
            print(f"WhisperSTT error: {e}")
            return None
        finally:
            os.remove(tmp_path)