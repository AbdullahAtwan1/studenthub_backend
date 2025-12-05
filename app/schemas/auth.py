from app.ai.verify_bzu_card import verify_bzu_card
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
# SIGNUP
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
    # Check duplicates
    if db.query(User).filter(User.student_id == student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already registered")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Save full card image
    upload_dir = "uploads/student_cards"
    os.makedirs(upload_dir, exist_ok=True)
    card_path = os.path.join(upload_dir, f"{student_id}.jpg")

    with open(card_path, "wb") as buffer:
        shutil.copyfileobj(student_id_image.file, buffer)

    # AI Verification
    verified, msg, face_path = verify_bzu_card(card_path, student_id, full_name)

    if not verified:
        os.remove(card_path)
        raise HTTPException(status_code=400, detail=f"Card verification failed: {msg}")

    # Create user
    user = User(
        student_id=student_id,
        full_name=full_name,
        email=email,
        phone=phone,
        password=hash_password(password),
        student_id_image=card_path,
        student_face_image=face_path,
        is_verified=True
    )

    # Auto assign major/college/minor
    demo = db.query(DemoStudent).filter_by(student_id=student_id).first()
    if demo:
        user.college = demo.college
        user.major = demo.major
        user.minor = demo.minor

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

    # ============================
    # 🔍 AI VERIFICATION SECTION
    # ============================
    verified, msg = verify_bzu_card(file_path, student_id, full_name)
    if not verified:
        os.remove(file_path)  # delete fake/wrong image
        raise HTTPException(status_code=400, detail=f"Card verification failed: {msg}")

    # 🔹 Create user instance
    user = User(
        student_id=student_id,
        full_name=full_name,
        email=email,
        phone=phone,
        password=hash_password(password),
        student_card_url=file_path
    )

    # Auto assign from demo
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
            "student_card_url": user.student_id_image,
            "student_face_url": user.student_face_image
        }
    }