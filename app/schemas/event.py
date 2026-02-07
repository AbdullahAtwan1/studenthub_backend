from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EventCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None

    category: str = Field(..., min_length=2, max_length=50)
    location: Optional[str] = Field(None, max_length=255)

    event_date: datetime
    start_time: Optional[str] = Field(None, max_length=20)
    end_time: Optional[str] = Field(None, max_length=20)

    image_url: Optional[str] = Field(None, max_length=255)

    # ALL | MAJOR
    target_type: str = Field("ALL", max_length=20)
    target_major: Optional[str] = Field(None, max_length=150)


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None

    category: Optional[str] = Field(None, min_length=2, max_length=50)
    location: Optional[str] = Field(None, max_length=255)

    event_date: Optional[datetime] = None
    start_time: Optional[str] = Field(None, max_length=20)
    end_time: Optional[str] = Field(None, max_length=20)

    image_url: Optional[str] = Field(None, max_length=255)

    target_type: Optional[str] = Field(None, max_length=20)  # ALL | MAJOR
    target_major: Optional[str] = Field(None, max_length=150)


class EventOut(BaseModel):
    id: int
    title: str
    description: Optional[str]

    category: str
    location: Optional[str]

    event_date: datetime
    start_time: Optional[str]
    end_time: Optional[str]

    image_url: Optional[str]

    target_type: str
    target_major: Optional[str]

    created_by_user_id: int
    created_by_role: str
    created_at: datetime

    going_count: int = 0

    class Config:
        from_attributes = True


class GoingUserOut(BaseModel):
    student_id: str
    full_name: Optional[str] = None
    major: Optional[str] = None


class EventStatsOut(BaseModel):
    event_id: int
    going_count: int
    going_users: List[GoingUserOut]
