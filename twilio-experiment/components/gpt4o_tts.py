import os
import base64
import asyncio
from openai import AsyncAzureOpenAI
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from pipeline import TTS

os.environ["AZURE_GPT_CREDENTIALS"] = os.path.join(os.getcwd(), "api_keys/voice-future-azure-gpt.json")

class AzureOpenAIRealtimeTTS(TTS):
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("AZURE_GPT_KEY"),
            api_version="2024-10-01-preview",
        )
        self.model = "gpt-4o-realtime-preview"
        self.connection = None

    async def initialize(self):
        self.connection = await self.client.beta.realtime.connect(model=self.model)
        await self.connection.session.update(session={"modalities": ["text", "audio"]})

        if self.connection.session:
            print("Connected to Azure OpenAI Realtime TTS")
        else:
            print("Failed to connect to Azure OpenAI Realtime TTS")

    def synthesize(self, text: str) -> bytes:
        return asyncio.run(self._synthesize_async(text))

    async def _synthesize_async(self, text: str) -> bytes:
        if not self.connection:
            await self.initialize()

        await self.connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            }
        )

        await self.connection.response.create()

        audio_chunks = []

        async for event in self.connection:
            if event.type == "response.audio.delta":
                chunk = base64.b64decode(event.delta)
                audio_chunks.append(chunk)
            elif event.type == "response.done":
                break

        return b"".join(audio_chunks) if audio_chunks else None