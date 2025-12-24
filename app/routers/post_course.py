# app/routers/post_course.py
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.content import Course
import os
from app.schemas.content_schemas import CourseOut

router = APIRouter(prefix="/post", tags=["post"])

@router.post("/course", response_model=CourseOut)
async def post_course(
    title: str = Form(...),
    description: str = Form(None),
    condition: str = Form(None),
    category: str = Form(None),
    file: UploadFile | None = None,
    db: Session = Depends(get_db)
):
    thumbnail_path = None
    if file:
        save_dir = "uploads/course_images"
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        thumbnail_path = file_path

    course = Course(title=title, description=description, thumbnail=thumbnail_path)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course
