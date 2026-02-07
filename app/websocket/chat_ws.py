from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List

# =====================================================
# Conversation-based WS (موجود عندك)
# =====================================================
class ConnectionManager:
    def __init__(self):
        # conversation_id -> list of sockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, conversation_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(conversation_id, []).append(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def broadcast(self, conversation_id: int, message: dict):
        if conversation_id in self.active_connections:
            for ws in self.active_connections[conversation_id]:
                await ws.send_json(message)


manager = ConnectionManager()

# =====================================================
# 🔥 Global WS (NEW)
# =====================================================
class GlobalConnectionManager:
    def __init__(self):
        # user_id -> list of sockets
        self.active_users: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_users.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_users:
            if websocket in self.active_users[user_id]:
                self.active_users[user_id].remove(websocket)
            if not self.active_users[user_id]:
                del self.active_users[user_id]

    async def send_to_user(self, user_id: int, message: dict):
        if user_id in self.active_users:
            for ws in self.active_users[user_id]:
                await ws.send_json(message)


global_manager = GlobalConnectionManager()


# =====================================================
# Conversation WebSocket endpoint handler
# =====================================================
async def chat_websocket(
    websocket: WebSocket,
    conversation_id: int,
    user_id: int
):
    await manager.connect(conversation_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)


# =====================================================
# Global WebSocket endpoint handler
# =====================================================
async def global_chat_websocket(
    websocket: WebSocket,
    user_id: int
):
    await global_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        global_manager.disconnect(user_id, websocket)
