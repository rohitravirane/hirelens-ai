#!/usr/bin/env python3
"""
Reprocess all existing resumes with vision-first architecture
Run: docker-compose exec backend python backend/scripts/reprocess_all_resumes.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.redis_client import redis_client
from app.models.resume import Resume
from app.tasks.resume_tasks import process_resume_task
import structlog

logger = structlog.get_logger()

def clear_resume_cache():
    """Clear all resume parsing cache"""
    try:
        print("\n" + "="*80)
        print("CLEARING RESUME CACHE")
        print("="*80 + "\n")
        
        # Get all cache keys
        pattern = "cache:ai_parse:*"
        keys = []
        for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info("cache_cleared", keys_deleted=deleted, total_keys=len(keys))
            print(f"✅ Cleared {deleted} cache keys")
        else:
            logger.info("no_cache_keys_found")
            print("ℹ️  No cache keys found")
        
        print("\n" + "-"*80 + "\n")
        return True
    except Exception as e:
        logger.error("cache_clear_failed", error=str(e))
        print(f"❌ Error clearing cache: {e}")
        return False

def reprocess_all_resumes():
    """Reprocess all resumes with vision-first architecture"""
    db: Session = SessionLocal()
    try:
        # Step 1: Clear cache first
        print("\n" + "="*80)
        print("VISION-FIRST ARCHITECTURE REPROCESSING")
        print("="*80)
        print("\nStep 1: Clearing cache...")
        clear_resume_cache()
        
        # Step 2: Get all completed resumes
        print("Step 2: Finding resumes to reprocess...\n")
        resumes = db.query(Resume).filter(Resume.processing_status == "completed").all()
        
        if not resumes:
            print("No completed resumes found to reprocess.")
            return
        
        print(f"Found {len(resumes)} resume(s) to reprocess:\n")
        
        for resume in resumes:
            print(f"  - Resume ID: {resume.id}")
            print(f"    File: {resume.file_name}")
            print(f"    Status: {resume.processing_status}")
        
        print(f"\n{'─'*80}")
        print(f"\n🔄 Automatically reprocessing {len(resumes)} resume(s) with vision-first pipeline...\n")
        
        reprocessed = 0
        for resume in resumes:
            try:
                # Set status to pending
                resume.processing_status = "pending"
                db.commit()
                
                # Trigger async processing (will use vision-first pipeline with LayoutLMv3-large)
                process_resume_task.delay(resume.id)
                
                print(f"✅ Queued Resume ID {resume.id} ({resume.file_name}) for reprocessing")
                reprocessed += 1
                
            except Exception as e:
                logger.error("reprocess_failed", resume_id=resume.id, error=str(e))
                print(f"❌ Failed to queue Resume ID {resume.id}: {e}")
                db.rollback()
        
        print(f"\n{'='*80}")
        print(f"✅ Successfully queued {reprocessed} resume(s) for reprocessing")
        print(f"{'='*80}\n")
        print("📋 Processing Details:")
        print("  - Vision-first pipeline: LayoutLMv3-large (GPU-accelerated if available)")
        print("  - Processing happens asynchronously via Celery workers")
        print("  - Check status after a few minutes")
        print("  - Quality scores will reflect layout confidence (+15 bonus for LayoutLM success)")
        print("\n💡 Monitor progress:")
        print("  - Backend logs: docker-compose logs -f backend")
        print("  - Celery logs: docker-compose logs -f celery-worker")
        print("  - Check data: python scripts/check_resume_data.py\n")
        
    except Exception as e:
        logger.error("reprocess_all_failed", error=str(e))
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    reprocess_all_resumes()

