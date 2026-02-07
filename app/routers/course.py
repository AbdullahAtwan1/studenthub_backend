from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import Course

from app.schemas.course import CourseCreate, CourseOut, CourseUpdate
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


# =========================
# CREATE COURSE (ADMIN)
# =========================
@router.post("/", response_model=CourseOut)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.developer, UserRole.system_admin])

    course = Course(**data.dict())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


# =========================
# LIST COURSES (PUBLIC)
# =========================
@router.get("/", response_model=List[CourseOut])
def list_courses(
    major: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Course).filter(Course.is_published == True)

    if major:
        query = query.filter(Course.major == major)

    return query.all()


# =========================
# UPDATE COURSE (ADMIN)
# =========================
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
