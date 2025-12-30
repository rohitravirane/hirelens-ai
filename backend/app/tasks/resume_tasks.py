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
                # Calculate quality score for fallback parsing
                if "quality_score" not in parsed_data or parsed_data.get("quality_score") is None:
                    from app.resumes.ai_parser import ai_parser as ai_parser_instance
                    quality_score = ai_parser_instance._calculate_quality_score(parsed_data, raw_text)
                    parsed_data["quality_score"] = quality_score
                    logger.info("fallback_quality_score_calculated", resume_id=resume_id, score=quality_score)
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
        
        # Get quality score from parsed data (should be calculated by parser)
        quality_score = parsed_data.get("quality_score")
        logger.info("quality_score_from_parsed_data", resume_id=resume_id, quality_score=quality_score)
        if quality_score is None:
            # Fallback: Calculate quality score if parser didn't provide it
            logger.warning("quality_score_missing_from_parser", resume_id=resume_id)
            from app.resumes.ai_parser import ai_parser
            quality_score = ai_parser._calculate_quality_score(parsed_data, raw_text)
            logger.info("quality_score_calculated_in_task", resume_id=resume_id, score=quality_score)
        
        logger.info("final_quality_score", resume_id=resume_id, quality_score=quality_score, version=version_number)
        
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

