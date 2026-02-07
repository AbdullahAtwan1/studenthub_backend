import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.db.models import Poll, PollOption, PollVote
from app.schemas.voting import (
    PollCreate, PollUpdate, PollOut,
    PollOptionCreate, PollOptionOut,
    PollDetailsOut, ResultsOut
)

router = APIRouter(prefix="/admin/polls", tags=["Admin Voting"])


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def sync_poll_status(db: Session, poll: Poll) -> Poll:
    n = now_utc()

    # Auto close
    if poll.status == "ACTIVE" and n > poll.end_at:
        poll.status = "CLOSED"
        db.commit()
        db.refresh(poll)

    # Auto revealed
    if poll.status in ["CLOSED", "ACTIVE"] and n >= poll.reveal_at:
        poll.status = "REVEALED"
        db.commit()
        db.refresh(poll)

    return poll


def ensure_valid_poll_rules(poll_type: str, major: Optional[str]):
    if poll_type not in ["COUNCIL", "MAJOR"]:
        raise HTTPException(status_code=400, detail="poll_type must be COUNCIL or MAJOR")

    if poll_type == "MAJOR" and not major:
        raise HTTPException(status_code=400, detail="major is required for MAJOR polls")

    if poll_type == "COUNCIL" and major:
        raise HTTPException(status_code=400, detail="major must be null for COUNCIL polls")


@router.post("", response_model=PollOut)
def create_poll(
    data: PollCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin])

    ensure_valid_poll_rules(data.poll_type, data.major)

    if data.end_at <= data.start_at:
        raise HTTPException(status_code=400, detail="end_at must be after start_at")

    if data.reveal_at < data.end_at:
        raise HTTPException(status_code=400, detail="reveal_at must be >= end_at")

    poll = Poll(
        poll_type=data.poll_type,
        title=data.title,
        description=data.description,
        major=data.major,
        status="DRAFT",
        start_at=data.start_at,
        end_at=data.end_at,
        reveal_at=data.reveal_at,
    )
    db.add(poll)
    db.commit()
    db.refresh(poll)
    return poll


@router.get("", response_model=List[PollOut])
def list_polls(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin])

    polls = db.query(Poll).order_by(Poll.id.desc()).all()
    for p in polls:
        sync_poll_status(db, p)
    return polls


@router.get("/{poll_id}", response_model=PollDetailsOut)
def get_poll_details(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin])

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = sync_poll_status(db, poll)

    options = db.query(PollOption).filter(PollOption.poll_id == poll_id).order_by(PollOption.id.asc()).all()
    return PollDetailsOut(
        **PollOut.model_validate(poll).model_dump(),
        options=[PollOptionOut.model_validate(o) for o in options]
    )


@router.put("/{poll_id}", response_model=PollOut)
def update_poll(
    poll_id: int,
    data: PollUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin])

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    if poll.status in ["CLOSED", "REVEALED"]:
        raise HTTPException(status_code=400, detail="Cannot edit a CLOSED/REVEALED poll")

    payload = data.model_dump(exclude_unset=True)

    # If updating poll_type rules indirectly
    major = payload.get("major", poll.major)
    ensure_valid_poll_rules(poll.poll_type, major)

    for k, v in payload.items():
        setattr(poll, k, v)

    # Validate times after update
    if poll.end_at <= poll.start_at:
        raise HTTPException(status_code=400, detail="end_at must be after start_at")
    if poll.reveal_at < poll.end_at:
        raise HTTPException(status_code=400, detail="reveal_at must be >= end_at")

    db.commit()
    db.refresh(poll)
    return poll


@router.post("/{poll_id}/activate", response_model=PollOut)
def activate_poll(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin])

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = sync_poll_status(db, poll)
    if poll.status in ["CLOSED", "REVEALED"]:
        raise HTTPException(status_code=400, detail="Cannot activate CLOSED/REVEALED poll")

    poll.status = "ACTIVE"
    db.commit()
    db.refresh(poll)
    return poll


@router.post("/{poll_id}/options", response_model=PollOptionOut)
def add_option(
    poll_id: int,
    data: PollOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin])

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    if poll.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Options can be added only in DRAFT")

    allowed = {"COUNCIL": ["PARTY"], "MAJOR": ["PRESIDENT", "MEMBER"]}
    if data.option_type not in allowed.get(poll.poll_type, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid option_type for {poll.poll_type}. Allowed: {allowed[poll.poll_type]}",
        )

    opt = PollOption(
        poll_id=poll_id,
        option_type=data.option_type,
        name=data.name,
        image_url=data.image_url,
        extra_info=data.extra_info,
    )
    db.add(opt)
    db.commit()
    db.refresh(opt)
    return opt


@router.delete("/{poll_id}/options/{option_id}")
def delete_option(
    poll_id: int,
    option_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin])

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    if poll.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Options can be deleted only in DRAFT")

    opt = db.query(PollOption).filter(PollOption.id == option_id, PollOption.poll_id == poll_id).first()
    if not opt:
        raise HTTPException(status_code=404, detail="Option not found")

    db.delete(opt)
    db.commit()
    return {"message": "Option deleted successfully"}


@router.post("/upload-image")
async def upload_poll_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin])

    uploads_dir = os.path.join("uploads", "polls")
    os.makedirs(uploads_dir, exist_ok=True)

    safe_name = file.filename.replace(" ", "_")
    timestamp = int(datetime.utcnow().timestamp())
    filename = f"{timestamp}_{safe_name}"
    file_path = os.path.join(uploads_dir, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {"url": f"/uploads/polls/{filename}"}


@router.get("/{poll_id}/results", response_model=ResultsOut)
def admin_results(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin])

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = sync_poll_status(db, poll)

    # Admin can always see counts (students will be hidden until reveal_at in public router)
    options = db.query(PollOption).filter(PollOption.poll_id == poll_id).all()
    votes = db.query(PollVote).filter(PollVote.poll_id == poll_id).all()

    counts: Dict[int, int] = {}
    for v in votes:
        counts[v.option_id] = counts.get(v.option_id, 0) + 1

    result_rows: List[Dict[str, Any]] = []
    for o in options:
        result_rows.append({
            "option_id": o.id,
            "option_type": o.option_type,
            "name": o.name,
            "image_url": o.image_url,
            "votes": counts.get(o.id, 0),
        })

    result_rows.sort(key=lambda x: x["votes"], reverse=True)

    return ResultsOut(
        poll_id=poll.id,
        is_revealed=(now_utc() >= poll.reveal_at),
        status=poll.status,
        totals={"items": result_rows, "total_votes": len(votes)}
    )
