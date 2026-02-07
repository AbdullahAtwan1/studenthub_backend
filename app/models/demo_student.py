from sqlalchemy import Column, Integer, String
from app.db.database import Base


class DemoStudent(Base):
    __tablename__ = "demo_students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    college = Column(String(150), nullable=True)
    major = Column(String(150), nullable=True)
    minor = Column(String(150), nullable=True)

    def __repr__(self):
        return f"<DemoStudent(student_id={self.student_id}, college={self.college}, major={self.major})>"
