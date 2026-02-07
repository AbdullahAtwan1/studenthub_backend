from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from fastapi import Query

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.db.models import Course
from app.schemas.course import CourseCreate, CourseUpdate, CourseOut
from app.services.course_service import create_course, get_all_majors

router = APIRouter(prefix="/admin/courses", tags=["Admin Courses"])


# =================================================
# GET ALL MAJORS
# =================================================
@router.get("/majors", response_model=List[str])
def list_majors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.developer, UserRole.system_admin])
    return get_all_majors(db)


# =================================================
# CREATE COURSE
# =================================================
@router.post("", response_model=CourseOut)
def create_new_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.developer, UserRole.system_admin])
    return create_course(db, data)


# =================================================
# LIST COURSES  ✅ SINGLE SOURCE OF TRUTH
# =================================================
@router.get("", response_model=List[CourseOut])
def list_courses(
    major: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.developer, UserRole.system_admin])

    query = (
        db.query(Course)
        .options(joinedload(Course.doctors))
    )

    if major:
        query = query.filter(Course.major == major)

    return query.order_by(Course.id.desc()).all()


# =================================================
# UPDATE COURSE
# =================================================
@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.developer, UserRole.system_admin])

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(course, key, value)

    db.commit()
    db.refresh(course)
    return course


# =================================================
# DELETE COURSE
# =================================================
@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.developer, UserRole.system_admin])

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}

# =================================================
# PUBLIC COURSES (NO AUTH)  ✅ GUARANTEED
# =================================================
@router.get("/public", response_model=List[CourseOut])
def list_courses_public(
    major: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Course).options(joinedload(Course.doctors))

    if major:
        query = query.filter(Course.major == major)

    return query.order_by(Course.id.desc()).all()



# =================================================
# PUBLISH / UNPUBLISH COURSE  ✅ FIXED
# =================================================
@router.patch("/{course_id}/publish", response_model=CourseOut)
def publish_course(
    course_id: int,
    publish: bool = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.developer, UserRole.system_admin])

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course.is_published = publish
    db.commit()
    db.refresh(course)

    return course