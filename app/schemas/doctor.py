from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# =========================
# BASE (FOR INPUT)
# =========================
class DoctorBase(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    department: str = Field(..., min_length=2)


# =========================
# CREATE (STRICT)
# =========================
class DoctorCreate(DoctorBase):
    pass


# =========================
# OUTPUT (SAFE – NO CRASH)
# =========================
class DoctorOut(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = None     # 🔥 relaxed
    department: Optional[str] = None
    photo: Optional[str] = None

    class Config:
        orm_mode = True
