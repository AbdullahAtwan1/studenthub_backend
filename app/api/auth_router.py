from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from sqlalchemy.orm import Session
from pathlib import Path
from jose import JWTError
from app.db.database import get_db
from app.db.models import User
from app.schemas.user_schemas import UserCreate, UserLogin, Token, UserOut
from app.services.otp_service import create_and_send_otp, verify_otp
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

def save_student_card(file: UploadFile) -> str:
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    file_path = upload_path / file.filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return str(file_path)

@router.post("/signup", response_model=UserOut)
async def signup(
    student_id: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    student_card: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists.")
    card_url = save_student_card(student_card)
    user = User(
        student_id=student_id,
        email=email,
        password_hash=hash_password(password),
        student_card_url=card_url,
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    create_and_send_otp(db, email)
    return user

@router.post("/verify-otp")
def verify_email(email: str = Form(...), code: str = Form(...), db: Session = Depends(get_db)):
    ok = verify_otp(db, email, code)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    user = db.query(User).filter(User.email == email).first()
    user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}

@router.post("/login", response_model=Token)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.student_id == body.student_id).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first.")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_profile(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")
