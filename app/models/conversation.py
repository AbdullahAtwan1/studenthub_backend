from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base_class import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False, default="direct")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
