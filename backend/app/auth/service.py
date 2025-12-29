"""
Authentication service layer
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
import structlog

from app.core.config import settings
from app.models.user import User, Role
from app.core.exceptions import AuthenticationError

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    role_names: Optional[list[str]] = None,
) -> User:
    """Create a new user with roles"""
    # Check if user exists
    if get_user_by_email(db, email):
        raise ValueError(f"User with email {email} already exists")
    
    # Create user
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
    )
    db.add(user)
    
    # Assign roles
    if role_names:
        roles = db.query(Role).filter(Role.name.in_(role_names)).all()
        user.roles = roles
    else:
        # Default role: recruiter
        default_role = db.query(Role).filter(Role.name == "recruiter").first()
        if default_role:
            user.roles = [default_role]
    
    db.commit()
    db.refresh(user)
    
    logger.info("user_created", user_id=user.id, email=email)
    return user


def update_user_last_login(db: Session, user: User):
    """Update user's last login timestamp"""
    user.last_login = datetime.utcnow()
    db.commit()

