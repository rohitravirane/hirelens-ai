"""
Candidate Pydantic schemas
"""
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class CandidateCreate(BaseModel):
    """Candidate creation schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_id: int
    notes: Optional[str] = None


class CandidateUpdate(BaseModel):
    """Candidate update schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CandidateResponse(BaseModel):
    """Candidate response schema"""
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    portfolio_url: Optional[str]
    resume_id: Optional[int]
    status: str
    notes: Optional[str]
    created_at: datetime
    resume_quality_score: Optional[int] = None  # Quality score from resume (0-100)
    
    class Config:
        from_attributes = True

