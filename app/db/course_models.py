from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Table,
)
from sqlalchemy.sql import func
from app.db.database import Base

# -------------------------------------------------
# Association table: Course ↔ Doctor (Many-to-Many)
# -------------------------------------------------
course_doctors = Table(
    "course_doctors",
    Base.metadata,
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True),
    Column("doctor_id", Integer, ForeignKey("doctors.id"), primary_key=True),
)


# -----------------
# Course model
# -----------------
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True)  # REQUIRED
    major = Column(String(150), nullable=False)

    description = Column(Text, nullable=False)
    about = Column(Text, nullable=True)

    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


# -----------------
# Doctor model
# -----------------
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    photo = Column(String(255), nullable=True)
