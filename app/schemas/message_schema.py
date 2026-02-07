class SendMessage(BaseModel):
    conversation_id: int
    content: str

class MessageOut(BaseModel):
    id: int
    sender_id: int
    content: str
    created_at: datetime
