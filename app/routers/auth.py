from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
)
from sqlalchemy.orm import Session
from sqlalchemy import text
import shutil
import os
import random
import string
from datetime import datetime, timedelta

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.core.email_service import send_otp_email
from app.core.permissions import require_role
from app.db.session import get_db
from app.models.otp import OTP, OtpPurpose
from app.models.pending_signup import PendingSignup
from app.ai.verify_bzu_card import verify_bzu_card

from app.models.user import User, UserRole


router = APIRouter()

MEDIA_ROOT = "uploads/student_media"
os.makedirs(MEDIA_ROOT, exist_ok=True)


# ---------------------------------------------------
# Helper: OTP
# ---------------------------------------------------
def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


# ---------------------------------------------------
# SIGN UP (NO USER CREATED YET)
# ---------------------------------------------------
@router.post("/signup")
async def signup(
    student_id: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    student_id_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    db.query(PendingSignup).filter(
        (PendingSignup.email == email)
        | (PendingSignup.student_id == student_id)
    ).delete()
    db.commit()

    db.query(PendingSignup).filter(
        PendingSignup.expires_at < datetime.utcnow()
    ).delete()
    db.commit()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.student_id == student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already registered")

    demo = db.execute(
        text(
            "SELECT full_name, college, major, minor "
            "FROM demo_students WHERE student_id = :sid"
        ),
        {"sid": student_id},
    ).fetchone()

    if not demo:
        raise HTTPException(status_code=404, detail="Student ID not found")

    full_name, college, major, minor = demo

    student_folder = os.path.join(MEDIA_ROOT, student_id)
    os.makedirs(student_folder, exist_ok=True)

    card_path = os.path.join(student_folder, "card.jpg")
    with open(card_path, "wb") as buffer:
        shutil.copyfileobj(student_id_image.file, buffer)

    verified, msg, face_path = verify_bzu_card(card_path, student_id, full_name)
    if not verified:
        raise HTTPException(status_code=400, detail=msg)

    otp = generate_otp()
    pending = PendingSignup(
        student_id=student_id,
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        student_media_folder=student_folder,
        student_card_path=card_path,
        student_face_path=face_path,
        otp_code=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        is_used=False,
    )

    db.add(pending)
    db.commit()

    send_otp_email(email, otp)
    return {"message": "OTP sent", "pending_id": pending.id}


# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------
@router.post("/login")
async def login(
    student_id: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.student_id == student_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Account not verified")

    if not verify_password(password, user.password_hash):

        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_access_token({"sub": user.student_id}, timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------
# CURRENT USER
# ---------------------------------------------------
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
