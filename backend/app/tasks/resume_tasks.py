"""
Resume processing tasks
"""
from celery import Task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.resume import Resume, ResumeVersion
from app.resumes.parser import ResumeParser
from app.resumes.ai_parser import ai_parser
import structlog

logger = structlog.get_logger()
parser = ResumeParser()


@celery_app.task(bind=True, max_retries=3)
def process_resume_task(self: Task, resume_id: int):
    """Process a resume asynchronously"""
    db: Session = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            logger.error("resume_not_found", resume_id=resume_id)
            return
        
        # Update status
        resume.processing_status = "processing"
        db.commit()
        
        # Extract text
        try:
            raw_text = parser.extract_text(resume.file_path)
            resume.raw_text = raw_text
        except Exception as e:
            logger.error("text_extraction_failed", resume_id=resume_id, error=str(e))
            resume.processing_status = "failed"
            resume.processing_error = str(e)
            db.commit()
            return
        
        # Parse resume using AI (intelligent extraction - heart of the system)
        try:
            # Try AI parsing first (intelligent extraction)
            logger.info("starting_ai_resume_parsing", resume_id=resume_id)
            parsed_data = ai_parser.parse_with_ai(raw_text)
            logger.info("ai_resume_parsing_complete", resume_id=resume_id)
        except Exception as e:
            logger.warning("ai_parsing_failed_fallback", resume_id=resume_id, error=str(e))
            # Fallback to rule-based parsing
            try:
                parsed_data = parser.parse(raw_text)
                logger.info("fallback_parsing_success", resume_id=resume_id)
            except Exception as e2:
                logger.error("resume_parsing_failed", resume_id=resume_id, error=str(e2))
                resume.processing_status = "failed"
                resume.processing_error = str(e2)
                db.commit()
                return
        
        # Mark old versions as not current
        db.query(ResumeVersion).filter(
            ResumeVersion.resume_id == resume_id,
            ResumeVersion.is_current == True,
        ).update({"is_current": False})
        
        # Create new version
        latest_version = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .first()
        )
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Calculate quality score if not already calculated
        quality_score = parsed_data.get("quality_score")
        if quality_score is None:
            # Calculate quality score
            from app.resumes.ai_parser import ai_parser
            quality_score = ai_parser._calculate_quality_score(parsed_data, raw_text)
        
        resume_version = ResumeVersion(
            resume_id=resume_id,
            version_number=version_number,
            parsed_data=parsed_data,
            skills=parsed_data.get("skills"),
            experience_years=parsed_data.get("experience_years"),
            education=parsed_data.get("education"),
            experience=parsed_data.get("experience"),
            projects=parsed_data.get("projects"),
            certifications=parsed_data.get("certifications"),
            languages=parsed_data.get("languages"),
            is_current=True,
            parser_version="3.0-ai-enhanced",  # Updated version for enhanced AI parsing
            quality_score=quality_score,
        )
        db.add(resume_version)
        
        # Update resume status
        resume.processing_status = "completed"
        db.commit()
        
        logger.info("resume_processed", resume_id=resume_id, version=version_number)
        
    except Exception as e:
        logger.exception("resume_processing_error", resume_id=resume_id, error=str(e))
        db.rollback()
        
        # Update resume status
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.processing_status = "failed"
            resume.processing_error = str(e)
            db.commit()
        
        # Retry
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()

