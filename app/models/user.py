from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from app.db.database import Base
from datetime import datetime
import enum


class UserRole(str, enum.Enum):
    student = "student"
    doctor = "doctor"
    club_admin = "club_admin"
    council_member = "council_member"
    council_head = "council_head"
    developer = "developer"
    system_admin = "system_admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)

    password_hash = Column(String(255), nullable=False)

    # ✅ Images
    profile_image = Column(String(255), nullable=True)
    cover_image = Column(String(255), nullable=True)   # ✅ NEW

    student_id_image = Column(String(255), nullable=True)
    student_media_folder = Column(String(255), nullable=True)
    student_card_path = Column(String(255), nullable=True)
    student_face_path = Column(String(255), nullable=True)

    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    college = Column(String(150), nullable=True)
    major = Column(String(150), nullable=True)
    minor = Column(String(150), nullable=True)

    role = Column(
        Enum(UserRole),
        default=UserRole.student,
        nullable=True
    )

    club_name = Column(String(150), nullable=True)
