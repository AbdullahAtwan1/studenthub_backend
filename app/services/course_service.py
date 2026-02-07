from sqlalchemy.orm import Session
from sqlalchemy import distinct

from app.db.models import Course, Doctor
from app.schemas.course import CourseCreate
from app.models.demo_student import DemoStudent


# =================================================
# GET ALL MAJORS (SAFE, NO CRASH)
# =================================================
def get_all_majors(db: Session) -> list[str]:
    majors = set()

    # 1️⃣ From demo students (if exists)
    try:
        demo_majors = db.query(distinct(DemoStudent.major)).all()
        majors.update(m[0] for m in demo_majors if m and m[0])
    except Exception:
        pass  # NEVER crash dashboard

    # 2️⃣ From existing courses
    course_majors = db.query(distinct(Course.major)).all()
    majors.update(m[0] for m in course_majors if m and m[0])

    return sorted(majors)


# =================================================
# CREATE COURSE (NO HARD FAILS)
# =================================================
def create_course(db: Session, data: CourseCreate) -> Course:
    # Basic validation only
    if not data.major or not data.major.strip():
        raise ValueError("Major is required")

    # Unique course code
    if db.query(Course).filter(Course.code == data.code).first():
        raise ValueError("Course code already exists")

    course = Course(
        name=data.name,
        code=data.code,
        major=data.major,
        description=data.description,
        about=data.about,
        is_published=data.is_published,
    )

    db.add(course)
    db.flush()

    # Attach doctors (if provided)
    if data.doctor_ids:
        doctors = db.query(Doctor).filter(
            Doctor.id.in_(data.doctor_ids)
        ).all()

        if doctors:
            course.doctors.extend(doctors)

    db.commit()
    db.refresh(course)
    return course
