"""Authentication & role-based-access-control dependencies.

``get_current_user`` decodes the bearer token; ``require_roles`` builds a
dependency that 403s unless the caller holds one of the allowed roles. These
are injected into routers to enforce the four-role tailored access model.
"""
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.database import get_db
from app.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise creds_exc
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if user is None or not user.is_active:
        raise creds_exc
    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    allowed = set(roles)

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource",
            )
        return user

    return checker


# Convenience role groups
ADMIN = UserRole.MANAGEMENT_ADMIN
MANAGER = UserRole.SENIOR_MANAGER
RECRUITER = UserRole.HR_RECRUITER
EMPLOYEE = UserRole.EMPLOYEE

is_admin = require_roles(ADMIN)
is_manager_or_admin = require_roles(ADMIN, MANAGER)
is_recruiter_staff = require_roles(ADMIN, MANAGER, RECRUITER)
