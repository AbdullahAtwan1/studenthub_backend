from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import os
import shutil

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User


router = APIRouter(prefix="/students", tags=["Students"])

PROFILE_DIR = "uploads/student_media/profile"
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def _get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _validate_image(upload: UploadFile):
    ext = _get_extension(upload.filename)

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image type. Allowed: jpg, jpeg, png."
        )

    # Validate size without reading into memory
    try:
        upload.file.seek(0, os.SEEK_END)
        size = upload.file.tell()
        upload.file.seek(0)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded file."
        )

    if size > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image is too large. Max size is 5MB."
        )

    return ext


def _safe_remove(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        # We do not crash if delete fails; we keep it safe
        pass


@router.post("/profile-picture")
def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logged-in student updates their profile picture.
    Saves image in uploads/student_media/profile/
    and stores the public path in users.profile_image.
    """

    os.makedirs(PROFILE_DIR, exist_ok=True)

    ext = _validate_image(file)

    # Re-load user in this DB session (avoid session mismatch)
    user = db.query(User).filter(User.student_id == current_user.student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Delete old profile image if exists
    if user.profile_image:
        old_disk_path = user.profile_image.lstrip("/")  # "/uploads/..." -> "uploads/..."
        _safe_remove(old_disk_path)

    # Also remove any previous extension variants (extra safety)
    base_name = f"student_{user.student_id}"
    for e in ALLOWED_EXTENSIONS:
        _safe_remove(os.path.join(PROFILE_DIR, f"{base_name}.{e}"))

    # Save new file
    filename = f"{base_name}.{ext}"
    disk_path = os.path.join(PROFILE_DIR, filename)

    try:
        with open(disk_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image."
        )

    # Store public path
    public_path = f"/uploads/student_media/profile/{filename}"
    user.profile_image = public_path
    db.commit()
    db.refresh(user)

    return {
        "message": "Profile picture updated successfully",
        "profile_image": user.profile_image,
    }


@router.post("/cover-photo")
def upload_cover_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logged-in student updates their cover photo.
    """

    COVER_DIR = "uploads/student_media/cover"
    os.makedirs(COVER_DIR, exist_ok=True)

    ext = _validate_image(file)

    user = db.query(User).filter(
        User.student_id == current_user.student_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Delete old cover image
    if user.cover_image:
        old_path = user.cover_image.lstrip("/")
        _safe_remove(old_path)

    # Remove any old extensions (safety)
    base_name = f"student_{user.student_id}"
    for e in ALLOWED_EXTENSIONS:
        _safe_remove(os.path.join(COVER_DIR, f"{base_name}.{e}"))

    # Save new cover image
    filename = f"{base_name}.{ext}"
    disk_path = os.path.join(COVER_DIR, filename)

    with open(disk_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    public_path = f"/uploads/student_media/cover/{filename}"
    user.cover_image = public_path

    db.commit()
    db.refresh(user)

    return {
        "message": "Cover photo updated successfully",
        "cover_image": user.cover_image,
    }