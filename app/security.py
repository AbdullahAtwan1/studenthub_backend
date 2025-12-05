# app/security.py

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException, status
import jwt

# ------------------------------------------
# 🔧 Load config or use fallback constants
# ------------------------------------------
try:
    from app.core.config import settings
    JWT_SECRET = settings.JWT_SECRET
    JWT_ALGORITHM = settings.JWT_ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
except Exception:
    JWT_SECRET = "your_secret_key_here"
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ------------------------------------------
# 🔐 Password hashing configuration
# ------------------------------------------
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# 🔐 PASSWORD UTILITIES (UTF-8 safe 72-byte truncation)
# ============================================================

def _truncate_bcrypt(password: str) -> str:
    """
    bcrypt only supports 72 BYTES, not characters.
    Arabic/Emoji characters use multiple bytes.
    This ensures we ALWAYS pass safe input to bcrypt.
    """
    if not password:
        return ""

    # Encode to UTF-8, truncate to 72 bytes, decode back safely.
    safe_bytes = password.encode("utf-8")[:72]
    return safe_bytes.decode("utf-8", "ignore")


def hash_password(password: str) -> str:
    """Hash the password safely with truncation."""
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be empty."
        )

    safe = _truncate_bcrypt(password)
    return pwd_context.hash(safe)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password safely with the same truncation rule."""
    safe = _truncate_bcrypt(plain_password)
    return pwd_context.verify(safe, hashed_password)


# ============================================================
# 🔑 JWT TOKEN UTILITIES
# ============================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode a JWT token safely."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired."
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token."
        )
