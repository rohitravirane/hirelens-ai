"""
Audit logging models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """Audit log for tracking all system actions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, view, etc.
    resource_type = Column(String(50), nullable=False, index=True)  # candidate, job, resume, etc.
    resource_id = Column(Integer, index=True)
    
    # Details
    details = Column(JSON)  # Additional context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

