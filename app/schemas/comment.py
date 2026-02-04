from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CommentCreate(BaseModel):
    content: Optional[str] = None
    image: Optional[str] = None

class CommentOut(CommentCreate):
    id: int
    user_id: int
    post_id: int
    created_at: datetime

    class Config:
        from_attributes = True
