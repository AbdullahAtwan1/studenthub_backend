from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime




# =================================================
# DOCTOR (NESTED RESPONSE – SAFE & LIGHT)
# =================================================
class CourseDoctorOut(BaseModel):
    id: int
    full_name: str
    email: str
    department: str

    class Config:
        from_attributes = True


# =================================================
# BASE
# =================================================
class CourseBase(BaseModel):
    name: str
    code: str
    major: str
    description: Optional[str] = None
    about: Optional[str] = None
    is_published: bool = False


# =================================================
# CREATE
# =================================================
class CourseCreate(CourseBase):
    doctor_ids: Optional[List[int]] = None


# =================================================
# UPDATE
# =================================================
class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    major: Optional[str] = None
    description: Optional[str] = None
    about: Optional[str] = None
    is_published: Optional[bool] = None
    doctor_ids: Optional[List[int]] = None


# =================================================
# RESPONSE  ✅ THIS WAS THE BUG SOURCE
# =================================================
class CourseOut(CourseBase):
    id: int
    created_at: datetime

    # 🔥 MUST EXIST so frontend keeps courses after refresh
    doctors: List[CourseDoctorOut] = []

    class Config:
        from_attributes = True




class CourseAdminOut(BaseModel):
    id: int
    name: str
    code: str
    major: str
    description: Optional[str] = None
    about: Optional[str] = None
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True        
