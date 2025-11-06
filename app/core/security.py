from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

# ----------------------------------------------------
# Password hashing setup
# ----------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for Swagger (adds Authorize button)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ----------------------------------------------------
# PASSWORD UTILITIES
# ----------------------------------------------------
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


# ----------------------------------------------------
# TOKEN UTILITIES
# ----------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with an expiration time.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
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


# ----------------------------------------------------
# GET CURRENT USER  ✅ (needed for /auth/me)
# ----------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract the current logged-in user based on the JWT token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        student_id: str = payload.get("sub")
        if student_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Retrieve the user from the database
    user = db.query(User).filter(User.student_id == student_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return user
