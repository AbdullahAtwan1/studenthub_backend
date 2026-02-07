class CreateConversation(BaseModel):
    other_user_id: int

class ConversationOut(BaseModel):
    id: int
    type: str
    created_at: datetime
