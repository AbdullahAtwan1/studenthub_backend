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

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.otp import OTP, OtpPurpose
from app.models.pending_signup import PendingSignup
from app.utils.email_sender import send_email
from app.core.permissions import require_role
from app.ai.verify_bzu_card import verify_bzu_card

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
    # Remove old pending signups for same student/email
    db.query(PendingSignup).filter(
        (PendingSignup.email == email) | 
        (PendingSignup.student_id == student_id)
    ).delete()
    db.commit()

    # Cleanup expired pending signups
    db.query(PendingSignup).filter(
        PendingSignup.expires_at < datetime.utcnow()
    ).delete()
    db.commit()

    # Prevent duplicates with verified users
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.student_id == student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already registered")

    # Fetch from demo_students
    demo = db.execute(
        text("SELECT full_name, college, major, minor FROM demo_students WHERE student_id = :sid"),
        {"sid": student_id}
    ).fetchone()

    if not demo:
        raise HTTPException(status_code=404, detail="Student ID not found in demo records")

    full_name, college, major, minor = demo

    # Create media folder
    student_folder = os.path.join(MEDIA_ROOT, student_id)
    os.makedirs(student_folder, exist_ok=True)

    # Save card image
    card_path = os.path.join(student_folder, "card.jpg")
    with open(card_path, "wb") as buffer:
        shutil.copyfileobj(student_id_image.file, buffer)

    print("📸 Saved card:", card_path)

    # AI Verification
    verified, msg, face_path = verify_bzu_card(card_path, student_id, full_name)
    print("🧠 Card verification:", verified, msg)

    if not verified:
        raise HTTPException(status_code=400, detail=f"Card verification failed: {msg}")

    # Create PendingSignup
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
    db.refresh(pending)

    # Send OTP
    try:
        send_email(email, "StudentHub OTP Verification", f"Your verification code is: {otp}")
    except Exception:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {
        "message": "OTP sent to email.",
        "pending_id": pending.id,
        "auto_filled": {
            "full_name": full_name,
            "college": college,
            "major": major,
            "minor": minor,
        }
    }


# ---------------------------------------------------
# VERIFY OTP → CREATE USER
# ---------------------------------------------------
@router.post("/verify-otp")
async def verify_otp(
    otp_code: str = Form(...),
    pending_id: int = Form(...),
    db: Session = Depends(get_db),
):
    pending = db.query(PendingSignup).filter(PendingSignup.id == pending_id).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending signup not found")

    if pending.is_used or pending.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    if pending.otp_code != otp_code:
        raise HTTPException(status_code=400, detail="Incorrect OTP")

    # Ensure user does NOT already exist
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

        student_media_folder=pending.student_media_folder,
        student_card_path=pending.student_card_path,
        student_face_path=pending.student_face_path,

        is_verified=True,
        role=UserRole.student,
    )

    # Add academic info again
    demo = db.execute(
        text("SELECT college, major, minor FROM demo_students WHERE student_id = :sid"),
        {"sid": pending.student_id}
    ).fetchone()

    if demo:
        new_user.college, new_user.major, new_user.minor = demo

    db.add(new_user)
    pending.is_used = True
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Account created successfully!",
        "user_id": new_user.id,
        "student_card_path": new_user.student_card_path,
        "student_face_path": new_user.student_face_path,
    }


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
            "role": user.role,
            "club_name": user.club_name,
            "student_media_folder": user.student_media_folder,
            "student_card_path": user.student_card_path,
            "student_face_path": user.student_face_path,
        }
    }


# ---------------------------------------------------
# CURRENT USER
# ---------------------------------------------------
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------------------------------------------------
# FORGOT PASSWORD
# ---------------------------------------------------
@router.post("/forgot-password")
async def forgot_password(
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    otp = generate_otp()
    record = OTP(user_id=user.id, code=otp, purpose=OtpPurpose.forgot_password)
    db.add(record)
    db.commit()

    send_email(email, "StudentHub Password Reset", f"Your reset code: {otp}")

    return {"message": "OTP sent", "user_id": user.id}


# ---------------------------------------------------
# VERIFY FORGOT PASSWORD OTP
# ---------------------------------------------------
@router.post("/verify-forgot-otp")
async def verify_forgot_otp(
    user_id: int = Form(...),
    otp_code: str = Form(...),
    db: Session = Depends(get_db),
):
    otp = db.query(OTP).filter(
        OTP.user_id == user_id,
        OTP.code == otp_code,
        OTP.purpose == OtpPurpose.forgot_password,
    ).first()

    if not otp or otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    db.query(OTP).filter(OTP.user_id == user_id).delete()
    db.commit()

    return {"message": "OTP verified"}


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

    return {"message": "Password reset successfully"}


# ---------------------------------------------------
# COUNT VERIFIED USERS
# ---------------------------------------------------
@router.get("/count-verified")
async def count_verified(db: Session = Depends(get_db)):
    count = db.query(User).filter(User.is_verified == True).count()
    return {"verified_students": count}


# ---------------------------------------------------
# ADMIN ROLE CHANGE
# ---------------------------------------------------
@router.post("/set-role")
async def set_role(
    target_user_id: int = Form(...),
    role: UserRole = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, [UserRole.developer, UserRole.system_admin])

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role
    db.commit()

    return {"message": "Role updated", "new_role": user.role}


# ---------------------------------------------------
# ADMIN CLUB ASSIGN
# ---------------------------------------------------
@router.post("/set-club")
async def set_club(
    target_user_id: int = Form(...),
    club_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(current_user, [UserRole.developer, UserRole.system_admin])

    user = db.query(User).filter(User.id == target_user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.club_name = club_name

    if user.role == UserRole.student:
        user.role = UserRole.club_admin

    db.commit()

    return {"message": "Club updated", "role": user.role}
