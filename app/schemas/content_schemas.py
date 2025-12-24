# app/schemas/content_schemas.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Courses ---
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: Optional[str] = None
    thumbnail: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseOut(CourseBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Progress
class CourseProgressBase(BaseModel):
    user_id: int
    course_id: int
    progress_percent: int = 0
    status: Optional[str] = "in_progress"

class CourseProgressOut(CourseProgressBase):
    id: int
    updated_at: datetime
    class Config:
        orm_mode = True

# --- Events ---
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventOut(EventBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

# --- Polls ---
class PollOptionCreate(BaseModel):
    option_text: str

class PollCreate(BaseModel):
    question: str
    options: List[PollOptionCreate]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    active: Optional[bool] = True

class PollOptionOut(BaseModel):
    id: int
    option_text: str
    votes_count: Optional[int] = 0

    class Config:
        orm_mode = True

class PollOut(BaseModel):
    id: int
    question: str
    options: List[PollOptionOut]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    active: bool

    class Config:
        orm_mode = True

# --- Chat ---
class MessageCreate(BaseModel):
    conversation_id: int
    sender_id: int
    text: Optional[str] = None
    attachment: Optional[str] = None

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    text: Optional[str]
    attachment: Optional[str]
    created_at: datetime
    is_read: bool

    class Config:
        orm_mode = True

# --- Notifications ---
class NotificationCreate(BaseModel):
    user_id: int
    title: str
    body: Optional[str] = None

class NotificationOut(NotificationCreate):
    id: int
    read: bool
    title: str
    body: str
    created_at: datetime

    class Config:
        orm_mode = True
