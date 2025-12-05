from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timedelta
from app.db.base_class import Base


class PendingSignup(Base):
    __tablename__ = "pending_signups"

    id = Column(Integer, primary_key=True, index=True)

    # Student info
    student_id = Column(String(20), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=False)

    # Password (hashed)
    password_hash = Column(String(255), nullable=False)

    # NEW — media paths
    student_media_folder = Column(String(255), nullable=True)
    student_card_path = Column(String(255), nullable=True)
    student_face_path = Column(String(255), nullable=True)

    # OTP
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(minutes=15))
    is_used = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
