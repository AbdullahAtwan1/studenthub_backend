from pydantic import BaseModel, EmailStr

class UserOut(BaseModel):
    id: int
    student_id: str
    full_name: str
    email: EmailStr
    phone: str
    is_active: bool

    class Config:
        from_attributes = True
