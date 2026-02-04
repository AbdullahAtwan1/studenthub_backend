from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    content: Optional[str] = None
    attachment: Optional[str] = None

class MessageOut(BaseModel):
    id: int
    sender_id: int
    content: Optional[str]
    attachment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
