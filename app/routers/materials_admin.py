from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.db.models import CourseMaterial

from app.db.models import Doctor
from app.db.models import CourseMaterial
from app.db.models import Course


from app.schemas.course_material import (
    CourseMaterialCreate,
    CourseMaterialOut,
)

router = APIRouter(
    prefix="/admin/materials",
    tags=["Course Materials"],
)


# ---------------------------------------------------------
# CREATE MATERIAL
# ---------------------------------------------------------
@router.post("", response_model=CourseMaterialOut)
def create_material(
    data: CourseMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    material = CourseMaterial(
        title=data.title,
        type=data.type,
        file_url=data.file_url,
        video_url=data.video_url,
        course_id=data.course_id,
        doctor_id=data.doctor_id,
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    return material


# ---------------------------------------------------------
# LIST MATERIALS BY COURSE
# ---------------------------------------------------------
@router.get("/course/{course_id}", response_model=List[CourseMaterialOut])
def list_course_materials(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    return (
        db.query(CourseMaterial)
        .filter(CourseMaterial.course_id == course_id)
        .order_by(CourseMaterial.created_at.desc())
        .all()
    )


# ---------------------------------------------------------
# DELETE MATERIAL
# ---------------------------------------------------------
@router.delete("/{material_id}")
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    material = db.query(CourseMaterial).filter(
        CourseMaterial.id == material_id
    ).first()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    db.delete(material)
    db.commit()

    return {"message": "Material deleted successfully"}
