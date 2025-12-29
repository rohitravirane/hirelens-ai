"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.auth.dependencies import get_current_active_user
from app.auth.service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    update_user_last_login,
)
from app.auth.schemas import (
    Token,
    LoginRequest,
    UserCreate,
    UserResponse,
    RefreshTokenRequest,
)
from app.models.user import User
from app.core.config import settings
from datetime import timedelta
from jose import jwt, JWTError

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
logger = structlog.get_logger()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a new user"""
    try:
        user = create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role_names=user_data.role_names,
        )
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=[role.name for role in user.roles],
            created_at=user.created_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user and return tokens"""
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        logger.warning("failed_login_attempt", email=credentials.email)
        raise AuthenticationError("Incorrect email or password")
    
    if not user.is_active:
        raise AuthenticationError("User account is inactive")
    
    # Update last login
    update_user_last_login(db, user)
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": user.id})
    
    logger.info("user_logged_in", user_id=user.id, email=user.email)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(
            token_data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        
        email: str = payload.get("sub")
        if email is None:
            raise AuthenticationError("Invalid token")
        
        from app.auth.service import get_user_by_email
        user = get_user_by_email(db, email)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires,
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except JWTError:
        raise AuthenticationError("Invalid refresh token")


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        roles=[role.name for role in current_user.roles],
        created_at=current_user.created_at,
    )

