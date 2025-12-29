"""
Job description routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.dependencies import get_current_active_user, require_role
from app.models.user import User
from app.models.job import JobDescription
from app.jobs.parser import JobDescriptionParser
from app.jobs.schemas import (
    JobDescriptionCreate,
    JobDescriptionUpdate,
    JobDescriptionResponse,
    JobDescriptionDetailResponse,
)
from app.tasks.job_tasks import process_job_description_task

router = APIRouter(prefix="/api/v1/jobs", tags=["Job Descriptions"])
logger = structlog.get_logger()

parser = JobDescriptionParser()


@router.post("/", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_job_description(
    job_data: JobDescriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new job description"""
    # Parse the job description
    parsed_data = parser.parse(job_data.raw_text)
    
    # Create job description
    job = JobDescription(
        title=job_data.title,
        company=job_data.company,
        department=job_data.department,
        raw_text=job_data.raw_text,
        location=job_data.location,
        remote_allowed=job_data.remote_allowed,
        employment_type=job_data.employment_type,
        parsed_data=parsed_data,
        required_skills=parsed_data.get("required_skills"),
        nice_to_have_skills=parsed_data.get("nice_to_have_skills"),
        experience_years_required=parsed_data.get("experience_years_required"),
        seniority_level=parsed_data.get("seniority_level"),
        education_requirements=parsed_data.get("education_requirements"),
        created_by=current_user.id,
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Trigger async processing for embeddings
    process_job_description_task.delay(job.id)
    
    logger.info("job_description_created", job_id=job.id, title=job.title)
    
    return JobDescriptionResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        department=job.department,
        required_skills=job.required_skills,
        nice_to_have_skills=job.nice_to_have_skills,
        experience_years_required=job.experience_years_required,
        seniority_level=job.seniority_level,
        location=job.location,
        remote_allowed=job.remote_allowed,
        employment_type=job.employment_type,
        is_active=job.is_active,
        created_at=job.created_at,
    )


@router.get("/", response_model=List[JobDescriptionResponse])
def list_job_descriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List job descriptions"""
    query = db.query(JobDescription).filter(JobDescription.is_archived == False)
    
    if is_active is not None:
        query = query.filter(JobDescription.is_active == is_active)
    
    jobs = query.order_by(JobDescription.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        JobDescriptionResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            department=job.department,
            required_skills=job.required_skills,
            nice_to_have_skills=job.nice_to_have_skills,
            experience_years_required=job.experience_years_required,
            seniority_level=job.seniority_level,
            location=job.location,
            remote_allowed=job.remote_allowed,
            employment_type=job.employment_type,
            is_active=job.is_active,
            created_at=job.created_at,
        )
        for job in jobs
    ]


@router.get("/{job_id}", response_model=JobDescriptionDetailResponse)
def get_job_description(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get job description details"""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise NotFoundError("Job description", str(job_id))
    
    return JobDescriptionDetailResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        department=job.department,
        raw_text=job.raw_text,
        required_skills=job.required_skills,
        nice_to_have_skills=job.nice_to_have_skills,
        experience_years_required=job.experience_years_required,
        seniority_level=job.seniority_level,
        education_requirements=job.education_requirements,
        location=job.location,
        remote_allowed=job.remote_allowed,
        employment_type=job.employment_type,
        is_active=job.is_active,
        parsed_data=job.parsed_data,
        created_at=job.created_at,
    )


@router.put("/{job_id}", response_model=JobDescriptionResponse)
def update_job_description(
    job_id: int,
    job_data: JobDescriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update job description"""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise NotFoundError("Job description", str(job_id))
    
    # Check permissions (only creator or admin can update)
    if job.created_by != current_user.id:
        from app.auth.dependencies import require_role
        _ = require_role("admin")(current_user)
    
    # Update fields
    if job_data.title is not None:
        job.title = job_data.title
    if job_data.company is not None:
        job.company = job_data.company
    if job_data.department is not None:
        job.department = job_data.department
    if job_data.raw_text is not None:
        job.raw_text = job_data.raw_text
        # Re-parse if text changed
        parsed_data = parser.parse(job_data.raw_text)
        job.parsed_data = parsed_data
        job.required_skills = parsed_data.get("required_skills")
        job.nice_to_have_skills = parsed_data.get("nice_to_have_skills")
        job.experience_years_required = parsed_data.get("experience_years_required")
        job.seniority_level = parsed_data.get("seniority_level")
        # Trigger async processing
        process_job_description_task.delay(job.id)
    if job_data.is_active is not None:
        job.is_active = job_data.is_active
    if job_data.is_archived is not None:
        job.is_archived = job_data.is_archived
    
    db.commit()
    db.refresh(job)
    
    logger.info("job_description_updated", job_id=job.id)
    
    return JobDescriptionResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        department=job.department,
        required_skills=job.required_skills,
        nice_to_have_skills=job.nice_to_have_skills,
        experience_years_required=job.experience_years_required,
        seniority_level=job.seniority_level,
        location=job.location,
        remote_allowed=job.remote_allowed,
        employment_type=job.employment_type,
        is_active=job.is_active,
        created_at=job.created_at,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_description(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete (archive) job description"""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise NotFoundError("Job description", str(job_id))
    
    # Check permissions
    if job.created_by != current_user.id:
        _ = require_role("admin")(current_user)
    
    job.is_archived = True
    job.is_active = False
    db.commit()
    
    logger.info("job_description_archived", job_id=job.id)

