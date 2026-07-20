from fastapi import Depends

from app.core.constants import UserRole
from app.core.exceptions import ForbiddenError
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User


def require_roles(*roles: UserRole):
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(
                f"This action requires one of the following roles: {', '.join(r.value for r in roles)}."
            )
        return current_user

    return _checker


require_student = require_roles(UserRole.STUDENT)
require_mentor = require_roles(UserRole.MENTOR)
require_super_admin = require_roles(UserRole.SUPER_ADMIN)
require_mentor_or_admin = require_roles(UserRole.MENTOR, UserRole.SUPER_ADMIN)
require_student_or_admin = require_roles(UserRole.STUDENT, UserRole.SUPER_ADMIN)
require_any_authenticated = require_roles(UserRole.STUDENT, UserRole.MENTOR, UserRole.SUPER_ADMIN)
