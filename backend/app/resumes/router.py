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
    
    # Extract personal info from parsed_data and candidate model
    personal_info = {}
    
    # First, check if candidate exists (created from kundali)
    from app.models.candidate import Candidate
    candidate = db.query(Candidate).filter(Candidate.resume_id == resume_id).first()
    if candidate:
        personal_info = {
            "first_name": candidate.first_name or "",
            "last_name": candidate.last_name or "",
            "email": candidate.email or "",
            "phone": candidate.phone or "",
            "linkedin_url": candidate.linkedin_url or "",
            "portfolio_url": candidate.portfolio_url or "",
        }
    
    # Also check parsed_data (fallback or additional info)
    if latest_version and latest_version.parsed_data:
        # parsed_data is stored as JSON, might be dict or string
        parsed_data = latest_version.parsed_data
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except (json.JSONDecodeError, TypeError):
                parsed_data = {}
        if isinstance(parsed_data, dict):
            # Only fill in missing fields from parsed_data
            if not personal_info.get("first_name"):
                # Try to split name if first_name not available
                name = parsed_data.get("name") or parsed_data.get("first_name", "")
                if name and name != "unknown":
                    name_parts = name.split(" ", 1)
                    personal_info["first_name"] = name_parts[0] if name_parts else ""
                    personal_info["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
                else:
                    personal_info["first_name"] = parsed_data.get("first_name") or ""
                    personal_info["last_name"] = parsed_data.get("last_name") or ""
            
            # Fill in other missing fields
            if not personal_info.get("email"):
                personal_info["email"] = parsed_data.get("email") or ""
            if not personal_info.get("phone"):
                personal_info["phone"] = parsed_data.get("phone") or ""
            if not personal_info.get("linkedin_url"):
                # Check contact object too
                contact = parsed_data.get("contact", {})
                personal_info["linkedin_url"] = parsed_data.get("linkedin_url") or contact.get("linkedin") or ""
            if not personal_info.get("portfolio_url"):
                contact = parsed_data.get("contact", {})
                personal_info["portfolio_url"] = parsed_data.get("portfolio_url") or contact.get("portfolio") or ""
    
    # Normalize skills format (dict to list) if needed
    normalized_skills = None
    if latest_version and latest_version.skills:
        normalized_skills = ResumeVersionResponse.normalize_skills(latest_version.skills)
    
    # Normalize experience format for frontend compatibility
    normalized_experience = None
    if latest_version and latest_version.experience:
        import json
        experience_data = latest_version.experience
        if isinstance(experience_data, str):
            try:
                experience_data = json.loads(experience_data)
            except (json.JSONDecodeError, TypeError):
                experience_data = []
        
        if isinstance(experience_data, list):
            normalized_experience = []
            for exp in experience_data:
                # Transform Kundali format to frontend-expected format
                normalized_exp = {
                    "title": exp.get("role") or exp.get("title") or exp.get("position") or "N/A",
                    "position": exp.get("role") or exp.get("position") or "N/A",
                    "company": exp.get("company") or exp.get("organization") or "N/A",
                    "organization": exp.get("company") or exp.get("organization") or "N/A",
                    "start_date": exp.get("start_date") or "N/A",
                    "end_date": exp.get("end_date") or (exp.get("is_current") and "Present" or "N/A"),
                    "location": exp.get("location") or "",
                    "description": ""
                }
                
                # Convert responsibilities array to description string
                responsibilities = exp.get("responsibilities", [])
                if isinstance(responsibilities, list) and responsibilities:
                    normalized_exp["description"] = "\n".join([f"• {r}" for r in responsibilities if r])
                elif exp.get("description"):
                    normalized_exp["description"] = exp.get("description")
                
                # Add technologies if available
                technologies = exp.get("technologies_used", [])
                if technologies:
                    normalized_exp["technologies"] = technologies
                
                normalized_experience.append(normalized_exp)
    
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
            skills=normalized_skills,
            experience_years=latest_version.experience_years,
            education=latest_version.education,
            experience=normalized_experience or latest_version.experience,
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

