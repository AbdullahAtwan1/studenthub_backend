# app/routers/notifications.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.models.content import Notification
from app.schemas.content_schemas import NotificationCreate, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/", response_model=NotificationOut)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    n = Notification(**payload.dict())
    db.add(n)
    db.commit()
    db.refresh(n)
    return n

@router.get("/user/{user_id}", response_model=List[NotificationOut])
def get_user_notifications(user_id: int, only_unread: bool = False, db: Session = Depends(get_db)):
    q = db.query(Notification).filter_by(user_id=user_id)
    if only_unread:
        q = q.filter_by(read=False)
    return q.order_by(Notification.created_at.desc()).all()

@router.post("/{notif_id}/mark_read")
def mark_read(notif_id: int, db: Session = Depends(get_db)):
    n = db.query(Notification).filter_by(id=notif_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = True
    db.commit()
    return {"ok": True}
