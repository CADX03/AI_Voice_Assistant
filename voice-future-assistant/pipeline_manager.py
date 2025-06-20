import asyncio
from typing import Dict, Optional, Type, List
from pipeline import AudioSource, STT, LLM, TTS, AudioSink, Finish
import websocket_msg_protocol as WebSocketProtocol

class PipelineManager:
    def __init__(self, config: Dict[str, Type]):
        self.audio_source: AudioSource = config["audio_source"]()
        self.stt: STT = config["stt"]()
        self.llm: LLM = config["llm"]()
        self.tts: TTS = config["tts"]()
        self.audio_sink: AudioSink = config["audio_sink"](self.audio_source)
        
        # setup finish function (if defined)
        finish_factory = config.get("finish", None)
        self.finish: Optional[Finish] = finish_factory() if finish_factory else None
        
        # For real-time interaction
        self.is_processing = False
        self.conversation_ended = False
        
    async def initialize(self):
        initial_response = None
        if self.llm:
            initial_response = self.llm.get_initial_response()
        if initial_response:
            response_audio = self.tts.synthesize(initial_response)
            if response_audio:
                await self.audio_sink.output_audio(response_audio, self.tts.get_output_type())

    async def handle_interim_result(self, text: str):
        """Handle interim results (during silence pauses)"""
        if self.is_processing or self.conversation_ended:
            return
            
        self.is_processing = True
        
        try:
            print(f"Processing interim: {text}")
            # Process the interim text
            _, response, _ = self.llm.process(text, is_interim=True)
            
            if response:
                if self.audio_sink.isWebsocket:
                    await WebSocketProtocol.send_websocket_text(self.audio_sink.websocket, WebSocketProtocol.TextType.TTS, response)
                # Synthesize and output the response
                response_audio = self.tts.synthesize(response)
                if response_audio:
                    await self.audio_sink.output_audio(response_audio, self.tts.get_output_type())
        finally:
            self.is_processing = False

    async def handle_final_result(self, text: str):
        """Handle final recognition results"""
        if self.conversation_ended:
            return
            
        print(f"Final result: {text}")
        
        # Process the final text
        last_response_flag, response, json_block = self.llm.process(text)
        
        if response:
            if self.audio_sink.isWebsocket:
                await WebSocketProtocol.send_websocket_text(self.audio_sink.websocket, WebSocketProtocol.TextType.TTS, response)
            # Synthesize and output the response
            response_audio = self.tts.synthesize(response)
            if response_audio:
                await self.audio_sink.output_audio(response_audio, self.tts.get_output_type())
                
        # Check if this is the end of the conversation
        if last_response_flag:
            self.conversation_ended = True
            print("\n\nConversa encerrada. Adeus!")
            print("conversation output:\n", json_block)
            if self.finish:
                await self.finish.finish(json_block)
            await self.stop()

    async def run(self):
        await self.initialize()

        print("\n" + "-"*50)
        print("\nEscutando... (diga algo ou 'sair' para encerrar)")
        
        # Start streaming mode if our STT supports it
        if hasattr(self.stt, 'start_streaming'):
            # Setup callbacks for streaming
            self.stt.start_streaming(
                on_final_result=lambda text: asyncio.create_task(self.handle_final_result(text)),
                on_interim_result=lambda text: asyncio.create_task(self.handle_interim_result(text))
            )
        
        # Main loop to continuously get audio
        while not self.conversation_ended:
            # Get audio bytes from source
            audio_data = await self.audio_source.get_audio()
            if not audio_data:
                await asyncio.sleep(0.1)
                continue

            # For streaming STT, this feeds the audio chunk into the stream
            # For legacy STT, this performs a full transcription
            text = self.stt.transcribe(audio_data)

            if self.audio_sink.isWebsocket:
                await WebSocketProtocol.send_websocket_text(self.audio_sink.websocket, WebSocketProtocol.TextType.STT, text)

            # Handle any text returned from the legacy method
            # (streaming mode will handle results through callbacks)
            if text and not hasattr(self.stt, 'start_streaming'):
                last_response_flag, response, json_block = self.llm.process(text)
                if response:
                    if self.audio_sink.isWebsocket:
                        await WebSocketProtocol.send_websocket_text(self.audio_sink.websocket, WebSocketProtocol.TextType.TTS, response)
                    response_audio = self.tts.synthesize(response)
                    if response_audio:
                        await self.audio_sink.output_audio(response_audio, self.tts.get_output_type())
                        
                if last_response_flag:
                    self.conversation_ended = True
                    print("\n\nConversa encerrada. Adeus!")
                    print("conversation output:\n", json_block)
                    if self.finish:
                        await self.finish.finish(json_block)
                    await self.stop()
                    break

    async def stop(self):
        # Stop streaming if it's active
        if hasattr(self.stt, 'stop_streaming'):
            self.stt.stop_streaming()
            
        await self.audio_source.stop()
        await self.audio_sink.stop()