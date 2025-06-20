import asyncio
from typing import Optional
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from pipeline import Finish
import websocket_msg_protocol as WebSocketProtocol

class WebSocketFinish(Finish):
    def __init__(self, websocket: Optional[WebSocket] = None):
        self.websocket = websocket # websocket connection to send audio data to the client

    async def finish(self, output: str):
        if self.websocket and self.websocket.client_state == WebSocketState.CONNECTED:
            await WebSocketProtocol.send_websocket_text(self.websocket, WebSocketProtocol.TextType.OUTPUT, output)
            await WebSocketProtocol.send_websocket_command(self.websocket, WebSocketProtocol.CommandType.EXIT)
