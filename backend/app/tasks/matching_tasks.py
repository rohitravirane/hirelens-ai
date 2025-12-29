"""
Matching and scoring tasks
"""
from celery import Task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.matching.service import matching_service
import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=2)
def calculate_match_task(self: Task, candidate_id: int, job_id: int):
    """Calculate match asynchronously"""
    db: Session = SessionLocal()
    try:
        match_result = matching_service.match_candidate_to_job(
            db, candidate_id, job_id, force_recalculate=True
        )
        logger.info(
            "match_calculated_async",
            candidate_id=candidate_id,
            job_id=job_id,
            match_id=match_result.id,
        )
        return match_result.id
    except Exception as e:
        logger.exception(
            "match_calculation_failed",
            candidate_id=candidate_id,
            job_id=job_id,
            error=str(e),
        )
        raise self.retry(exc=e, countdown=120)
    finally:
        db.close()


@celery_app.task(bind=True)
def bulk_match_candidates_task(self: Task, job_id: int, candidate_ids: list[int]):
    """Bulk match candidates to a job"""
    db: Session = SessionLocal()
    results = []
    try:
        for candidate_id in candidate_ids:
            try:
                match_result = matching_service.match_candidate_to_job(
                    db, candidate_id, job_id, force_recalculate=False
                )
                results.append({
                    "candidate_id": candidate_id,
                    "match_id": match_result.id,
                    "score": match_result.overall_score,
                })
            except Exception as e:
                logger.error(
                    "bulk_match_failed",
                    candidate_id=candidate_id,
                    job_id=job_id,
                    error=str(e),
                )
                results.append({
                    "candidate_id": candidate_id,
                    "error": str(e),
                })
        
        logger.info("bulk_match_completed", job_id=job_id, count=len(results))
        return results
    finally:
        db.close()

