from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

from app.db.session import engine
from app.db.base_class import Base
import app.models

from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.face_router import router as face_router

from app.websocket.chat_ws import chat_websocket, global_chat_websocket

app = FastAPI(title="StudentHub Backend")

# ======================
# Startup
# ======================
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")

# ======================
# Routers (REST APIs)
# ======================
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router)
app.include_router(face_router)

# ======================
# Static files
# ======================
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ======================
# Chat WebSocket
# ======================
@app.websocket("/ws/chat/{conversation_id}/{user_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    conversation_id: int,
    user_id: int
):
    await chat_websocket(websocket, conversation_id, user_id)

# ======================
# 🔥 Global WebSocket
# ======================
@app.websocket("/ws/global-chat/{user_id}")
async def websocket_global_chat_endpoint(
    websocket: WebSocket,
    user_id: int
):
    await global_chat_websocket(websocket, user_id)


# ======================
# Root
# ======================
@app.get("/")
def root():
    return {"message": "StudentHub backend is running successfully!"}
