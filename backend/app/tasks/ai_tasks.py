"""
AI-related async tasks
"""
from celery import Task
from app.core.celery_app import celery_app
import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=2)
def generate_embedding_task(self: Task, text: str, cache_key: str):
    """Generate embedding asynchronously"""
    from app.ai_engine.service import ai_engine
    from app.core.redis_client import set_cache
    
    try:
        embedding = ai_engine.generate_embedding(text)
        set_cache(cache_key, embedding, ttl=86400)  # 24 hours
        return cache_key
    except Exception as e:
        logger.error("embedding_generation_failed", error=str(e))
        raise self.retry(exc=e, countdown=60)

