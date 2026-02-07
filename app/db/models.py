from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Table,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


# ==============================
# DOCTORS
# ==============================
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(255), nullable=False)

    email = Column(String(255), unique=True, nullable=False)

    department = Column(String(150), nullable=False)

    photo = Column(String(255), nullable=True)

    # ❌ REMOVED created_at (NOT in DB)


# ==============================
# COURSE ↔ DOCTOR (MANY TO MANY)
# ==============================
course_doctors = Table(
    "course_doctors",
    Base.metadata,
    Column("course_id", ForeignKey("courses.id"), primary_key=True),
    Column("doctor_id", ForeignKey("doctors.id"), primary_key=True),
)


# ==============================
# COURSES
# ==============================
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    major = Column(String(150), nullable=False)

    about = Column(Text, nullable=True)

    is_published = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())

    doctors = relationship(
        "Doctor",
        secondary=course_doctors,
        backref="courses",
        lazy="joined",
    )


# ==============================
# COURSE MATERIALS
# ==============================
class CourseMaterial(Base):
    __tablename__ = "course_materials"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)

    file_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)

    material_type = Column(String(50), nullable=False)

    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    course = relationship("Course", backref="materials")
    doctor = relationship("Doctor", backref="materials")


# ==============================
# VOTING SYSTEM (NEW)
# ==============================

class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)

    # COUNCIL = Student Council parties
    # MAJOR = Major-based voting (club voting)
    poll_type = Column(String(20), nullable=False)  # "COUNCIL" | "MAJOR"

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # For MAJOR polls only: only students with user.major == poll.major can vote
    major = Column(String(150), nullable=True)

    # Status labels: DRAFT / ACTIVE / CLOSED / REVEALED
    status = Column(String(20), nullable=False, default="DRAFT")

    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    reveal_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    votes = relationship("PollVote", back_populates="poll", cascade="all, delete-orphan")


class PollOption(Base):
    __tablename__ = "poll_options"

    id = Column(Integer, primary_key=True, index=True)

    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)

    # PARTY for COUNCIL
    # PRESIDENT / MEMBER for MAJOR
    option_type = Column(String(20), nullable=False)  # "PARTY" | "PRESIDENT" | "MEMBER"

    name = Column(String(255), nullable=False)
    image_url = Column(String(500), nullable=True)
    extra_info = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    poll = relationship("Poll", back_populates="options")
    votes = relationship("PollVote", back_populates="option", cascade="all, delete-orphan")


class PollVote(Base):
    __tablename__ = "poll_votes"

    id = Column(Integer, primary_key=True, index=True)

    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    option_id = Column(Integer, ForeignKey("poll_options.id"), nullable=False)

    # user.student_id is string; keep it as string in votes for consistency
    student_id = Column(String(20), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    poll = relationship("Poll", back_populates="votes")
    option = relationship("PollOption", back_populates="votes")


# ==============================
# EVENTS SYSTEM (NEW)
# ==============================

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    category = Column(String(50), nullable=False)
    location = Column(String(255), nullable=True)

    # We keep date/time simple and frontend-friendly
    event_date = Column(DateTime, nullable=False)
    start_time = Column(String(20), nullable=True)
    end_time = Column(String(20), nullable=True)

    image_url = Column(String(255), nullable=True)

    # Visibility target
    # ALL  -> visible to all students
    # MAJOR -> visible only for students with user.major == target_major
    target_type = Column(String(20), nullable=False, default="ALL")  # ALL | MAJOR
    target_major = Column(String(150), nullable=True)

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_role = Column(String(50), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    attendees = relationship(
        "EventAttendance",
        back_populates="event",
        cascade="all, delete-orphan"
    )


class EventAttendance(Base):
    __tablename__ = "event_attendance"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # Keep consistency with voting: store student_id as string
    student_id = Column(String(20), nullable=False)

    # Only GOING (as you confirmed)
    status = Column(String(20), nullable=False, default="GOING")

    created_at = Column(DateTime, server_default=func.now())

    event = relationship("Event", back_populates="attendees")
