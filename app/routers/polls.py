# app/routers/polls.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.models.content import Poll, PollOption, Vote
from app.schemas.content_schemas import PollCreate, PollOut, PollOptionOut

router = APIRouter(prefix="/polls", tags=["polls"])

@router.post("/", response_model=PollOut)
def create_poll(payload: PollCreate, db: Session = Depends(get_db)):
    poll = Poll(question=payload.question, start_date=payload.start_date, end_date=payload.end_date, active=payload.active)
    db.add(poll)
    db.flush()  # get id
    for opt in payload.options:
        po = PollOption(poll_id=poll.id, option_text=opt.option_text)
        db.add(po)
    db.commit()
    db.refresh(poll)
    return poll

@router.get("/active", response_model=List[PollOut])
def get_active_polls(db: Session = Depends(get_db)):
    polls = db.query(Poll).filter(Poll.active==True).all()
    return polls

@router.post("/{option_id}/vote")
def vote(option_id: int, user_id: int, db: Session = Depends(get_db)):
    option = db.query(PollOption).filter_by(id=option_id).first()
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")
    # For simplicity, allow multiple votes; to restrict, check existing Vote by user and poll
    v = Vote(option_id=option_id, user_id=user_id)
    db.add(v)
    db.commit()
    return {"ok": True}

# results
@router.get("/{poll_id}/results", response_model=PollOut)
def poll_results(poll_id: int, db: Session = Depends(get_db)):
    poll = db.query(Poll).filter_by(id=poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll
