from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ---------------------------------------------------------
# MATERIAL TYPE ENUM
# ---------------------------------------------------------
class MaterialType(str, Enum):
    lecture = "lecture"
    slide = "slide"
    exam = "exam"


# ---------------------------------------------------------
# CREATE
# (Used for JSON-based creation: links, not uploads)
# ---------------------------------------------------------
class CourseMaterialCreate(BaseModel):
    title: str = Field(..., min_length=2)
    material_type: MaterialType

    # One of these depending on material_type
    file_url: Optional[str] = None
    video_url: Optional[str] = None

    doctor_id: Optional[int] = None


# ---------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------
class CourseMaterialOut(BaseModel):
    id: int
    course_id: int
    doctor_id: Optional[int] = None

    title: str
    material_type: MaterialType

    file_url: Optional[str] = None
    video_url: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------
# LIST OUTPUT (optional helper)
# ---------------------------------------------------------
class CourseMaterialListOut(BaseModel):
    items: List[CourseMaterialOut]
