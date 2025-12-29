"""
Job description Pydantic schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class JobDescriptionCreate(BaseModel):
    """Job description creation schema"""
    title: str = Field(..., min_length=1, max_length=255)
    company: Optional[str] = None
    department: Optional[str] = None
    raw_text: str = Field(..., min_length=50)
    location: Optional[str] = None
    remote_allowed: bool = False
    employment_type: Optional[str] = None


class JobDescriptionUpdate(BaseModel):
    """Job description update schema"""
    title: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    raw_text: Optional[str] = None
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None


class JobDescriptionResponse(BaseModel):
    """Job description response schema"""
    id: int
    title: str
    company: Optional[str]
    department: Optional[str]
    required_skills: Optional[List[str]]
    nice_to_have_skills: Optional[List[str]]
    experience_years_required: Optional[int]
    seniority_level: Optional[str]
    location: Optional[str]
    remote_allowed: bool
    employment_type: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobDescriptionDetailResponse(JobDescriptionResponse):
    """Detailed job description response"""
    raw_text: Optional[str]
    education_requirements: Optional[List[str]]
    parsed_data: Optional[Dict[str, Any]]

