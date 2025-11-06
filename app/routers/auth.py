from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
    status,
    Security,
)
from sqlalchemy.orm import Session
from sqlalchemy import text

import shutil, os, random, string
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.user import User
from app.models.otp import OTP, OtpPurpose
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.core.security import get_current_user

from app.utils.email_sender import send_email
from app.core.security_scheme import api_key_scheme
router = APIRouter()
UPLOAD_DIR = "uploads/student_ids"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------
# Helper function
# ---------------------------------------------------
def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


# ---------------------------------------------------
# SIGN UP
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
    # ✅ Check if already registered
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.student_id == student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already registered")

    # ✅ Fetch student data from demo_students table
    demo_student = db.execute(
        text("SELECT full_name, college, major, minor FROM demo_students WHERE student_id = :sid"),
        {"sid": student_id}
    ).fetchone()

    if not demo_student:
        raise HTTPException(status_code=404, detail="Student ID not found in demo records")

    full_name, college, major, minor = demo_student

    # ✅ Save uploaded ID image
    image_path = os.path.join(UPLOAD_DIR, f"{student_id}_{student_id_image.filename}")
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(student_id_image.file, buffer)

    # ✅ Create new user with data from demo_students
    new_user = User(
        student_id=student_id,
        full_name=full_name,
        email=email,
        phone=phone,
        password=hash_password(password),
        student_id_image=image_path,
        college=college,
        major=major,
        minor=minor,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # ✅ Generate OTP
    otp_code = generate_otp()
    otp = OTP(user_id=new_user.id, code=otp_code, purpose=OtpPurpose.signup)
    db.add(otp)
    db.commit()

    # ✅ Send OTP
    try:
        send_email(email, "StudentHub OTP Verification", f"Your verification code is: {otp_code}")
    except Exception as e:
        print(f"[❌] Email sending failed: {e}")
        raise HTTPException(status_code=500, detail="Could not send OTP email.")

    return {
        "message": "OTP sent to email.",
        "user_id": new_user.id,
        "auto_filled": {
            "full_name": full_name,
            "college": college,
            "major": major,
            "minor": minor
        }
    }
# ---------------------------------------------------
# VERIFY OTP (SIGNUP)
# ---------------------------------------------------
@router.post("/verify-otp")
async def verify_otp(
    user_id: int = Form(...),
    otp_code: str = Form(...),
    db: Session = Depends(get_db),
):
    otp = (
        db.query(OTP)
        .filter(OTP.user_id == user_id, OTP.code == otp_code, OTP.purpose == OtpPurpose.signup)
        .first()
    )
    if not otp or otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.query(OTP).filter(OTP.user_id == user_id).delete()
    db.commit()

    return {"message": "Account verified successfully!"}


# ---------------------------------------------------
# RESEND OTP
# ---------------------------------------------------
@router.post("/resend-otp")
async def resend_otp(
    user_id: int = Form(...),
    purpose: str = Form(...),
    db: Session = Depends(get_db),
):
    purpose = purpose.lower().strip()
    if purpose not in ["signup", "forgot_password"]:
        raise HTTPException(status_code=400, detail="Invalid purpose")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp_code = generate_otp()
    otp = OTP(user_id=user.id, code=otp_code, purpose=purpose)
    db.add(otp)
    db.commit()

    try:
        subject = "StudentHub OTP Verification"
        body = f"Your StudentHub {purpose.replace('_', ' ')} OTP code is: {otp_code}"
        send_email(user.email, subject, body)
        print(f"[✅] Resent OTP {otp_code} sent to {user.email}")
    except Exception as e:
        print(f"[❌] Failed to send email: {e}")

    return {"message": f"OTP resent successfully for {purpose}."}


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
    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_access_token({"sub": user.student_id}, timedelta(minutes=60))

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "student_id": user.student_id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "college": user.college,
            "major": user.major,
            "minor": user.minor,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
        },
    }


# ---------------------------------------------------
# GET CURRENT USER (/auth/me)
# ---------------------------------------------------
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return info of the currently authenticated (logged-in) student."""
    return {
        "id": current_user.id,
        "student_id": current_user.student_id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "college": current_user.college,
        "major": current_user.major,
        "minor": current_user.minor,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,
    }

# ---------------------------------------------------
# FORGOT PASSWORD
# ---------------------------------------------------
@router.post("/forgot-password")
async def forgot_password(
    student_id: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.student_id == student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    otp_code = generate_otp()
    otp = OTP(user_id=user.id, code=otp_code, purpose=OtpPurpose.forgot_password)
    db.add(otp)
    db.commit()

    try:
        send_email(user.email, "StudentHub Password Reset", f"Your password reset OTP is: {otp_code}")
    except Exception as e:
        print(f"[❌] Email sending failed: {e}")
        raise HTTPException(status_code=500, detail="Could not send password reset OTP.")

    return {"message": "OTP sent for password reset", "user_id": user.id}


# ---------------------------------------------------
# VERIFY FORGOT PASSWORD OTP
# ---------------------------------------------------
@router.post("/verify-forgot-otp")
async def verify_forgot_otp(
    user_id: int = Form(...),
    otp_code: str = Form(...),
    db: Session = Depends(get_db),
):
    otp = (
        db.query(OTP)
        .filter(
            OTP.user_id == user_id,
            OTP.code == otp_code,
            OTP.purpose == OtpPurpose.forgot_password,
        )
        .first()
    )
    if not otp or otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    db.query(OTP).filter(OTP.user_id == user_id).delete()
    db.commit()

    return {"message": "OTP verified, you can now reset password"}


# ---------------------------------------------------
# RESET PASSWORD
# ---------------------------------------------------
@router.post("/reset-password")
async def reset_password(
    user_id: int = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(new_password)
    db.commit()

    return {"message": "Password reset successful"}


# ---------------------------------------------------
# COUNT VERIFIED STUDENTS
# ---------------------------------------------------
@router.get("/count-verified")
async def count_verified_students(db: Session = Depends(get_db)):
    """
    Return the total number of verified students in the system.
    """
    verified_count = db.query(User).filter(User.is_verified == True).count()
    return {"verified_students": verified_count}
