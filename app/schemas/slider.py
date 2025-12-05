from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HomeSliderBase(BaseModel):
    image_url: str
    order_index: int = 0
    is_active: bool = True


class HomeSliderCreate(HomeSliderBase):
    pass


class HomeSliderUpdate(BaseModel):
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class HomeSliderOut(HomeSliderBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # بديل orm_mode في Pydantic v2
