from sqlalchemy import Column, Integer, String, Boolean
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    student_card_url = Column(String(255), nullable=True)

    # ✅ Added new fields
    college = Column(String(150), nullable=True)
    major = Column(String(150), nullable=True)
    minor = Column(String(150), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, student_id={self.student_id}, email={self.email})>"
