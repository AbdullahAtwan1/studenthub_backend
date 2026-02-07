from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.conversation_participant import ConversationParticipant
from app.models.message import Message
from app.websocket.chat_ws import manager
from app.websocket.chat_ws import manager, global_manager
from app.models.user import User



router = APIRouter(prefix="/chat", tags=["Chat"])


# ======================================================
# Create or get direct conversation
# ======================================================
@router.post("/create")
def create_conversation(
    user1_id: int,
    user2_id: int,
    db: Session = Depends(get_db)
):
    if user1_id == user2_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot create conversation with yourself"
        )

    # 🔍 check if direct conversation already exists
    conversation = (
        db.query(Conversation)
        .join(ConversationParticipant)
        .filter(Conversation.type == "direct")
        .group_by(Conversation.id)
        .having(func.count(ConversationParticipant.id) == 2)
        .having(
            func.sum(
                ConversationParticipant.user_id.in_([user1_id, user2_id])
            ) == 2
        )
        .first()
    )

    if conversation:
        return {"conversation_id": conversation.id}

    # ➕ create new conversation
    conversation = Conversation(type="direct")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    participants = [
        ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user1_id
        ),
        ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user2_id
        ),
    ]

    db.add_all(participants)
    db.commit()

    return {"conversation_id": conversation.id}


# ======================================================
# Send message (REST + WebSocket broadcast)
# ======================================================
@router.post("/send")
async def send_message(
    conversation_id: int,
    sender_id: int,
    content: str,
    db: Session = Depends(get_db)
):
    participant = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == sender_id
    ).first()

    if not participant:
        raise HTTPException(status_code=403, detail="Not allowed")

    message = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content.strip()
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    payload = {
        "id": message.id,
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }

    # بث داخل المحادثة
    await manager.broadcast(conversation_id, payload)

    # بث عالمي (للي مش فاتحين الشات)
    participants = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id != sender_id
    ).all()

    for p in participants:
        await global_manager.send_to_user(p.user_id, payload)

    return payload



# ======================================================
# Get messages by conversation
# ======================================================
@router.get("/messages/{conversation_id}")
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )

    return messages





# ======================================================
# Get my conversations
# ======================================================
@router.get("/my-conversations/{user_id}")
def get_my_conversations(user_id: int, db: Session = Depends(get_db)):
    conversations = (
        db.query(Conversation)
        .join(ConversationParticipant)
        .filter(ConversationParticipant.user_id == user_id)
        .all()
    )

    result = []

    for conv in conversations:
        other_participant = (
            db.query(ConversationParticipant)
            .filter(
                ConversationParticipant.conversation_id == conv.id,
                ConversationParticipant.user_id != user_id
            )
            .first()
        )

        other_user = None
        if other_participant:
            other_user = db.query(User).filter(
                User.id == other_participant.user_id
            ).first()

        last_message = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.id.desc())
            .first()
        )

        me = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conv.id,
            ConversationParticipant.user_id == user_id
        ).first()

        unread_count = 0
        if last_message and me and me.last_read_message_id:
            unread_count = db.query(Message).filter(
                Message.conversation_id == conv.id,
                Message.id > me.last_read_message_id
            ).count()
        elif last_message:
            unread_count = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).count()

        result.append({
            "conversation_id": conv.id,
            "other_user_id": other_user.id if other_user else None,
            "other_user_name": other_user.full_name if other_user else "Unknown",
            # أو other_user.username حسب جدولك
            "last_message": last_message.content if last_message else "",
            "last_time": last_message.created_at.isoformat() if last_message else "",
            "unread_count": unread_count,
        })

    return result



@router.post("/mark-as-read")
def mark_as_read(
    conversation_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):

    last_message = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.id.desc()).first()

    if not last_message:
        return {"status": "no messages"}

    participant = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == user_id
    ).first()

    if not participant:
        raise HTTPException(status_code=403, detail="Not allowed")

    participant.last_read_message_id = last_message.id
    db.commit()

    return {"status": "ok"}



