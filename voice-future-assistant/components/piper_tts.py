import subprocess
from pathlib import Path
from typing import Optional
from components.tts_base import TTSBase, TTSOutputType

# there is also a streaming mode for this library, that can be explored

class PiperTTS(TTSBase):
    def __init__(self):
        self.model_path = Path("/app/piper_voices/pt_PT-tugão-medium.onnx") # no other models available for pt-pt
        self.output_wav = Path("/app/temp/piper_output.wav")

        super().__init__(output_type=TTSOutputType.wav) # define output type sent to frontend

        if not self.model_path.exists():
            raise FileNotFoundError("Piper model file is missing.")

    def synthesize(self, text: str) -> Optional[bytes]:
        try:
            cmd = [
                "piper",
                "--model", str(self.model_path),
                "--output_file", str(self.output_wav)
            ]

            subprocess.run(cmd, input=text.encode("utf-8"), check=True)

            if self.output_wav.exists():
                with open(self.output_wav, "rb") as f:
                    return f.read()
            else:
                print("Piper did not generate output.wav.")
                return None

        except subprocess.CalledProcessError as e:
            print(f"Piper CLI error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
