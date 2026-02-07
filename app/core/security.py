from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, APIRouter
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

# OAuth2 scheme (for Swagger + Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Router used for endpoints in this module
router = APIRouter()

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
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
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
    This is the ONLY place where jwt.decode is used.
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
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ----------------------------------------------------
# GET CURRENT USER  ✅ (FINAL FIX)
# ----------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract the current logged-in user based on the JWT token.
    """

    # ✅ Decode token using ONE unified function
    payload = decode_access_token(token)

    student_id: str | None = payload.get("sub")
    if student_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
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

# ---------------------------------------------------
# COUNT REGISTERED STUDENTS
# ---------------------------------------------------
@router.get("/count-students")
async def count_students(db: Session = Depends(get_db)):
    """
    Return the total number of registered (verified) students.
    """
    count = db.query(User).filter(User.is_verified == True).count()
    return {"total_students": count}
