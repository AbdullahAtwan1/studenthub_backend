from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.db.models import OTP
from app.core.email_service import send_otp_email

def generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"

def create_and_send_otp(db: Session, email: str):
    code = generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=10)
    otp = OTP(email=email, code=code, expires_at=expires)
    db.add(otp)
    db.commit()
    send_otp_email(email, code)

def verify_otp(db: Session, email: str, code: str) -> bool:
    record = (
        db.query(OTP)
        .filter(
            OTP.email == email,
            OTP.code == code,
            OTP.expires_at > datetime.utcnow(),
            OTP.used == False,
        )
        .order_by(OTP.id.desc())
        .first()
    )
    if not record:
        return False
    record.used = True
    db.commit()
    return True
