"""
Reprocess a single resume by ID
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.resume import Resume
from app.tasks.resume_tasks import process_resume_task
import structlog

logger = structlog.get_logger()

def reprocess_resume(resume_id: int):
    """Reprocess a single resume"""
    db: Session = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if not resume:
            print(f"❌ Resume ID {resume_id} not found.")
            return
        
        print(f"\n{'='*80}")
        print(f"REPROCESSING RESUME")
        print(f"{'='*80}\n")
        print(f"Resume ID: {resume.id}")
        print(f"File: {resume.file_name}")
        print(f"Current Status: {resume.processing_status}")
        print(f"{'─'*80}\n")
        
        # Set status to pending
        resume.processing_status = "pending"
        db.commit()
        
        # Trigger async processing
        process_resume_task.delay(resume.id)
        
        print(f"✅ Resume ID {resume.id} queued for reprocessing")
        print(f"\nProcessing will happen asynchronously.")
        print(f"Check status after a few minutes using: python scripts/check_resume_data.py\n")
        
    except Exception as e:
        logger.error("reprocess_failed", resume_id=resume_id, error=str(e))
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/reprocess_single_resume.py <resume_id>")
        print("Example: python scripts/reprocess_single_resume.py 33")
        sys.exit(1)
    
    try:
        resume_id = int(sys.argv[1])
        reprocess_resume(resume_id)
    except ValueError:
        print("❌ Invalid resume ID. Please provide a number.")
        sys.exit(1)

