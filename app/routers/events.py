# app/routers/events.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.models.content import Event
from app.schemas.content_schemas import EventCreate, EventOut

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/", response_model=EventOut)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    ev = Event(**payload.dict())
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev

@router.get("/", response_model=List[EventOut])
def list_events(limit:int=10, skip:int=0, db: Session = Depends(get_db)):
    return db.query(Event).order_by(Event.date.desc()).offset(skip).limit(limit).all()
