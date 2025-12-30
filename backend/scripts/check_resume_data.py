"""
Check resume data quality in database
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.resume import Resume, ResumeVersion
from app.models.candidate import Candidate

def check_resume_data():
    """Check resume data quality"""
    db: Session = SessionLocal()
    try:
        resumes = db.query(Resume).all()
        print(f"\n{'='*80}")
        print(f"RESUME DATA QUALITY CHECK")
        print(f"{'='*80}\n")
        print(f"Total Resumes: {len(resumes)}\n")
        
        for resume in resumes:
            print(f"\n{'─'*80}")
            print(f"Resume ID: {resume.id}")
            print(f"File: {resume.file_name}")
            print(f"Status: {resume.processing_status}")
            print(f"Size: {resume.file_size} bytes" if resume.file_size else "Size: N/A")
            
            # Get latest version
            latest_version = (
                db.query(ResumeVersion)
                .filter(ResumeVersion.resume_id == resume.id, ResumeVersion.is_current == True)
                .first()
            )
            
            if not latest_version:
                print("❌ NO PARSED VERSION FOUND")
                continue
            
            # Check candidate
            candidate = db.query(Candidate).filter(Candidate.resume_id == resume.id).first()
            candidate_name = f"{candidate.first_name} {candidate.last_name}" if candidate else "No candidate linked"
            
            print(f"Candidate: {candidate_name}")
            print(f"\nParsed Data Quality:")
            
            # Calculate quality score
            quality_score = 0
            max_score = 0
            
            # Skills
            skills_count = len(latest_version.skills) if latest_version.skills else 0
            max_score += 20
            if skills_count > 0:
                quality_score += min(20, skills_count * 2)
                print(f"  ✅ Skills: {skills_count} found")
            else:
                print(f"  ❌ Skills: NONE")
            
            # Experience
            max_score += 20
            if latest_version.experience_years is not None:
                quality_score += 20
                print(f"  ✅ Experience: {latest_version.experience_years} years")
            else:
                print(f"  ❌ Experience: NOT CALCULATED")
            
            # Experience details
            exp_count = len(latest_version.experience) if latest_version.experience else 0
            max_score += 15
            if exp_count > 0:
                quality_score += min(15, exp_count * 3)
                print(f"  ✅ Experience Details: {exp_count} entries")
            else:
                print(f"  ❌ Experience Details: NONE")
            
            # Education
            edu_count = len(latest_version.education) if latest_version.education else 0
            max_score += 15
            if edu_count > 0:
                quality_score += min(15, edu_count * 5)
                print(f"  ✅ Education: {edu_count} entries")
            else:
                print(f"  ❌ Education: NONE")
            
            # Projects
            proj_count = len(latest_version.projects) if latest_version.projects else 0
            max_score += 15
            if proj_count > 0:
                quality_score += min(15, proj_count * 3)
                print(f"  ✅ Projects: {proj_count} entries")
            else:
                print(f"  ❌ Projects: NONE")
            
            # Raw text
            max_score += 15
            if resume.raw_text and len(resume.raw_text) > 100:
                quality_score += 15
                print(f"  ✅ Raw Text: {len(resume.raw_text)} characters")
            else:
                print(f"  ❌ Raw Text: MISSING or TOO SHORT")
            
            # Calculate percentage
            quality_percentage = int((quality_score / max_score) * 100) if max_score > 0 else 0
            
            print(f"\n📊 Quality Score: {quality_score}/{max_score} ({quality_percentage}%)")
            
            if quality_percentage >= 80:
                print("✅ GOOD QUALITY")
            elif quality_percentage >= 50:
                print("⚠️  MODERATE QUALITY - Needs improvement")
            else:
                print("❌ POOR QUALITY - Reprocessing recommended")
            
            # Show sample data
            if latest_version.skills:
                print(f"\nSample Skills: {', '.join(latest_version.skills[:5])}")
            if latest_version.experience:
                exp = latest_version.experience[0]
                print(f"Sample Experience: {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
        
        print(f"\n{'='*80}\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_resume_data()

