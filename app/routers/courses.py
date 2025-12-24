# app/routers/courses.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.models.content import Course, CourseProgress
from app.schemas.content_schemas import CourseCreate, CourseOut, CourseProgressOut, CourseProgressBase
from app.db.session import SessionLocal


router = APIRouter(prefix="/courses", tags=["courses"])

@router.post("/", response_model=CourseOut)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    course = Course(**payload.dict())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

@router.get("/", response_model=List[CourseOut])
def list_courses(limit:int=10, skip:int=0, db: Session = Depends(get_db)):
    courses = db.query(Course).order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return courses

@router.post("/progress", response_model=CourseProgressOut)
def update_progress(payload: CourseProgressBase, db: Session = Depends(get_db)):
    p = db.query(CourseProgress).filter_by(user_id=payload.user_id, course_id=payload.course_id).first()
    if not p:
        p = CourseProgress(**payload.dict())
        db.add(p)
    else:
        p.progress_percent = payload.progress_percent
        p.status = payload.status
    db.commit()
    db.refresh(p)
    return p

# simple image upload helper (optional)
@router.post("/upload-thumbnail")
def upload_thumbnail(file: UploadFile = File(...)):
    # Simple local save; adapt to project's storage
    save_path = f"uploads/course_thumbs/{file.filename}"
    import os
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(file.file.read())
    return {"url": save_path}
