"""
Clean candidates and resume data, preserve jobs and users
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.candidate import Candidate
from app.models.candidate_kundali import CandidateKundali
from app.models.resume import Resume, ResumeVersion
from app.models.job import JobDescription
from app.models.matching import MatchResult, AIExplanation
import structlog

logger = structlog.get_logger()


def clean_database():
    """Clean candidates and resume data, preserve jobs and users"""
    db: Session = SessionLocal()
    try:
        logger.info("starting_database_cleanup")
        
        # Delete AI Explanations (related to matches)
        ai_explanations_count = db.query(AIExplanation).count()
        db.query(AIExplanation).delete()
        logger.info("deleted_ai_explanations", count=ai_explanations_count)
        
        # Delete Match Results
        match_results_count = db.query(MatchResult).count()
        db.query(MatchResult).delete()
        logger.info("deleted_match_results", count=match_results_count)
        
        # Delete Resume Versions
        resume_versions_count = db.query(ResumeVersion).count()
        db.query(ResumeVersion).delete()
        logger.info("deleted_resume_versions", count=resume_versions_count)
        
        # Delete Candidate Kundalis (must be deleted before Candidates due to FK constraint)
        candidate_kundalis_count = db.query(CandidateKundali).count()
        db.query(CandidateKundali).delete()
        logger.info("deleted_candidate_kundalis", count=candidate_kundalis_count)
        
        # Delete Candidates
        candidates_count = db.query(Candidate).count()
        db.query(Candidate).delete()
        logger.info("deleted_candidates", count=candidates_count)
        
        # Delete Resumes
        resumes_count = db.query(Resume).count()
        db.query(Resume).delete()
        logger.info("deleted_resumes", count=resumes_count)
        
        # Jobs are PRESERVED - not deleted
        jobs_count = db.query(JobDescription).count()
        logger.info("preserved_jobs", count=jobs_count)
        
        db.commit()
        logger.info("database_cleanup_complete")
        print("\n✅ Database cleaned successfully!")
        print(f"   - Deleted {ai_explanations_count} AI Explanations")
        print(f"   - Deleted {match_results_count} Match Results")
        print(f"   - Deleted {resume_versions_count} Resume Versions")
        print(f"   - Deleted {candidate_kundalis_count} Candidate Kundalis")
        print(f"   - Deleted {candidates_count} Candidates")
        print(f"   - Deleted {resumes_count} Resumes")
        print(f"\n✅ Preserved:")
        print(f"   - {jobs_count} Jobs")
        print(f"   - All Users and Roles")
        
    except Exception as e:
        logger.error("database_cleanup_failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clean_database()

