from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.orm import Session
from typing import Dict, List
import os
import uuid

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.db.models import Course, CourseMaterial
from app.schemas.course_material import CourseMaterialOut, MaterialType

router = APIRouter(
    prefix="/courses",
    tags=["Course Materials"],
)

# =================================================
# FILE STORAGE
# =================================================
BASE_UPLOAD_DIR = "uploads"
VIDEO_DIR = os.path.join(BASE_UPLOAD_DIR, "videos")
FILE_DIR = os.path.join(BASE_UPLOAD_DIR, "files")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(FILE_DIR, exist_ok=True)

# =================================================
# UPLOAD MATERIAL (LECTURE / SLIDE / EXAM)
# =================================================
@router.post(
    "/{course_id}/materials/upload",
    response_model=CourseMaterialOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_material(
    course_id: int,
    title: str = Form(...),
    material_type: MaterialType = Form(...),
    doctor_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    ext = file.filename.split(".")[-1].lower()
    uid = str(uuid.uuid4())

    # ---------- LECTURE (VIDEO) ----------
    if material_type == MaterialType.lecture:
        if ext not in ["mp4", "mov", "avi"]:
            raise HTTPException(status_code=400, detail="Invalid video file")

        filename = f"{uid}.{ext}"
        path = os.path.join(VIDEO_DIR, filename)

        with open(path, "wb") as buffer:
            buffer.write(file.file.read())

        material = CourseMaterial(
            course_id=course_id,
            title=title,
            material_type=material_type.value,
            video_url=f"/uploads/videos/{filename}",
            doctor_id=doctor_id,
        )

    # ---------- SLIDE / EXAM (PDF) ----------
    else:
        if ext != "pdf":
            raise HTTPException(status_code=400, detail="PDF required")

        filename = f"{uid}.pdf"
        path = os.path.join(FILE_DIR, filename)

        with open(path, "wb") as buffer:
            buffer.write(file.file.read())

        material = CourseMaterial(
            course_id=course_id,
            title=title,
            material_type=material_type.value,
            file_url=f"/uploads/files/{filename}",
            doctor_id=doctor_id,
        )

    db.add(material)
    db.commit()
    db.refresh(material)
    return material

# =================================================
# EDIT MATERIAL TITLE ✏️
# =================================================
@router.put(
    "/materials/{material_id}",
    response_model=CourseMaterialOut,
)
def update_material_title(
    material_id: int,
    title: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    material = db.query(CourseMaterial).filter(CourseMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    material.title = title
    db.commit()
    db.refresh(material)
    return material

# =================================================
# DELETE MATERIAL 🗑
# =================================================
@router.delete(
    "/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    material = db.query(CourseMaterial).filter(CourseMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # Remove physical file
    if material.video_url:
        path = material.video_url.lstrip("/")
    elif material.file_url:
        path = material.file_url.lstrip("/")
    else:
        path = None

    if path and os.path.exists(path):
        os.remove(path)

    db.delete(material)
    db.commit()

# =================================================
# LIST MATERIALS (FLUTTER-READY GROUPED 📦)
# =================================================
@router.get(
    "/{course_id}/materials",
    response_model=Dict[str, List[CourseMaterialOut]],
)
def list_materials_grouped(
    course_id: int,
    db: Session = Depends(get_db),
):
    if not db.query(Course.id).filter(Course.id == course_id).first():
        raise HTTPException(status_code=404, detail="Course not found")

    materials = (
        db.query(CourseMaterial)
        .filter(CourseMaterial.course_id == course_id)
        .order_by(CourseMaterial.created_at.desc())
        .all()
    )

    return {
        "lectures": [m for m in materials if m.material_type == "lecture"],
        "slides": [m for m in materials if m.material_type == "slide"],
        "exams": [m for m in materials if m.material_type == "exam"],
    }
