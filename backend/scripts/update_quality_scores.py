"""
Update quality scores for existing resume versions
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.resume import Resume, ResumeVersion
from app.resumes.ai_parser import ai_parser

def update_quality_scores():
    """Update quality scores for all existing resume versions"""
    db: Session = SessionLocal()
    try:
        versions = db.query(ResumeVersion).filter(ResumeVersion.is_current == True).all()
        
        if not versions:
            print("No resume versions found.")
            return
        
        print(f"\n{'='*80}")
        print(f"UPDATING QUALITY SCORES")
        print(f"{'='*80}\n")
        print(f"Found {len(versions)} resume version(s) to update:\n")
        
        updated = 0
        for version in versions:
            resume = db.query(Resume).filter(Resume.id == version.resume_id).first()
            if not resume or not resume.raw_text:
                print(f"⚠️  Skipping Resume ID {version.resume_id} - No raw text available")
                continue
            
            # Calculate quality score
            parsed_data = {
                "skills": version.skills or [],
                "experience": version.experience or [],
                "education": version.education or [],
                "projects": version.projects or [],
                "experience_years": version.experience_years,
            }
            
            quality_score = ai_parser._calculate_quality_score(parsed_data, resume.raw_text)
            version.quality_score = quality_score
            
            print(f"✅ Resume ID {version.resume_id}: Quality Score = {quality_score}%")
            updated += 1
        
        db.commit()
        print(f"\n{'='*80}")
        print(f"✅ Successfully updated quality scores for {updated} resume version(s)")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_quality_scores()

