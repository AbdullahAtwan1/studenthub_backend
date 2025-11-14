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
import shutil, os, random, string
from datetime import datetime, timedelta

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.otp import OTP, OtpPurpose
from app.models.pending_signup import PendingSignup
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.utils.email_sender import send_email
from app.core.permissions import require_role

router = APIRouter()

UPLOAD_DIR = "uploads/student_ids"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------
# Helper
# ---------------------------------------------------
def generate_otp() -> str:
    """Generate a 6-digit numeric OTP."""
    return "".join(random.choices(string.digits, k=6))


# ---------------------------------------------------
# SIGN UP  (NO USER ROW UNTIL OTP VERIFIED)
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
    # 1) Clean old pending signups for same student/email
    db.query(PendingSignup).filter(PendingSignup.email == email).delete()
    db.query(PendingSignup).filter(PendingSignup.student_id == student_id).delete()
    db.commit()

    # Optional: clean expired general pending signups
    db.query(PendingSignup).filter(PendingSignup.expires_at < datetime.utcnow()).delete()
    db.commit()

    # 2) Prevent if already verified user exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.student_id == student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already registered")

    # 3) Fetch from demo_students
    demo_student = db.execute(
        text("SELECT full_name, college, major, minor FROM demo_students WHERE student_id = :sid"),
        {"sid": student_id}
    ).fetchone()

    if not demo_student:
        raise HTTPException(status_code=404, detail="Student ID not found in demo records")

    full_name, college, major, minor = demo_student

    # 4) Save student_id image
    image_path = os.path.join(UPLOAD_DIR, f"{student_id}_{student_id_image.filename}")
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(student_id_image.file, buffer)

    # 5) Create OTP + PendingSignup
    otp_code = generate_otp()
    pending = PendingSignup(
        student_id=student_id,
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        student_id_image=image_path,
        otp_code=otp_code,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        is_used=False,
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)

    # 6) Send OTP email
    try:
        send_email(email, "StudentHub OTP Verification", f"Your verification code is: {otp_code}")
    except Exception:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=500, detail="Could not send OTP email.")

    return {
        "message": "OTP sent to email.",
        "pending_id": pending.id,
        "auto_filled": {
            "full_name": full_name,
            "college": college,
            "major": major,
            "minor": minor,
        },
    }


# ---------------------------------------------------
# VERIFY OTP (SIGNUP) — creates the user NOW
# ---------------------------------------------------
@router.post("/verify-otp")
async def verify_otp(
    otp_code: str = Form(...),
    pending_id: int | None = Form(None),   # new flow (use this)
    user_id: int | None = Form(None),      # legacy (kept if old app still uses it)
    db: Session = Depends(get_db),
):
    # New flow with pending_id
    if pending_id is not None:
        pending = db.query(PendingSignup).filter(PendingSignup.id == pending_id).first()
        if not pending:
            raise HTTPException(status_code=404, detail="Pending signup not found")

        if pending.is_used or pending.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        if pending.otp_code != otp_code:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        # Double-check uniqueness (in case something changed meanwhile)
        if db.query(User).filter(User.email == pending.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        if db.query(User).filter(User.student_id == pending.student_id).first():
            raise HTTPException(status_code=400, detail="Student ID already registered")

        # Create final user
        new_user = User(
            student_id=pending.student_id,
            full_name=pending.full_name,
            email=pending.email,
            phone=pending.phone,
            password=pending.password_hash,
            student_id_image=pending.student_id_image,
            is_verified=True,
            role=UserRole.student,   # default role for signup
            club_name=None,
        )

        # Fill college, major, minor again from demo_students
        demo_student = db.execute(
            text("SELECT college, major, minor FROM demo_students WHERE student_id = :sid"),
            {"sid": pending.student_id}
        ).fetchone()
        if demo_student:
            new_user.college, new_user.major, new_user.minor = demo_student

        db.add(new_user)
        pending.is_used = True
        db.commit()
        db.refresh(new_user)

        return {"message": "Account created & verified successfully!", "user_id": new_user.id}

    # Legacy flow (if old mobile code still sends user_id)
    if user_id is not None:
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

    raise HTTPException(status_code=400, detail="You must provide pending_id (new) or user_id (legacy).")


# ---------------------------------------------------
# RESEND OTP (legacy - kept for forgot_password)
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
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

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
            "role": user.role,
            "club_name": user.club_name,
        },
    }


# ---------------------------------------------------
# GET CURRENT USER (/auth/me)
# ---------------------------------------------------
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
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
        "role": current_user.role,
        "club_name": current_user.club_name,
    }


# ---------------------------------------------------
# FORGOT PASSWORD — uses EMAIL
# ---------------------------------------------------
@router.post("/forgot-password")
async def forgot_password(
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    otp_code = generate_otp()
    otp = OTP(user_id=user.id, code=otp_code, purpose=OtpPurpose.forgot_password)
    db.add(otp)
    db.commit()

    try:
        send_email(user.email, "StudentHub Password Reset", f"Your password reset OTP is: {otp_code}")
    except Exception:
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
    verified_count = db.query(User).filter(User.is_verified == True).count()
    return {"verified_students": verified_count}


# ---------------------------------------------------
# ADMIN: SET USER ROLE (developer / council_head / club_admin / etc.)
# ---------------------------------------------------
@router.post("/set-role")
async def set_role(
    target_user_id: int = Form(...),
    role: UserRole = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only developer or system_admin can change roles
    require_role(current_user, [UserRole.developer, UserRole.system_admin])

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Target user not found")

    user.role = role
    db.commit()
    db.refresh(user)

    return {"message": "Role updated successfully", "user_id": user.id, "new_role": user.role}


# ---------------------------------------------------
# ADMIN: SET CLUB FOR USER (make them club_admin if needed)
# ---------------------------------------------------
@router.post("/set-club")
async def set_club(
    target_user_id: int = Form(...),
    club_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only developer or system_admin can assign clubs
    require_role(current_user, [UserRole.developer, UserRole.system_admin])

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Target user not found")

    user.club_name = club_name

    # If still a normal student, upgrade to club_admin
    if user.role == UserRole.student:
        user.role = UserRole.club_admin

    db.commit()
    db.refresh(user)

    return {
        "message": "Club assigned successfully",
        "user_id": user.id,
        "role": user.role,
        "club_name": user.club_name,
    }
