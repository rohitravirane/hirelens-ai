"""
Reprocess all existing resumes with enhanced AI parser
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

def reprocess_all_resumes():
    """Reprocess all resumes with enhanced AI parser"""
    db: Session = SessionLocal()
    try:
        # Get all completed resumes
        resumes = db.query(Resume).filter(Resume.processing_status == "completed").all()
        
        if not resumes:
            print("No completed resumes found to reprocess.")
            return
        
        print(f"\n{'='*80}")
        print(f"REPROCESSING RESUMES WITH ENHANCED AI PARSER")
        print(f"{'='*80}\n")
        print(f"Found {len(resumes)} resume(s) to reprocess:\n")
        
        for resume in resumes:
            print(f"  - Resume ID: {resume.id}")
            print(f"    File: {resume.file_name}")
            print(f"    Status: {resume.processing_status}")
        
        print(f"\n{'─'*80}")
        response = input(f"\nReprocess all {len(resumes)} resume(s)? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("Cancelled.")
            return
        
        print(f"\n🔄 Reprocessing resumes...\n")
        
        reprocessed = 0
        for resume in resumes:
            try:
                # Set status to pending
                resume.processing_status = "pending"
                db.commit()
                
                # Trigger async processing
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
        print("Processing will happen asynchronously. Check status after a few minutes.")
        print("You can check quality scores using: python scripts/check_resume_data.py\n")
        
    except Exception as e:
        logger.error("reprocess_all_failed", error=str(e))
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    reprocess_all_resumes()

