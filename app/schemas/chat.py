from pydantic import BaseModel
from datetime import datetime

class ChatOut(BaseModel):
    id: int
    user_id: int
    last_message: str | None
    unread_count: int
    updated_at: datetime
