"""
Migration script to add quality_score column to resume_versions table
Run this once to update existing database
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import SessionLocal

def add_quality_score_column():
    """Add quality_score column to resume_versions table"""
    db = SessionLocal()
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='resume_versions' AND column_name='quality_score'
        """))
        
        if result.fetchone():
            print("✅ quality_score column already exists")
            return
        
        # Add column
        db.execute(text("""
            ALTER TABLE resume_versions 
            ADD COLUMN quality_score INTEGER
        """))
        db.commit()
        print("✅ Successfully added quality_score column to resume_versions table")
        
        # Calculate quality scores for existing records
        print("\n📊 Calculating quality scores for existing resumes...")
        from app.models.resume import ResumeVersion, Resume
        from app.resumes.ai_parser import ai_parser
        
        versions = db.query(ResumeVersion).filter(ResumeVersion.is_current == True).all()
        updated = 0
        
        for version in versions:
            resume = db.query(Resume).filter(Resume.id == version.resume_id).first()
            if resume and resume.raw_text:
                parsed_data = {
                    "skills": version.skills or [],
                    "experience": version.experience or [],
                    "education": version.education or [],
                    "projects": version.projects or [],
                    "experience_years": version.experience_years,
                }
                quality_score = ai_parser._calculate_quality_score(parsed_data, resume.raw_text)
                version.quality_score = quality_score
                updated += 1
        
        db.commit()
        print(f"✅ Updated quality scores for {updated} resume versions")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_quality_score_column()

