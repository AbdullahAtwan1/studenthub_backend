# app/models/content.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(String(50))
    thumbnail = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, nullable=True)  # optional, if courses created by users

    # progress relation (optional)
    progresses = relationship("CourseProgress", back_populates="course")

class CourseProgress(Base):
    __tablename__ = "course_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    progress_percent = Column(Integer, default=0)
    status = Column(String(50), default="in_progress")  # 'saved','in_progress','completed'
    updated_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="progresses")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    date = Column(DateTime)
    location = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, nullable=True)

class Poll(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(500), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    options = relationship("PollOption", back_populates="poll", cascade="all,delete-orphan")

class PollOption(Base):
    __tablename__ = "poll_options"
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    option_text = Column(String(255))
    poll = relationship("Poll", back_populates="options")
    votes = relationship("Vote", back_populates="option")

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    option_id = Column(Integer, ForeignKey("poll_options.id"))
    user_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    option = relationship("PollOption", back_populates="votes")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    participants = Column(Text)  # comma-separated user ids (simple approach)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender_id = Column(Integer, index=True)
    text = Column(Text, nullable=True)
    attachment = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    title = Column(String(255))
    body = Column(Text)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
