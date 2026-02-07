from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import UserRole, User

router = APIRouter(prefix="/admin", tags=["Majors"])


@router.get("/majors")
def get_majors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    result = db.execute(
        text("SELECT DISTINCT major FROM demo_students WHERE major IS NOT NULL ORDER BY major")
    )

    majors = [row[0] for row in result.fetchall()]
    return majors
