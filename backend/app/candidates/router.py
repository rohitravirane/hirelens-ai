"""
Candidate routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.candidate import Candidate
from app.models.resume import Resume, ResumeVersion
from app.candidates.schemas import CandidateCreate, CandidateUpdate, CandidateResponse

router = APIRouter(prefix="/api/v1/candidates", tags=["Candidates"])
logger = structlog.get_logger()


@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(
    candidate_data: CandidateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new candidate"""
    # Verify resume exists
    resume = db.query(Resume).filter(Resume.id == candidate_data.resume_id).first()
    if not resume:
        raise NotFoundError("Resume", str(candidate_data.resume_id))
    
    # Check if candidate already exists with this resume
    existing = db.query(Candidate).filter(Candidate.resume_id == candidate_data.resume_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate already exists for this resume",
        )
    
    candidate = Candidate(
        first_name=candidate_data.first_name,
        last_name=candidate_data.last_name,
        email=candidate_data.email,
        phone=candidate_data.phone,
        linkedin_url=candidate_data.linkedin_url,
        portfolio_url=candidate_data.portfolio_url,
        resume_id=candidate_data.resume_id,
        notes=candidate_data.notes,
        created_by=current_user.id,
    )
    
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    logger.info("candidate_created", candidate_id=candidate.id)
    
    return CandidateResponse(
        id=candidate.id,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        email=candidate.email,
        phone=candidate.phone,
        linkedin_url=candidate.linkedin_url,
        portfolio_url=candidate.portfolio_url,
        resume_id=candidate.resume_id,
        status=candidate.status,
        notes=candidate.notes,
        created_at=candidate.created_at,
    )


@router.get("/", response_model=List[CandidateResponse])
def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List candidates"""
    query = db.query(Candidate)
    
    if status:
        query = query.filter(Candidate.status == status)
    
    candidates = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for c in candidates:
        # Get resume quality score if resume exists
        resume_quality_score = None
        if c.resume_id:
            latest_version = (
                db.query(ResumeVersion)
                .filter(ResumeVersion.resume_id == c.resume_id, ResumeVersion.is_current == True)
                .first()
            )
            if latest_version:
                resume_quality_score = latest_version.quality_score
        
        result.append(
            CandidateResponse(
                id=c.id,
                first_name=c.first_name,
                last_name=c.last_name,
                email=c.email,
                phone=c.phone,
                linkedin_url=c.linkedin_url,
                portfolio_url=c.portfolio_url,
                resume_id=c.resume_id,
                status=c.status,
                notes=c.notes,
                created_at=c.created_at,
                resume_quality_score=resume_quality_score,
            )
        )
    
    return result


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get candidate details"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise NotFoundError("Candidate", str(candidate_id))
    
    # Get resume quality score if resume exists
    resume_quality_score = None
    if candidate.resume_id:
        latest_version = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.resume_id == candidate.resume_id, ResumeVersion.is_current == True)
            .first()
        )
        if latest_version:
            resume_quality_score = latest_version.quality_score
    
    return CandidateResponse(
        id=candidate.id,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        email=candidate.email,
        phone=candidate.phone,
        linkedin_url=candidate.linkedin_url,
        portfolio_url=candidate.portfolio_url,
        resume_id=candidate.resume_id,
        status=candidate.status,
        notes=candidate.notes,
        created_at=candidate.created_at,
        resume_quality_score=resume_quality_score,
    )


@router.put("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(
    candidate_id: int,
    candidate_data: CandidateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise NotFoundError("Candidate", str(candidate_id))
    
    # Update fields
    if candidate_data.first_name is not None:
        candidate.first_name = candidate_data.first_name
    if candidate_data.last_name is not None:
        candidate.last_name = candidate_data.last_name
    if candidate_data.email is not None:
        candidate.email = candidate_data.email
    if candidate_data.phone is not None:
        candidate.phone = candidate_data.phone
    if candidate_data.linkedin_url is not None:
        candidate.linkedin_url = candidate_data.linkedin_url
    if candidate_data.portfolio_url is not None:
        candidate.portfolio_url = candidate_data.portfolio_url
    if candidate_data.status is not None:
        candidate.status = candidate_data.status
    if candidate_data.notes is not None:
        candidate.notes = candidate_data.notes
    
    db.commit()
    db.refresh(candidate)
    
    logger.info("candidate_updated", candidate_id=candidate.id)
    
    return CandidateResponse(
        id=candidate.id,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        email=candidate.email,
        phone=candidate.phone,
        linkedin_url=candidate.linkedin_url,
        portfolio_url=candidate.portfolio_url,
        resume_id=candidate.resume_id,
        status=candidate.status,
        notes=candidate.notes,
        created_at=candidate.created_at,
    )


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise NotFoundError("Candidate", str(candidate_id))
    
    db.delete(candidate)
    db.commit()
    
    logger.info("candidate_deleted", candidate_id=candidate_id)

