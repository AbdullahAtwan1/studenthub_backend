from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from fastapi import HTTPException, status
import jwt

from app.core.config import settings

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ========== PASSWORD UTILITIES ==========

def hash_password(password: str) -> str:
    """
    Hash a user's password safely.
    Bcrypt has a 72-byte limit, so we truncate very long passwords automatically.
    """
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be empty."
        )

    safe_password = password[:72]
    return pwd_context.hash(safe_password)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if a plain text password matches the stored hashed password.
    """
    safe_password = plain_password[:72]
    return pwd_context.verify(safe_password, hashed_password)


# ========== TOKEN UTILITIES ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with an expiration time.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
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
