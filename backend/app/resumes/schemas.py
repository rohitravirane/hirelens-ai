"""
Resume Pydantic schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ResumeUpload(BaseModel):
    """Resume upload schema"""
    candidate_email: Optional[str] = None
    candidate_name: Optional[str] = None


class ResumeResponse(BaseModel):
    """Resume response schema"""
    id: int
    file_name: str
    file_size: Optional[int]
    file_type: Optional[str]
    processing_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ResumeVersionResponse(BaseModel):
    """Resume version response schema"""
    id: int
    resume_id: int
    version_number: int
    skills: Optional[List[str]]
    experience_years: Optional[int]
    education: Optional[List[Dict[str, Any]]]
    experience: Optional[List[Dict[str, Any]]]
    projects: Optional[List[Dict[str, Any]]]
    parsed_at: datetime
    quality_score: Optional[int]  # Quality score 0-100
    
    class Config:
        from_attributes = True


class ResumeDetailResponse(ResumeResponse):
    """Detailed resume response"""
    raw_text: Optional[str]
    latest_version: Optional[ResumeVersionResponse]

