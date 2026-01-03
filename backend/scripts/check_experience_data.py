"""
Check experience data for a specific resume
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.resume import ResumeVersion

def check_experience_data(resume_id: int = 42):
    """Check experience data for a resume"""
    db: Session = SessionLocal()
    try:
        version = db.query(ResumeVersion).filter(
            ResumeVersion.resume_id == resume_id,
            ResumeVersion.is_current == True
        ).first()
        
        if not version:
            print(f"❌ No current version found for Resume ID {resume_id}")
            return
        
        if not version.parsed_data:
            print(f"❌ No parsed data found for Resume ID {resume_id}")
            return
        
        data = version.parsed_data if isinstance(version.parsed_data, dict) else json.loads(version.parsed_data)
        
        print(f"\n{'='*80}")
        print(f"RESUME ID: {resume_id} - VERSION {version.version_number}")
        print(f"{'='*80}\n")
        print(f"Quality Score: {version.quality_score}%")
        print(f"Parsed At: {version.parsed_at}")
        
        # Metadata
        metadata = data.get('_metadata', {})
        print(f"\n📊 METADATA:")
        print(f"   - Parser Version: {metadata.get('parser_version', 'N/A')}")
        print(f"   - Used LayoutLMv3: {metadata.get('used_layoutlm', False)}")
        print(f"   - Used Text Detection: {metadata.get('used_text_based_detection', False)}")
        print(f"   - Used OCR: {metadata.get('used_ocr', False)}")
        
        # Experience entries
        experience = data.get('experience', [])
        print(f"\n💼 EXPERIENCE ENTRIES ({len(experience)}):")
        print(f"{'='*80}")
        
        for i, exp in enumerate(experience, 1):
            title = exp.get('title', 'N/A')
            company = exp.get('company', 'N/A')
            start_date = exp.get('start_date', 'N/A')
            end_date = exp.get('end_date', 'N/A')
            description = exp.get('description', '')
            
            print(f"\n{i}. {title}")
            print(f"   Company: {company}")
            print(f"   Dates: {start_date} - {end_date}")
            if description:
                desc_preview = description[:150] + '...' if len(description) > 150 else description
                print(f"   Description: {desc_preview}")
            else:
                print("   Description: None")
        
        # Skills
        skills = data.get('skills', {})
        if isinstance(skills, dict):
            technical = skills.get('technical', [])
            print(f"\n🛠️  SKILLS:")
            print(f"   Technical: {len(technical)} items")
            if technical:
                print(f"   First 5: {technical[:5]}")
        
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    resume_id = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    check_experience_data(resume_id)

