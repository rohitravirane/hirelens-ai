"""
Resume processing routes
"""
import os
import uuid
import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import ProcessingError, NotFoundError
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.resume import Resume, ResumeVersion
from app.resumes.parser import ResumeParser
from app.resumes.schemas import ResumeResponse, ResumeDetailResponse, ResumeVersionResponse
from app.tasks.resume_tasks import process_resume_task

router = APIRouter(prefix="/api/v1/resumes", tags=["Resumes"])
logger = structlog.get_logger()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload and process a resume"""
    # Validate file type
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    if file_ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise ProcessingError(
            f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
        )
    
    # Validate file size
    file_content = file.file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise ProcessingError(
            f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_name = f"{file_id}.{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, file_name)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create resume record
    resume = Resume(
        file_name=file.filename,
        file_path=file_path,
        file_size=len(file_content),
        file_type=file_ext,
        processing_status="pending",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    # Trigger async processing
    process_resume_task.delay(resume.id)
    
    logger.info("resume_uploaded", resume_id=resume.id, file_name=file.filename)
    
    return ResumeResponse(
        id=resume.id,
        file_name=resume.file_name,
        file_size=resume.file_size,
        file_type=resume.file_type,
        processing_status=resume.processing_status,
        created_at=resume.created_at,
    )


@router.get("/", response_model=List[ResumeResponse])
def list_resumes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all resumes"""
    resumes = db.query(Resume).offset(skip).limit(limit).all()
    return [
        ResumeResponse(
            id=r.id,
            file_name=r.file_name,
            file_size=r.file_size,
            file_type=r.file_type,
            processing_status=r.processing_status,
            created_at=r.created_at,
        )
        for r in resumes
    ]


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get resume details"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise NotFoundError("Resume", str(resume_id))
    
    # Get latest version
    latest_version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume_id, ResumeVersion.is_current == True)
        .first()
    )
    
    # Extract personal info from parsed_data if available
    personal_info = {}
    if latest_version and latest_version.parsed_data:
        # parsed_data is stored as JSON, might be dict or string
        parsed_data = latest_version.parsed_data
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except (json.JSONDecodeError, TypeError):
                parsed_data = {}
        if isinstance(parsed_data, dict):
            personal_info = {
                "first_name": parsed_data.get("first_name") or "",
                "last_name": parsed_data.get("last_name") or "",
                "email": parsed_data.get("email") or "",
                "phone": parsed_data.get("phone") or "",
                "linkedin_url": parsed_data.get("linkedin_url") or "",
                "portfolio_url": parsed_data.get("portfolio_url") or "",
            }
    
    return ResumeDetailResponse(
        id=resume.id,
        file_name=resume.file_name,
        file_size=resume.file_size,
        file_type=resume.file_type,
        processing_status=resume.processing_status,
        raw_text=resume.raw_text,
        created_at=resume.created_at,
        latest_version=ResumeVersionResponse(
            id=latest_version.id,
            resume_id=latest_version.resume_id,
            version_number=latest_version.version_number,
            skills=latest_version.skills,
            experience_years=latest_version.experience_years,
            education=latest_version.education,
            experience=latest_version.experience,
            projects=latest_version.projects,
            parsed_at=latest_version.parsed_at,
            quality_score=latest_version.quality_score,
            **personal_info,
        ) if latest_version else None,
    )


@router.post("/{resume_id}/reprocess", response_model=ResumeResponse)
def reprocess_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reprocess a resume"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise NotFoundError("Resume", str(resume_id))
    
    resume.processing_status = "pending"
    db.commit()
    
    # Trigger async processing
    process_resume_task.delay(resume.id)
    
    logger.info("resume_reprocessing", resume_id=resume.id)
    
    return ResumeResponse(
        id=resume.id,
        file_name=resume.file_name,
        file_size=resume.file_size,
        file_type=resume.file_type,
        processing_status=resume.processing_status,
        created_at=resume.created_at,
    )

