"""
Job Description models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class JobDescription(Base):
    """Job Description model"""
    
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255))
    department = Column(String(255))
    
    # Raw input
    raw_text = Column(Text)  # Original JD text
    file_path = Column(String(500))  # If uploaded as file
    
    # Extracted/parsed data
    parsed_data = Column(JSON)  # Full parsed structure
    
    # Extracted fields
    required_skills = Column(JSON)  # List of required skills
    nice_to_have_skills = Column(JSON)  # List of nice-to-have skills
    experience_years_required = Column(Integer)
    seniority_level = Column(String(50))  # junior, mid, senior, lead, etc.
    education_requirements = Column(JSON)
    location = Column(String(255))
    remote_allowed = Column(Boolean, default=False)
    employment_type = Column(String(50))  # full-time, part-time, contract, etc.
    
    # AI processing
    embedding = Column(JSON)  # Vector embedding for semantic search
    processed_at = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by_user = relationship("User", back_populates="created_jobs")
    match_results = relationship("MatchResult", back_populates="job_description")

