from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    password = Column(String(255), nullable=False)
    student_id_image = Column(String(255))
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ✅ NEW FIELDS — required for auto-fetch from demo_students
    college = Column(String(150), nullable=True)
    major = Column(String(150), nullable=True)
    minor = Column(String(150), nullable=True)
