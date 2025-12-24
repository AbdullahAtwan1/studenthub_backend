from pydantic import BaseModel, EmailStr
from typing import Optional

# ----------------------------
#  Create User Schema
# ----------------------------
class UserCreate(BaseModel):
    student_id: str
    email: EmailStr
    password: str


# ----------------------------
#  Login Schema
# ----------------------------
class UserLogin(BaseModel):
    student_id: str
    password: str


# ----------------------------
#  Token Schema
# ----------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ----------------------------
#  User Output Schema
# ----------------------------
class UserOut(BaseModel):
    id: int
    student_id: str
    email: str
    is_verified: bool
    student_card_url: Optional[str] = None

    # ✅ New fields added for automatic college/major/minor
    college: Optional[str] = None
    major: Optional[str] = None
    minor: Optional[str] = None

    class Config:
        from_attributes = True
