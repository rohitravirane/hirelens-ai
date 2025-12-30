"""
Check Rohit Rane's data in the system
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.candidate import Candidate
from app.models.resume import Resume, ResumeVersion
from app.models.job import JobDescription
from app.models.matching import MatchResult

db: Session = SessionLocal()

try:
    # Find Rohit Rane user
    user = db.query(User).filter(User.email == "rohitravikantrane@gmail.com").first()
    
    if user:
        print(f"✅ User Found:")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.full_name}")
        print(f"   User ID: {user.id}")
        print(f"   Active: {user.is_active}")
        print()
        
        # Check candidates created by this user
        candidates = db.query(Candidate).filter(Candidate.created_by == user.id).all()
        print(f"📋 Candidates created by Rohit: {len(candidates)}")
        for c in candidates[:10]:
            print(f"   - {c.first_name} {c.last_name} ({c.email}) - Status: {c.status}")
        print()
        
        # Check all resumes
        resumes = db.query(Resume).all()
        print(f"📄 Total Resumes: {len(resumes)}")
        
        # Check resume versions with experience
        resume_versions = db.query(ResumeVersion).filter(ResumeVersion.experience_years != None).all()
        print(f"📊 Resume Versions with Experience Years: {len(resume_versions)}")
        for rv in resume_versions[:10]:
            resume = db.query(Resume).filter(Resume.id == rv.resume_id).first()
            print(f"   Resume ID {rv.resume_id} ({resume.file_name if resume else 'N/A'}): {rv.experience_years} years")
            if rv.experience:
                print(f"      Experience entries: {len(rv.experience)}")
                for exp in rv.experience[:2]:
                    print(f"        - {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
        print()
        
        # Check jobs
        jobs = db.query(JobDescription).filter(JobDescription.created_by == user.id).all()
        print(f"💼 Jobs created by Rohit: {len(jobs)}")
        for job in jobs[:5]:
            print(f"   - {job.title} at {job.company} (ID: {job.id})")
        print()
        
        # Check match results
        match_results = db.query(MatchResult).all()
        print(f"🎯 Total Match Results: {len(match_results)}")
        if match_results:
            avg_score = sum(mr.overall_score for mr in match_results) / len(match_results)
            print(f"   Average Score: {avg_score:.2f}%")
        print()
        
        # Detailed check of one resume
        print("📝 Sample Resume Data (First Resume with Experience):")
        rv = db.query(ResumeVersion).filter(ResumeVersion.experience_years != None).first()
        if rv:
            resume = db.query(Resume).filter(Resume.id == rv.resume_id).first()
            print(f"   Resume ID: {rv.resume_id}")
            print(f"   File: {resume.file_name if resume else 'N/A'}")
            print(f"   Experience Years: {rv.experience_years}")
            print(f"   Parser Version: {rv.parser_version}")
            print(f"   Skills Count: {len(rv.skills) if rv.skills else 0}")
            print(f"   Experience Entries: {len(rv.experience) if rv.experience else 0}")
            if rv.experience:
                print("   Experience Details:")
                for i, exp in enumerate(rv.experience[:3], 1):
                    print(f"     {i}. {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
                    print(f"        Date: {exp.get('date_range', 'N/A')}")
            if rv.skills:
                print(f"   Sample Skills: {', '.join(rv.skills[:10])}")
    else:
        print("❌ User not found!")
        
finally:
    db.close()

