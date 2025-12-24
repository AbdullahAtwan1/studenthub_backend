# app/routers/chat.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.models.content import Conversation, Message
from app.schemas.content_schemas import MessageCreate, MessageOut

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/conversations")
def create_conversation(participants: str, db: Session = Depends(get_db)):
    conv = Conversation(participants=participants)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/conversations/{conv_id}/messages", response_model=List[MessageOut])
def get_messages(conv_id: int, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter_by(conversation_id=conv_id).order_by(Message.created_at).all()
    return msgs

@router.post("/messages", response_model=MessageOut)
def send_message(payload: MessageCreate, db: Session = Depends(get_db)):
    msg = Message(**payload.dict())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

# --- Simple WebSocket manager (in-memory)
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conv_id: int):
        await websocket.accept()
        self.active_connections.setdefault(conv_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, conv_id: int):
        if conv_id in self.active_connections:
            self.active_connections[conv_id].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, conv_id: int, message: str):
        for ws in self.active_connections.get(conv_id, []):
            await ws.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{conv_id}")
async def websocket_endpoint(websocket: WebSocket, conv_id: int, db: Session = Depends(get_db)):
    conv_id = int(conv_id)
    await manager.connect(websocket, conv_id)
    try:
        while True:
            data = await websocket.receive_text()
            # optionally save to DB as message
            # NOTE: websockets can't use sync DB session easily here; this is a simple echo + broadcast
            await manager.broadcast(conv_id, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, conv_id)
