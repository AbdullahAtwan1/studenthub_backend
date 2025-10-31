import random
from datetime import datetime, timedelta
from app.core.config import settings

def generate_otp() -> str:
    return "".join(random.choices("0123456789", k=settings.OTP_LENGTH))

def expiry_from_now() -> datetime:
    return datetime.utcnow() + timedelta(minutes=settings.OTP_TTL_MINUTES)
