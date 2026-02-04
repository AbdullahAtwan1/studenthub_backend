from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PostCreate(BaseModel):
    content: Optional[str] = None
    image: Optional[str] = None

class PostOut(PostCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
