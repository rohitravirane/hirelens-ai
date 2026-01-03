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
    skills: Optional[List[str]]  # Flattened list of all skills (technical, languages, tools, frameworks)
    experience_years: Optional[int]
    education: Optional[List[Dict[str, Any]]]
    experience: Optional[List[Dict[str, Any]]]
    projects: Optional[List[Dict[str, Any]]]
    parsed_at: datetime
    quality_score: Optional[int]  # Quality score 0-100
    # Personal information extracted from resume
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    
    @classmethod
    def normalize_skills(cls, skills: Any) -> Optional[List[str]]:
        """Normalize skills from dict or list format to flat list"""
        if skills is None:
            return None
        if isinstance(skills, list):
            return skills if all(isinstance(s, str) for s in skills) else None
        if isinstance(skills, dict):
            # Flatten dict format: {"technical": [...], "languages": [...], "tools": [...], "frameworks": [...]}
            flattened = []
            for category in ["technical", "languages", "tools", "frameworks"]:
                if category in skills and isinstance(skills[category], list):
                    flattened.extend(skills[category])
            return flattened if flattened else None
        return None
    
    class Config:
        from_attributes = True


class ResumeDetailResponse(ResumeResponse):
    """Detailed resume response"""
    raw_text: Optional[str]
    latest_version: Optional[ResumeVersionResponse]

