# app/routers/auth.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
import shutil, os, random, string
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.user import User
from app.models.otp import OTP, OtpPurpose
from app.security import hash_password, verify_password, create_access_token
from app.utils.email_sender import send_email  # ✅ added import

router = APIRouter()
UPLOAD_DIR = "uploads/student_ids"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Helper ---
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


# ---------- SIGN UP ----------
@router.post("/signup")
async def signup(
    student_id: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    student_id_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_sid = db.query(User).filter(User.student_id == student_id).first()
    if existing_sid:
        raise HTTPException(status_code=400, detail="Student ID already registered")

    image_path = os.path.join(UPLOAD_DIR, f"{student_id}_{student_id_image.filename}")
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(student_id_image.file, buffer)

    new_user = User(
        student_id=student_id,
        full_name=full_name,
        email=email,
        phone=phone,
        password=hash_password(password),
        student_id_image=image_path,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    otp_code = generate_otp()
    otp = OTP(user_id=new_user.id, code=otp_code, purpose=OtpPurpose.signup)
    db.add(otp)
    db.commit()

    # ✅ Send OTP email
    print(f"[DEBUG] OTP for signup: {otp_code}")
    try:
        send_email(email, "StudentHub OTP Verification", f"Your StudentHub verification code is: {otp_code}")
    except Exception as e:
        print(f"[❌] Email sending failed: {e}")
        raise HTTPException(status_code=500, detail="Could not send OTP email. Please try again.")

    return {"message": "OTP sent to email.", "user_id": new_user.id}


# ---------- VERIFY OTP ----------
@router.post("/verify-otp")
async def verify_otp(user_id: int = Form(...), otp_code: str = Form(...), db: Session = Depends(get_db)):
    print("DEBUG: verifying OTP")
    print("DEBUG: received user_id =", user_id)
    print("DEBUG: received otp_code =", otp_code)
    otp = db.query(OTP).filter(OTP.user_id == user_id, OTP.code == otp_code).first()
    print("DEBUG: OTP from DB =", otp)

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.query(OTP).filter(OTP.user_id == user_id).delete()
    db.commit()
    return {"message": "Account verified successfully!"}


# ---------- RESEND OTP ----------
# send_email is already imported above from app.utils.email_sender

@router.post("/resend-otp")
async def resend_otp(
    user_id: int = Form(...),
    purpose: str = Form(...),  # 'signup' or 'forgot_password'
    db: Session = Depends(get_db)
):
    purpose = purpose.lower().strip()
    if purpose not in ["signup", "forgot_password"]:
        raise HTTPException(status_code=400, detail="Invalid purpose")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp_code = ''.join(random.choices(string.digits, k=6))
    otp = OTP(user_id=user.id, code=otp_code, purpose=purpose)
    db.add(otp)
    db.commit()

     # --- Send Email ---
    try:
        subject = "StudentHub OTP Verification"
        body = f"Your StudentHub {purpose.replace('_', ' ')} OTP code is: {otp_code}"
        send_email(user.email, subject, body)
        print(f"[✅] Resent OTP {otp_code} sent to {user.email}")
    except Exception as e:
        print(f"[❌] Failed to send email: {e}")

    return {"message": f"OTP resent successfully for {purpose}."}
# ---------- LOGIN ----------
@router.post("/login")
async def login(student_id: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.student_id == student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Account not verified")
    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_access_token({"sub": user.student_id}, timedelta(minutes=60))
    return {"message": "Login successful", "access_token": token}


# ---------- FORGOT PASSWORD ----------
@router.post("/forgot-password")
async def forgot_password(student_id: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.student_id == student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    otp_code = generate_otp()
    otp = OTP(user_id=user.id, code=otp_code, purpose=OtpPurpose.forgot_password)
    db.add(otp)
    db.commit()
    print(f"[DEBUG] OTP for password reset: {otp_code}")

    try:
        send_email(user.email, "StudentHub Password Reset", f"Your password reset OTP is: {otp_code}")
    except Exception as e:
        print(f"[❌] Email sending failed: {e}")
        raise HTTPException(status_code=500, detail="Could not send password reset OTP.")

    return {"message": "OTP sent for password reset", "user_id": user.id}


# ---------- VERIFY FORGOT PASSWORD OTP ----------
@router.post("/verify-forgot-otp")
async def verify_forgot_otp(user_id: int = Form(...), otp_code: str = Form(...), db: Session = Depends(get_db)):
    otp = db.query(OTP).filter(
        OTP.user_id == user_id,
        OTP.code == otp_code,
        OTP.purpose == OtpPurpose.forgot_password
    ).first()
    if not otp or otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    db.query(OTP).filter(OTP.user_id == user_id).delete()
    db.commit()
    return {"message": "OTP verified, you can now reset password"}


# ---------- RESET PASSWORD ----------
@router.post("/reset-password")
async def reset_password(user_id: int = Form(...), new_password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(get_db)):
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(new_password)
    db.commit()
    return {"message": "Password reset successful"}
