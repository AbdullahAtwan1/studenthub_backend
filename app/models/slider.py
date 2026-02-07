from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.db.database import Base

class HomeSlider(Base):
    __tablename__ = "home_slider"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
