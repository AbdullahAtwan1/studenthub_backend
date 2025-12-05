from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from .base_class import Base  # هذا نفس Base اللي تستخدمه لباقي الـ models


class HomeSlider(Base):
    __tablename__ = "home_slider"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
