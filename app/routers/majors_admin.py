from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole
from app.services.course_service import get_all_majors

router = APIRouter(prefix="/admin/majors", tags=["Admin Majors"])


@router.get("")
def list_all_majors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ SINGLE SOURCE OF TRUTH FOR MAJORS
    Used by Courses page, Doctors page, etc.
    """
    require_role(current_user, [UserRole.developer, UserRole.system_admin])
    return get_all_majors(db)
