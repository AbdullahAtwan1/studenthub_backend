from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import os
import uuid

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.db.models import Event, EventAttendance
from app.models.user import User

router = APIRouter(prefix="/admin/events", tags=["Events Admin"])

ALLOWED_ROLES = [
    UserRole.system_admin,
    UserRole.club_admin,
    UserRole.council_member,
    UserRole.council_head,
]

UPLOAD_DIR = "uploads/events"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ======================================================
# UPLOAD EVENT IMAGE
# ======================================================
@router.post("/upload-image")
def upload_event_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, ALLOWED_ROLES)

    ext = os.path.splitext(image.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as f:
        f.write(image.file.read())

    return {"image_url": f"/uploads/events/{filename}"}


# ======================================================
# CREATE EVENT
# ======================================================
@router.post("")
def create_event(
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    location: str = Form(""),
    event_date: str = Form(...),

    target: str = Form(...),          # all | major
    target_major: str | None = Form(None),

    image_url: str | None = Form(None),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, ALLOWED_ROLES)

    if target not in ["all", "major"]:
        raise HTTPException(status_code=400, detail="Invalid target")

    if target == "major" and not target_major:
        raise HTTPException(status_code=400, detail="target_major is required")

    event = Event(
        title=title,
        description=description,
        category=category,
        location=location,
        event_date=datetime.fromisoformat(event_date),
        target_type="ALL" if target == "all" else "MAJOR",
        target_major=target_major if target == "major" else None,
        image_url=image_url,
        created_by_user_id=current_user.id,
        created_by_role=current_user.role,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "title": event.title,
        "category": event.category,
        "event_date": event.event_date,
        "target_type": event.target_type,
        "target_major": event.target_major,
        "image_url": event.image_url,
        "going_count": 0,
    }


# ======================================================
# LIST EVENTS (ADMIN)
# ======================================================
@router.get("")
def list_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, ALLOWED_ROLES)

    events = db.query(Event).order_by(Event.created_at.desc()).all()

    result = []
    for e in events:
        going_count = (
            db.query(EventAttendance)
            .filter(EventAttendance.event_id == e.id)
            .count()
        )

        result.append({
            "id": e.id,
            "title": e.title,
            "category": e.category,
            "event_date": e.event_date,
            "target_type": e.target_type,
            "target_major": e.target_major,
            "image_url": e.image_url,
            "going_count": going_count,
        })

    return result


# ======================================================
# EVENT STATS (✅ FIX FOR 404)
# ======================================================
@router.get("/{event_id}/stats")
def event_stats(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, ALLOWED_ROLES)

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    rows = (
        db.query(
            User.student_id,
            User.full_name,
            User.major,
        )
        .join(
            EventAttendance,
            EventAttendance.student_id == User.student_id
        )
        .filter(EventAttendance.event_id == event_id)
        .all()
    )

    return {
        "going_count": len(rows),
        "going_users": [
            {
                "student_id": r.student_id,
                "full_name": r.full_name,
                "major": r.major,
            }
            for r in rows
        ],
    }

# ======================================================
# DELETE EVENT
# ======================================================
@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if (
        current_user.role != UserRole.system_admin
        and event.created_by_user_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(event)
    db.commit()

    return {"message": "Event deleted"}
