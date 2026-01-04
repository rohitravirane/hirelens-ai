"""
Matching Pydantic schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class MatchResultResponse(BaseModel):
    """Match result response schema"""
    id: int
    candidate_id: int
    job_description_id: int
    overall_score: float
    confidence_level: str
    skill_match_score: float
    experience_score: float
    project_similarity_score: float
    domain_familiarity_score: float
    percentile_rank: Optional[float]
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class AIExplanationResponse(BaseModel):
    """AI explanation response schema"""
    summary: Optional[str]
    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    recommendations: Optional[List[str]]
    confidence_score: Optional[float]
    reasoning_quality: Optional[str]
    
    class Config:
        from_attributes = True


class MatchDetailResponse(MatchResultResponse):
    """Detailed match response with explanation"""
    ai_explanation: Optional[AIExplanationResponse]


class CandidateKundaliSummaryResponse(BaseModel):
    """Candidate Kundali summary for rankings"""
    name: Optional[str] = None
    total_experience_years: Optional[float] = None
    seniority_level: Optional[str] = None
    skills_frontend: Optional[List[str]] = None
    skills_backend: Optional[List[str]] = None
    skills_devops: Optional[List[str]] = None
    skills_ai_ml: Optional[List[str]] = None
    skills_tools: Optional[List[str]] = None
    skills_soft: Optional[List[str]] = None
    summary: Optional[str] = None
    overall_confidence_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class CandidateRankingResponse(BaseModel):
    """Candidate ranking response"""
    candidate_id: int
    candidate_name: Optional[str]
    candidate_email: Optional[str]
    match_result: MatchDetailResponse
    kundali: Optional[CandidateKundaliSummaryResponse] = None

