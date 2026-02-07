import os
import uuid
from typing import Optional, List, Tuple
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Event, EventAttendance
from app.models.user import User, UserRole


ALLOWED_CREATORS = {
    UserRole.system_admin,
    UserRole.club_admin,
    UserRole.council_member,
    UserRole.council_head,
}


def _validate_target(target_type: str, target_major: Optional[str]):
    t = (target_type or "").upper().strip()
    if t not in ["ALL", "MAJOR"]:
        raise HTTPException(status_code=400, detail="target_type must be ALL or MAJOR")

    if t == "MAJOR" and (not target_major or not target_major.strip()):
        raise HTTPException(status_code=400, detail="target_major is required when target_type=MAJOR")

    if t == "ALL":
        return "ALL", None

    return "MAJOR", target_major.strip()


def can_manage_event(current_user: User, event: Event) -> bool:
    # Only creator OR system_admin can edit/delete
    if current_user.role == UserRole.system_admin:
        return True
    return event.created_by_user_id == current_user.id


def create_event(db: Session, current_user: User, data) -> Event:
    if current_user.role not in ALLOWED_CREATORS:
        raise HTTPException(status_code=403, detail="Only admin/club/council can create events")

    target_type, target_major = _validate_target(data.target_type, data.target_major)

    ev = Event(
        title=data.title.strip(),
        description=data.description,
        category=data.category.strip(),
        location=data.location,

        event_date=data.event_date,
        start_time=data.start_time,
        end_time=data.end_time,

        image_url=data.image_url,

        target_type=target_type,
        target_major=target_major,

        created_by_user_id=current_user.id,
        created_by_role=str(current_user.role),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def update_event(db: Session, current_user: User, event_id: int, data) -> Event:
    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    if not can_manage_event(current_user, ev):
        raise HTTPException(status_code=403, detail="Only creator or system_admin can edit this event")

    # Update fields if provided
    if data.title is not None:
        ev.title = data.title.strip()

    if data.description is not None:
        ev.description = data.description

    if data.category is not None:
        ev.category = data.category.strip()

    if data.location is not None:
        ev.location = data.location

    if data.event_date is not None:
        ev.event_date = data.event_date

    if data.start_time is not None:
        ev.start_time = data.start_time

    if data.end_time is not None:
        ev.end_time = data.end_time

    if data.image_url is not None:
        ev.image_url = data.image_url

    if data.target_type is not None:
        # If target_type changes, validate with target_major
        new_target_type, new_target_major = _validate_target(
            data.target_type,
            data.target_major if data.target_major is not None else ev.target_major
        )
        ev.target_type = new_target_type
        ev.target_major = new_target_major

    if data.target_major is not None and (data.target_type is None):
        # target_major updated but target_type unchanged: validate based on current target_type
        new_target_type, new_target_major = _validate_target(ev.target_type, data.target_major)
        ev.target_type = new_target_type
        ev.target_major = new_target_major

    db.commit()
    db.refresh(ev)
    return ev


def delete_event(db: Session, current_user: User, event_id: int) -> None:
    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    if not can_manage_event(current_user, ev):
        raise HTTPException(status_code=403, detail="Only creator or system_admin can delete this event")

    db.delete(ev)
    db.commit()


def list_events_public(db: Session, current_user: User) -> List[Tuple[Event, int]]:
    """
    Returns events for:
      - ALL
      - MAJOR where event.target_major == current_user.major
    """
    user_major = (current_user.major or "").strip()

    q = db.query(Event).filter(
        (Event.target_type == "ALL") |
        ((Event.target_type == "MAJOR") & (Event.target_major == user_major))
    ).order_by(Event.event_date.desc())

    events = q.all()

    # add going counts
    event_ids = [e.id for e in events]
    counts = {}
    if event_ids:
        rows = (
            db.query(EventAttendance.event_id, func.count(EventAttendance.id))
            .filter(EventAttendance.event_id.in_(event_ids))
            .group_by(EventAttendance.event_id)
            .all()
        )
        counts = {eid: c for (eid, c) in rows}

    return [(e, counts.get(e.id, 0)) for e in events]


def list_events_admin(db: Session) -> List[Tuple[Event, int]]:
    q = db.query(Event).order_by(Event.created_at.desc())
    events = q.all()

    event_ids = [e.id for e in events]
    counts = {}
    if event_ids:
        rows = (
            db.query(EventAttendance.event_id, func.count(EventAttendance.id))
            .filter(EventAttendance.event_id.in_(event_ids))
            .group_by(EventAttendance.event_id)
            .all()
        )
        counts = {eid: c for (eid, c) in rows}

    return [(e, counts.get(e.id, 0)) for e in events]


def get_event_stats(db: Session, event_id: int) -> Tuple[int, List[str]]:
    going_rows = db.query(EventAttendance.student_id).filter(
        EventAttendance.event_id == event_id,
        EventAttendance.status == "GOING"
    ).all()
    student_ids = [r[0] for r in going_rows]
    return len(student_ids), student_ids


def mark_going(db: Session, current_user: User, event_id: int) -> None:
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="Only students can mark going")

    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    # Ensure visibility rules
    if ev.target_type == "MAJOR":
        if (current_user.major or "").strip() != (ev.target_major or "").strip():
            raise HTTPException(status_code=403, detail="This event is not for your major")

    # Upsert GOING
    row = db.query(EventAttendance).filter(
        EventAttendance.event_id == event_id,
        EventAttendance.student_id == current_user.student_id
    ).first()

    if row:
        row.status = "GOING"
    else:
        row = EventAttendance(
            event_id=event_id,
            student_id=current_user.student_id,
            status="GOING"
        )
        db.add(row)

    db.commit()


def unmark_going(db: Session, current_user: User, event_id: int) -> None:
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="Only students can remove going")

    row = db.query(EventAttendance).filter(
        EventAttendance.event_id == event_id,
        EventAttendance.student_id == current_user.student_id
    ).first()

    if not row:
        return

    db.delete(row)
    db.commit()


def save_event_image(upload_dir: str, filename: str, file_bytes: bytes) -> str:
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(filename)[1].lower().strip()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail="Only png/jpg/jpeg/webp images are allowed")

    new_name = f"event_{uuid.uuid4().hex}{ext}"
    path = os.path.join(upload_dir, new_name)

    with open(path, "wb") as f:
        f.write(file_bytes)

    # Returned path matches your static mount /uploads
    return f"/uploads/events/{new_name}"
