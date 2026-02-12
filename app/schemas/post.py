from pydantic import BaseModel
from typing import List, Optional

class PostCreate(BaseModel):
    content: Optional[str] = None
class PostResponse(BaseModel):
    id: int
    content: Optional[str]
    images: List[str]
    likes_count: int
    comments_count: int

    class Config:
        from_attributes = True
