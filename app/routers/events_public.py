from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.event import EventOut
from app.services import event_service

router = APIRouter(prefix="/events", tags=["Events (Public)"])


@router.get("", response_model=list[EventOut])
def list_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = event_service.list_events_public(db, current_user)

    out = []
    for ev, going_count in rows:
        item = EventOut.model_validate(ev)
        item.going_count = going_count
        out.append(item)

    return out


@router.post("/{event_id}/going")
def mark_going(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event_service.mark_going(db, current_user, event_id)
    return {"message": "Marked as GOING"}


@router.delete("/{event_id}/going")
def unmark_going(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event_service.unmark_going(db, current_user, event_id)
    return {"message": "Removed GOING"}
