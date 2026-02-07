from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.models.pending_signup import PendingSignup
from app.models.user import User as UserModel
from app.models.otp import OTP
from app.models.demo_student import DemoStudent

router = APIRouter(prefix="/admin", tags=["Admin Stats"])


# ---------------------------------------------------------
# DASHBOARD STATS
# ---------------------------------------------------------
@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    return {
        "users": db.query(UserModel).count(),
        "pending": db.query(PendingSignup).count(),
        "otps_today": db.query(OTP).count(),
    }


# ---------------------------------------------------------
# GET DISTINCT MAJORS (FROM DEMO STUDENTS)
# ---------------------------------------------------------
@router.get("/majors")
def get_majors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    majors = (
        db.query(distinct(DemoStudent.major))
        .filter(DemoStudent.major.isnot(None))
        .order_by(DemoStudent.major)
        .all()
    )

    return [m[0] for m in majors]
