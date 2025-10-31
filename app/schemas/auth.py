from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.demo_student import DemoStudent   # ✅ NEW import
from app.schemas.user_schemas import UserCreate, UserLogin, UserOut
from app.security import hash_password, verify_password, create_access_token

import shutil
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------
# ✅ SIGNUP
# ---------------------------
@router.post("/signup", response_model=UserOut)
async def signup(
    student_id: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    student_id_image: UploadFile = Form(...),
    db: Session = Depends(get_db)
):
    # 🔹 Check if student already exists
    existing_user = db.query(User).filter(User.student_id == student_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Student ID already registered")

    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 🔹 Save student ID image
    upload_dir = "app/uploads/student_cards"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, student_id_image.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(student_id_image.file, buffer)

    # 🔹 Create user instance
    user = User(
        student_id=student_id,
        full_name=full_name,
        email=email,
        phone=phone,
        password=hash_password(password),
        student_card_url=file_path
    )

    # ✅ Auto assign college & major based on demo_students table
    demo = db.query(DemoStudent).filter_by(student_id=student_id).first()
    if demo:
        user.college = demo.college
        user.major = demo.major
        user.minor = demo.minor

    # 🔹 Save user
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ---------------------------
# ✅ LOGIN
# ---------------------------
@router.post("/login")
async def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.student_id == data.student_id).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid student ID or password")

    token = create_access_token({"sub": user.student_id})

    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "student_id": user.student_id,
            "full_name": user.full_name,
            "email": user.email,
            "college": user.college,
            "major": user.major,
            "minor": user.minor,
            "is_verified": user.is_verified,
            "student_card_url": user.student_card_url
        }
    }
