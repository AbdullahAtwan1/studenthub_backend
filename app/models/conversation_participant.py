from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.base_class import Base


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    id = Column(Integer, primary_key=True, index=True)

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 🔥 آخر رسالة قرأها المستخدم (لـ unread / seen logic)
    last_read_message_id = Column(Integer, nullable=True)

    # ⏱️ وقت الانضمام للمحادثة
    joined_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
