from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.db.models import Poll, PollOption, PollVote
from app.schemas.voting import (
    PollOut, PollDetailsOut, PollOptionOut,
    VoteRequest, VoteManyRequest, ResultsOut
)

router = APIRouter(prefix="/polls", tags=["Public Voting"])


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def sync_poll_status(db: Session, poll: Poll) -> Poll:
    n = now_utc()

    if poll.status == "ACTIVE" and n > poll.end_at:
        poll.status = "CLOSED"
        db.commit()
        db.refresh(poll)

    if poll.status in ["CLOSED", "ACTIVE"] and n >= poll.reveal_at:
        poll.status = "REVEALED"
        db.commit()
        db.refresh(poll)

    return poll


def ensure_verified(user: User):
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Voting is allowed only for verified students.")


def ensure_major_access(user: User, poll: Poll):
    if poll.poll_type == "MAJOR":
        if not poll.major:
            raise HTTPException(status_code=500, detail="Poll major is missing.")
        if (user.major or "").strip() != (poll.major or "").strip():
            raise HTTPException(status_code=403, detail="You are not allowed to vote in this major poll.")


@router.get("/active", response_model=List[PollOut])
def list_active_polls(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_verified(current_user)

    polls = db.query(Poll).filter(Poll.status.in_(["ACTIVE", "CLOSED", "REVEALED"])).order_by(Poll.id.desc()).all()
    visible: List[PollOut] = []

    for p in polls:
        p = sync_poll_status(db, p)

        # only show polls that started
        if now_utc() < p.start_at:
            continue

        # MAJOR polls: show only same major
        if p.poll_type == "MAJOR":
            if (current_user.major or "").strip() != (p.major or "").strip():
                continue

        visible.append(PollOut.model_validate(p))

    return visible


@router.get("/{poll_id}", response_model=PollDetailsOut)
def get_poll(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_verified(current_user)

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = sync_poll_status(db, poll)
    ensure_major_access(current_user, poll)

    if now_utc() < poll.start_at:
        raise HTTPException(status_code=403, detail="Poll has not started yet")

    options = db.query(PollOption).filter(PollOption.poll_id == poll_id).order_by(PollOption.id.asc()).all()

    return PollDetailsOut(
        **PollOut.model_validate(poll).model_dump(),
        options=[PollOptionOut.model_validate(o) for o in options]
    )


@router.post("/{poll_id}/vote")
def vote_single(
    poll_id: int,
    data: VoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_verified(current_user)

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = sync_poll_status(db, poll)
    ensure_major_access(current_user, poll)

    n = now_utc()
    if poll.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Poll is not active")
    if n < poll.start_at:
        raise HTTPException(status_code=403, detail="Poll has not started yet")
    if n > poll.end_at:
        raise HTTPException(status_code=403, detail="Poll has ended")

    option = db.query(PollOption).filter(PollOption.id == data.option_id, PollOption.poll_id == poll_id).first()
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")

    # COUNCIL: exactly one vote total
    if poll.poll_type == "COUNCIL":
        existing = db.query(PollVote).filter(
            PollVote.poll_id == poll_id,
            PollVote.student_id == current_user.student_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="You already voted in this poll")

        if option.option_type != "PARTY":
            raise HTTPException(status_code=400, detail="Invalid option type for this poll")

        db.add(PollVote(
            poll_id=poll_id,
            option_id=option.id,
            student_id=current_user.student_id
        ))
        db.commit()
        return {"message": "Vote submitted"}

    # MAJOR: one PRESIDENT vote, multiple MEMBER votes (single endpoint for president if you want)
    if poll.poll_type == "MAJOR":
        if option.option_type == "PRESIDENT":
            existing_pres = (
                db.query(PollVote)
                .join(PollOption, PollVote.option_id == PollOption.id)
                .filter(
                    PollVote.poll_id == poll_id,
                    PollVote.student_id == current_user.student_id,
                    PollOption.option_type == "PRESIDENT"
                )
                .first()
            )
            if existing_pres:
                raise HTTPException(status_code=409, detail="You already voted for president")

            db.add(PollVote(
                poll_id=poll_id,
                option_id=option.id,
                student_id=current_user.student_id
            ))
            db.commit()
            return {"message": "President vote submitted"}

        if option.option_type == "MEMBER":
            # allow multiple member votes, but prevent duplicate same option
            duplicate = db.query(PollVote).filter(
                PollVote.poll_id == poll_id,
                PollVote.student_id == current_user.student_id,
                PollVote.option_id == option.id
            ).first()
            if duplicate:
                raise HTTPException(status_code=409, detail="You already voted for this member")

            db.add(PollVote(
                poll_id=poll_id,
                option_id=option.id,
                student_id=current_user.student_id
            ))
            db.commit()
            return {"message": "Member vote submitted"}

        raise HTTPException(status_code=400, detail="Invalid option type for MAJOR poll")

    raise HTTPException(status_code=400, detail="Invalid poll type")


@router.post("/{poll_id}/vote-members")
def vote_members_many(
    poll_id: int,
    data: VoteManyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_verified(current_user)

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = sync_poll_status(db, poll)
    ensure_major_access(current_user, poll)

    n = now_utc()
    if poll.poll_type != "MAJOR":
        raise HTTPException(status_code=400, detail="This endpoint is only for MAJOR polls")
    if poll.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Poll is not active")
    if n < poll.start_at:
        raise HTTPException(status_code=403, detail="Poll has not started yet")
    if n > poll.end_at:
        raise HTTPException(status_code=403, detail="Poll has ended")

    if not data.option_ids:
        raise HTTPException(status_code=400, detail="option_ids cannot be empty")

    # fetch and validate all options
    options = db.query(PollOption).filter(
        PollOption.poll_id == poll_id,
        PollOption.id.in_(data.option_ids)
    ).all()

    if len(options) != len(set(data.option_ids)):
        raise HTTPException(status_code=404, detail="One or more options not found")

    # all must be MEMBER
    for o in options:
        if o.option_type != "MEMBER":
            raise HTTPException(status_code=400, detail="All options must be MEMBER")

    # insert votes, skipping duplicates
    inserted = 0
    for o in options:
        duplicate = db.query(PollVote).filter(
            PollVote.poll_id == poll_id,
            PollVote.student_id == current_user.student_id,
            PollVote.option_id == o.id
        ).first()
        if duplicate:
            continue

        db.add(PollVote(
            poll_id=poll_id,
            option_id=o.id,
            student_id=current_user.student_id
        ))
        inserted += 1

    db.commit()
    return {"message": "Member votes submitted", "inserted": inserted}


@router.get("/{poll_id}/results", response_model=ResultsOut)
def public_results(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_verified(current_user)

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = sync_poll_status(db, poll)
    ensure_major_access(current_user, poll)

    # hide results until reveal time
    if now_utc() < poll.reveal_at:
        return ResultsOut(
            poll_id=poll.id,
            is_revealed=False,
            status=poll.status,
            totals=None
        )

    options = db.query(PollOption).filter(PollOption.poll_id == poll_id).all()
    votes = db.query(PollVote).filter(PollVote.poll_id == poll_id).all()

    counts: Dict[int, int] = {}
    for v in votes:
        counts[v.option_id] = counts.get(v.option_id, 0) + 1

    items: List[Dict[str, Any]] = []
    for o in options:
        items.append({
            "option_id": o.id,
            "option_type": o.option_type,
            "name": o.name,
            "image_url": o.image_url,
            "votes": counts.get(o.id, 0),
        })
    items.sort(key=lambda x: x["votes"], reverse=True)

    return ResultsOut(
        poll_id=poll.id,
        is_revealed=True,
        status=poll.status,
        totals={"items": items, "total_votes": len(votes)}
    )
