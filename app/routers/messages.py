from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.content import Message
from app.db.database import get_db

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("/")
def send_message(sender_id: int, receiver_id: int, content: str, db: Session = Depends(get_db)):
    msg = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/{user_id}")
def get_messages(user_id: int, db: Session = Depends(get_db)):
    return db.query(Message).filter(
        (Message.sender_id == user_id) |
        (Message.receiver_id == user_id)
    ).all()
