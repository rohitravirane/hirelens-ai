"""
Job description processing tasks
"""
from celery import Task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.job import JobDescription
from app.ai_engine.service import ai_engine
from datetime import datetime
import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def process_job_description_task(self: Task, job_id: int):
    """Process job description and generate embeddings"""
    db: Session = SessionLocal()
    try:
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        if not job:
            logger.error("job_not_found", job_id=job_id)
            return
        
        # Generate embedding
        try:
            text_for_embedding = f"{job.title} {job.raw_text or ''}"
            embedding = ai_engine.generate_embedding(text_for_embedding[:2000])  # Limit length
            job.embedding = embedding
            job.processed_at = datetime.utcnow()
            db.commit()
            
            logger.info("job_processed", job_id=job_id)
        except Exception as e:
            logger.error("job_processing_failed", job_id=job_id, error=str(e))
            # Don't fail the job, just log the error
            db.rollback()
        
    except Exception as e:
        logger.exception("job_processing_error", job_id=job_id, error=str(e))
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()

