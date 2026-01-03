"""
Check extracted data from resumes in database
Shows detailed parsed_data content
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.resume import Resume, ResumeVersion

def check_extracted_data():
    """Check extracted data from resumes"""
    db: Session = SessionLocal()
    try:
        resumes = db.query(Resume).order_by(Resume.id.desc()).limit(5).all()
        print(f"\n{'='*80}")
        print(f"EXTRACTED DATA CHECK (Latest 5 Resumes)")
        print(f"{'='*80}\n")
        
        if not resumes:
            print("No resumes found in database.")
            return
        
        for resume in resumes:
            print(f"\n{'─'*80}")
            print(f"Resume ID: {resume.id}")
            print(f"File: {resume.file_name}")
            print(f"Status: {resume.processing_status}")
            
            # Get latest version
            latest_version = (
                db.query(ResumeVersion)
                .filter(ResumeVersion.resume_id == resume.id, ResumeVersion.is_current == True)
                .first()
            )
            
            if not latest_version:
                print("❌ NO PARSED VERSION FOUND")
                continue
            
            print(f"Version: {latest_version.version_number}")
            print(f"Quality Score: {latest_version.quality_score}%")
            print(f"Parsed At: {latest_version.parsed_at}")
            
            # Check metadata first
            if latest_version.parsed_data:
                parsed_data = latest_version.parsed_data
                if isinstance(parsed_data, str):
                    try:
                        parsed_data = json.loads(parsed_data)
                    except:
                        parsed_data = {}
                
                if isinstance(parsed_data, dict) and "_metadata" in parsed_data:
                    metadata = parsed_data["_metadata"]
                    print(f"\n🔍 METADATA (Processing Info):")
                    print(f"   - Parser Version: {metadata.get('parser_version', 'N/A')}")
                    print(f"   - Used LayoutLMv3: {metadata.get('used_layoutlm', False)} ⭐")
                    print(f"   - Used Text Detection: {metadata.get('used_text_based_detection', False)}")
                    print(f"   - Used OCR: {metadata.get('used_ocr', False)}")
                    print(f"   - Used Semantic Normalizer: {metadata.get('used_semantic_normalizer', False)}")
                    print(f"   - Pages Processed: {metadata.get('pages_processed', 0)}")
                    print(f"   - Sections Detected: {metadata.get('sections_detected', [])}")
            
            # Check parsed_data
            print(f"\n📄 PARSED_DATA (Full JSON):")
            if latest_version.parsed_data:
                parsed_data = latest_version.parsed_data
                if isinstance(parsed_data, str):
                    try:
                        parsed_data = json.loads(parsed_data)
                    except:
                        parsed_data = {}
                
                print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
            else:
                print("❌ parsed_data is NULL/EMPTY")
            
            # Check individual fields
            print(f"\n📊 EXTRACTED FIELDS:")
            
            # Skills
            print(f"\n  Skills:")
            if latest_version.skills:
                if isinstance(latest_version.skills, dict):
                    print(f"    Format: DICT")
                    for key, value in latest_version.skills.items():
                        if value:
                            print(f"    {key}: {value}")
                elif isinstance(latest_version.skills, list):
                    print(f"    Format: LIST")
                    print(f"    Count: {len(latest_version.skills)}")
                    print(f"    Skills: {latest_version.skills[:10]}")
                else:
                    print(f"    Format: {type(latest_version.skills)}")
                    print(f"    Value: {latest_version.skills}")
            else:
                print("    ❌ NONE")
            
            # Experience
            print(f"\n  Experience:")
            if latest_version.experience:
                print(f"    Count: {len(latest_version.experience)}")
                for i, exp in enumerate(latest_version.experience[:3], 1):
                    print(f"    {i}. {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
                    print(f"       Dates: {exp.get('start_date', 'N/A')} - {exp.get('end_date', 'N/A')}")
            else:
                print("    ❌ NONE")
            
            # Education
            print(f"\n  Education:")
            if latest_version.education:
                print(f"    Count: {len(latest_version.education)}")
                for i, edu in enumerate(latest_version.education[:3], 1):
                    print(f"    {i}. {edu.get('degree', 'N/A')} from {edu.get('institution', 'N/A')}")
            else:
                print("    ❌ NONE")
            
            # Projects
            print(f"\n  Projects:")
            if latest_version.projects:
                print(f"    Count: {len(latest_version.projects)}")
                for i, proj in enumerate(latest_version.projects[:3], 1):
                    print(f"    {i}. {proj.get('name', 'N/A')}")
            else:
                print("    ❌ NONE")
            
            # Experience Years
            print(f"\n  Experience Years: {latest_version.experience_years if latest_version.experience_years is not None else '❌ NOT CALCULATED'}")
            
            # Personal Info from parsed_data
            if latest_version.parsed_data:
                parsed_data = latest_version.parsed_data
                if isinstance(parsed_data, str):
                    try:
                        parsed_data = json.loads(parsed_data)
                    except:
                        parsed_data = {}
                
                if isinstance(parsed_data, dict):
                    print(f"\n  Personal Info from parsed_data:")
                    print(f"    Name: {parsed_data.get('name', 'N/A')}")
                    print(f"    Email: {parsed_data.get('email', 'N/A')}")
                    print(f"    Phone: {parsed_data.get('phone', 'N/A')}")
        
        print(f"\n{'='*80}\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_extracted_data()

