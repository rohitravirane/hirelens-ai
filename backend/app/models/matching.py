"""
Matching and scoring models
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Boolean, Index, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MatchResult(Base):
    """Match result between candidate and job"""
    
    __tablename__ = "match_results"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False, index=True)
    
    # Overall score
    overall_score = Column(Float, nullable=False, index=True)  # 0-100
    confidence_level = Column(String(20))  # high, medium, low
    
    # Dimension scores
    skill_match_score = Column(Float)  # 0-100
    experience_score = Column(Float)  # 0-100
    project_similarity_score = Column(Float)  # 0-100
    domain_familiarity_score = Column(Float)  # 0-100
    
    # Percentile
    percentile_rank = Column(Float)  # 0-100
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate = relationship("Candidate", back_populates="match_results")
    job_description = relationship("JobDescription", back_populates="match_results")
    ai_explanation = relationship("AIExplanation", back_populates="match_result", uselist=False, cascade="all, delete-orphan")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index("idx_candidate_job", "candidate_id", "job_description_id"),
    )


class AIExplanation(Base):
    """AI-generated explanation for match result"""
    
    __tablename__ = "ai_explanations"
    
    id = Column(Integer, primary_key=True, index=True)
    match_result_id = Column(Integer, ForeignKey("match_results.id"), unique=True, nullable=False)
    
    # Explanation text
    summary = Column(Text)  # Overall summary
    strengths = Column(JSON)  # List of strengths
    weaknesses = Column(JSON)  # List of weaknesses/gaps
    recommendations = Column(JSON)  # List of recommendations
    
    # Detailed analysis
    skill_analysis = Column(JSON)  # Detailed skill match analysis
    experience_analysis = Column(JSON)  # Experience relevance analysis
    gap_analysis = Column(JSON)  # Missing skills/experience
    
    # Confidence metrics
    confidence_score = Column(Float)  # 0-1
    reasoning_quality = Column(String(20))  # high, medium, low
    
    # Metadata
    model_used = Column(String(100))  # Which AI model was used
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    match_result = relationship("MatchResult", back_populates="ai_explanation")

