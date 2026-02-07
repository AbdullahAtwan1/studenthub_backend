from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.db.models import Course, CourseMaterial
from app.schemas.course_material import CourseMaterialOut, MaterialType

router = APIRouter(
    prefix="/courses",
    tags=["Course Materials Upload"],
)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
UPLOAD_ROOT = Path("uploads/courses")

ALLOWED_EXTENSIONS = {
    MaterialType.lecture: {"mp4", "mov"},
    MaterialType.slide: {"pdf", "ppt", "pptx"},
    MaterialType.exam: {"pdf", "docx"},
}

# --------------------------------------------------
# UPLOAD MATERIAL
# --------------------------------------------------
@router.post(
    "/{course_id}/materials/upload",
    response_model=CourseMaterialOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_course_material(
    course_id: int,
    material_type: MaterialType = Form(...),
    title: str = Form(...),
    doctor_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    # -----------------------------
    # Validate course
    # -----------------------------
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # -----------------------------
    # Validate file extension
    # -----------------------------
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS[material_type]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type for {material_type}",
        )

    # -----------------------------
    # Create folder
    # -----------------------------
    target_dir = UPLOAD_ROOT / str(course_id) / f"{material_type}s"
    target_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Save file
    # -----------------------------
    unique_name = f"{uuid.uuid4()}.{ext}"
    file_path = target_dir / unique_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # -----------------------------
    # Save DB record
    # -----------------------------
    material = CourseMaterial(
        title=title,
        material_type=material_type.value,
        file_url=f"/uploads/courses/{course_id}/{material_type}s/{unique_name}",
        course_id=course_id,
        doctor_id=doctor_id,
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    return material
