"""
Authentication dependencies for FastAPI routes
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import structlog

from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.user import User, Role
from app.auth.service import get_user_by_email

logger = structlog.get_logger()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise AuthenticationError("Invalid token")
    except JWTError:
        raise AuthenticationError("Invalid token")
    
    user = get_user_by_email(db, email)
    if user is None:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("User is inactive")
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    return current_user


def require_role(role_name: str):
    """
    Dependency factory for role-based access control
    Usage: @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = [role.name for role in current_user.roles]
        if role_name not in user_roles:
            logger.warning(
                "unauthorized_access_attempt",
                user_id=current_user.id,
                required_role=role_name,
                user_roles=user_roles,
            )
            raise AuthorizationError(
                f"Requires {role_name} role",
                details={"required_role": role_name, "user_roles": user_roles},
            )
        return current_user
    
    return role_checker


def require_any_role(*role_names: str):
    """
    Dependency factory for requiring any of the specified roles
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = [role.name for role in current_user.roles]
        if not any(role in user_roles for role in role_names):
            raise AuthorizationError(
                f"Requires one of: {', '.join(role_names)}",
                details={"required_roles": list(role_names), "user_roles": user_roles},
            )
        return current_user
    
    return role_checker

