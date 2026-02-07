from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PollCreate(BaseModel):
    poll_type: str = Field(..., description="COUNCIL or MAJOR")
    title: str
    description: Optional[str] = None

    major: Optional[str] = None  # required for MAJOR polls

    start_at: datetime
    end_at: datetime
    reveal_at: datetime


class PollUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    major: Optional[str] = None

    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    reveal_at: Optional[datetime] = None

    status: Optional[str] = None  # allow admin to set DRAFT/ACTIVE manually if needed


class PollOut(BaseModel):
    id: int
    poll_type: str
    title: str
    description: Optional[str] = None
    major: Optional[str] = None

    status: str
    start_at: datetime
    end_at: datetime
    reveal_at: datetime

    class Config:
        from_attributes = True


class PollOptionCreate(BaseModel):
    option_type: str  # PARTY / PRESIDENT / MEMBER
    name: str
    image_url: Optional[str] = None
    extra_info: Optional[str] = None


class PollOptionOut(BaseModel):
    id: int
    poll_id: int
    option_type: str
    name: str
    image_url: Optional[str] = None
    extra_info: Optional[str] = None

    class Config:
        from_attributes = True


class PollDetailsOut(PollOut):
    options: List[PollOptionOut] = []


class VoteRequest(BaseModel):
    option_id: int


class VoteManyRequest(BaseModel):
    option_ids: List[int]


class ResultsOut(BaseModel):
    poll_id: int
    is_revealed: bool
    status: str
    totals: Optional[Dict[str, Any]] = None
