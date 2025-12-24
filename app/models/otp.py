from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from datetime import datetime, timedelta
import enum
from app.db.base_class import Base

class OtpPurpose(str, enum.Enum):
    signup = "signup"
    forgot_password = "forgot_password"

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    code = Column(String(6), nullable=False)
    purpose = Column(Enum(OtpPurpose), nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=15))
    created_at = Column(DateTime, default=datetime.utcnow)
