from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from datetime import datetime
from app.db.session import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))      # صاحب البوست
    actor_id = Column(Integer, ForeignKey("users.id"))    # اللي عمل لايك / كومنت
    post_id = Column(Integer, ForeignKey("posts.id"))
    type = Column(String(20))  # LIKE / COMMENT
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
