from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.db.database import get_db

router = APIRouter(prefix="/admin", tags=["Admin Stats"])

@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    # 1. Total registered students
    total_students = db.execute("SELECT COUNT(*) FROM demo_students").scalar()

    # 2. Active users
    active_users = db.execute("SELECT COUNT(*) FROM users").scalar()

    # 3. Pending signups
    pending = db.execute("SELECT COUNT(*) FROM pending_signups").scalar()

    # 4. OTP requests today
    otps_today = db.execute(
        "SELECT COUNT(*) FROM otps WHERE DATE(created_at) = CURDATE()"
    ).scalar()

    # 5. Active slider images
    slider_count = db.execute(
        "SELECT COUNT(*) FROM home_slider WHERE is_active = 1"
    ).scalar()

    return {
        "students": total_students,
        "active_users": active_users,
        "pending_signups": pending,
        "otps_today": otps_today,
        "slider_images": slider_count,
    }
