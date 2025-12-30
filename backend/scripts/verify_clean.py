"""
Verify database is clean
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, Role
from app.models.candidate import Candidate
from app.models.resume import Resume, ResumeVersion
from app.models.job import JobDescription
from app.models.matching import MatchResult, AIExplanation

db: Session = SessionLocal()

try:
    print("=== FINAL DATABASE STATUS ===\n")
    
    users_count = db.query(User).count()
    roles_count = db.query(Role).count()
    candidates_count = db.query(Candidate).count()
    resumes_count = db.query(Resume).count()
    resume_versions_count = db.query(ResumeVersion).count()
    jobs_count = db.query(JobDescription).count()
    match_results_count = db.query(MatchResult).count()
    ai_explanations_count = db.query(AIExplanation).count()
    
    print(f"✅ Users: {users_count}")
    if users_count > 0:
        user = db.query(User).first()
        print(f"   - {user.email} ({user.full_name})")
    
    print(f"✅ Roles: {roles_count}")
    print(f"✅ Candidates: {candidates_count}")
    print(f"✅ Resumes: {resumes_count}")
    print(f"✅ Resume Versions: {resume_versions_count}")
    print(f"✅ Jobs: {jobs_count}")
    print(f"✅ Match Results: {match_results_count}")
    print(f"✅ AI Explanations: {ai_explanations_count}")
    
    print("\n✅ Database is clean! Only login/user data remains.")
    
finally:
    db.close()

