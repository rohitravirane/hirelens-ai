"""
Authentication Pydantic schemas
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data schema"""
    email: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8)
    role_names: Optional[List[str]] = None


class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    is_verified: bool
    roles: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class RoleResponse(BaseModel):
    """Role response schema"""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

