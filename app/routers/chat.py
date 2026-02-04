from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.chat import Chat
from app.models.content import Message

router = APIRouter(prefix="/chats", tags=["Chat"])

@router.get("/")
def get_chats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    chats = db.query(Chat).filter(
        (Chat.user1_id == current_user.id) |
        (Chat.user2_id == current_user.id)
    ).all()

    result = []
    for chat in chats:
        last_msg = db.query(Message)\
            .filter(Message.conversation_id == chat.id)\
            .order_by(Message.created_at.desc())\
            .first()

        result.append({
            "id": chat.id,
            "user_id": chat.user2_id if chat.user1_id == current_user.id else chat.user1_id,
            "last_message": last_msg.content if last_msg else None,
            "updated_at": chat.updated_at,
            "unread_count": 0
        })

    return result
