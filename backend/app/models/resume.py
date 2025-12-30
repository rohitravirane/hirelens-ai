"""
Resume models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Resume(Base):
    """Resume model"""
    
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    file_type = Column(String(50))  # pdf, docx, etc.
    raw_text = Column(Text)  # Extracted raw text
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")
    candidate = relationship("Candidate", back_populates="resume", uselist=False)


class ResumeVersion(Base):
    """Resume version for auditability"""
    
    __tablename__ = "resume_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # Structured parsed data
    parsed_data = Column(JSON)  # Full parsed structure
    
    # Extracted fields
    skills = Column(JSON)  # List of skills
    experience_years = Column(Integer)
    education = Column(JSON)  # List of education entries
    experience = Column(JSON)  # List of experience entries
    projects = Column(JSON)  # List of projects
    certifications = Column(JSON)  # List of certifications
    languages = Column(JSON)  # List of languages
    
    # Metadata
    is_current = Column(Boolean, default=True)
    parsed_at = Column(DateTime(timezone=True), server_default=func.now())
    parser_version = Column(String(50))  # Version of parser used
    quality_score = Column(Integer)  # Quality score 0-100 for parsed data
    
    # Relationships
    resume = relationship("Resume", back_populates="versions")

