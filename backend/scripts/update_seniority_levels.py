"""
Script to update all existing seniority levels from 'unknown' to proper levels
Uses elite seniority analyzer to re-analyze all candidates
"""
from app.core.database import SessionLocal
from app.models.candidate_kundali import CandidateKundali
from app.models.resume import Resume
from app.resumes.seniority_analyzer import elite_seniority_analyzer
import structlog

logger = structlog.get_logger()

def _flatten_skills(skills_dict):
    """Flatten skills dictionary to list"""
    if isinstance(skills_dict, dict):
        flattened = []
        for category, skill_list in skills_dict.items():
            if isinstance(skill_list, list):
                flattened.extend(skill_list)
            elif skill_list:
                flattened.append(skill_list)
        return flattened
    elif isinstance(skills_dict, list):
        return skills_dict
    return []

def update_seniority_levels():
    """Update all seniority levels that are 'unknown'"""
    db = SessionLocal()
    
    try:
        # Get all kundalis with unknown seniority
        kundalis = db.query(CandidateKundali).filter(
            CandidateKundali.seniority_level == "unknown"
        ).all()
        
        print(f"Found {len(kundalis)} candidates with 'unknown' seniority level")
        
        updated_count = 0
        for kundali in kundalis:
            try:
                # Get resume for raw text
                candidate = kundali.candidate
                if not candidate or not candidate.resume_id:
                    continue
                
                resume = db.query(Resume).filter(Resume.id == candidate.resume_id).first()
                raw_text = resume.raw_text if resume else ""
                
                # Prepare resume data
                resume_data = {
                    "experience_years": kundali.total_experience_years or 0,
                    "experience": kundali.experience_data or [],
                    "projects": kundali.projects_data or [],
                    "education": kundali.education_data or [],
                    "skills": _flatten_skills({
                        "frontend": kundali.skills_frontend or [],
                        "backend": kundali.skills_backend or [],
                        "data": kundali.skills_data or [],
                        "devops": kundali.skills_devops or [],
                        "ai_ml": kundali.skills_ai_ml or [],
                        "tools": kundali.skills_tools or [],
                        "soft_skills": kundali.skills_soft or [],
                    }),
                }
                
                # Analyze with elite seniority analyzer
                seniority_analysis = elite_seniority_analyzer.analyze_seniority(
                    resume_data=resume_data,
                    raw_text=raw_text or ""
                )
                
                # Update kundali
                new_level = seniority_analysis.get("seniority_level", "mid")
                if new_level == "unknown":
                    new_level = "mid"  # Never allow unknown
                
                kundali.seniority_level = new_level
                kundali.seniority_confidence = seniority_analysis.get("confidence", 0.7)
                kundali.seniority_evidence = seniority_analysis.get("evidence", [])
                
                updated_count += 1
                print(f"Updated candidate {kundali.candidate_id}: {kundali.name} -> {new_level}")
                
            except Exception as e:
                logger.error("failed_to_update_seniority", 
                           candidate_id=kundali.candidate_id, 
                           error=str(e))
                # Set to mid as fallback
                kundali.seniority_level = "mid"
                kundali.seniority_confidence = 0.5
                updated_count += 1
                continue
        
        db.commit()
        print(f"\n✅ Successfully updated {updated_count} candidates")
        
    except Exception as e:
        db.rollback()
        logger.error("seniority_update_failed", error=str(e))
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting seniority level update...")
    update_seniority_levels()
    print("Done!")

