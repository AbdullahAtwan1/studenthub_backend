from fastapi import HTTPException, status
from app.models.user import User, UserRole


def require_role(current_user: User, allowed_roles: list[UserRole]):
    """
    Simple role-based access check.
    If the current user's role is not in allowed_roles, raise 403.
    """
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied for role: {current_user.role}",
        )

