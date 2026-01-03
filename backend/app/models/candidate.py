"""
Candidate models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Candidate(Base):
    """Candidate model"""
    
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Personal information
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), index=True)
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    portfolio_url = Column(String(500))
    
    # Resume reference
    resume_id = Column(Integer, ForeignKey("resumes.id"), unique=True)
    
    # Status
    status = Column(String(50), default="new")  # new, screening, interview, offer, rejected, hired
    notes = Column(Text)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resume = relationship("Resume", back_populates="candidate")
    created_by_user = relationship("User", back_populates="created_candidates")
    match_results = relationship("MatchResult", back_populates="candidate")
    kundali = relationship("CandidateKundali", back_populates="candidate", uselist=False)

