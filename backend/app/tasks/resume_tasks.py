"""
Resume processing tasks
"""
from celery import Task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.resume import Resume, ResumeVersion
from app.resumes.parser import ResumeParser
from app.resumes.ai_parser import ai_parser
from app.resumes.resume_validator import ResumeValidator
from typing import Dict, Any
from sqlalchemy.orm import Session
import structlog

logger = structlog.get_logger()
parser = ResumeParser()
resume_validator = ResumeValidator()


@celery_app.task(bind=True, max_retries=3, soft_time_limit=600, time_limit=900)
def process_resume_task(self: Task, resume_id: int):
    """Process a resume asynchronously"""
    db: Session = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            logger.error("resume_not_found", resume_id=resume_id)
            return
        
        # Update status
        resume.processing_status = "processing"
        db.commit()
        
        # Extract text
        try:
            raw_text = parser.extract_text(resume.file_path)
            resume.raw_text = raw_text
        except Exception as e:
            logger.error("text_extraction_failed", resume_id=resume_id, error=str(e))
            resume.processing_status = "failed"
            resume.processing_error = str(e)
            db.commit()
            return
        
        # Validate if document is actually a resume
        is_valid_resume, validation_details = resume_validator.validate(raw_text)
        if not is_valid_resume:
            logger.warning("resume_validation_failed", 
                         resume_id=resume_id, 
                         score=validation_details.get('score', 0),
                         reasons=validation_details.get('reasons', []))
            resume.processing_status = "failed"
            resume.processing_error = f"Document does not appear to be a resume. Validation score: {validation_details.get('score', 0)}. Reasons: {', '.join(validation_details.get('reasons', []))}"
            db.commit()
            return
        
        logger.info("resume_validation_passed", 
                   resume_id=resume_id, 
                   score=validation_details.get('score', 0))
        
        # Parse resume using Candidate Kundali Parser (v2.0 - Masterpiece Architecture)
        # Philosophy: Resume-as-Source-of-Truth, Image-First, Qwen Vision
        try:
            from app.resumes.kundali_parser import kundali_parser
            from app.models.candidate_kundali import CandidateKundali
            from app.models.candidate import Candidate
            
            logger.info("starting_kundali_parsing", resume_id=resume_id, pdf_path=resume.file_path)
            
            # Use Kundali Parser (Qwen Vision-based)
            kundali_data = kundali_parser.parse_resume(resume.file_path, text_from_pdf=raw_text)
            candidate_kundali = kundali_data.get("candidate_kundali", {})
            
            logger.info("kundali_parsing_complete", 
                       resume_id=resume_id,
                       confidence=candidate_kundali.get("overall_confidence_score", 0.0),
                       has_experience=bool(candidate_kundali.get("experience")),
                       has_personality=bool(candidate_kundali.get("personality_inference")))
            
            # Convert Kundali to legacy parsed_data format (for backward compatibility)
            parsed_data = _kundali_to_parsed_data(candidate_kundali)
            parsed_data["_metadata"] = {
                "parser_version": "kundali-v2.0",
                "used_qwen_vision": kundali_parser.ollama_available and kundali_parser.use_vision,
                "kundali_confidence": candidate_kundali.get("overall_confidence_score", 0.0)
            }
            
            # Create/Update Candidate from Kundali
            _create_candidate_from_kundali(db, resume_id, candidate_kundali)
            
        except ImportError:
            # Fallback to legacy AI parser if Kundali parser not available
            logger.warning("kundali_parser_not_available_fallback_to_legacy", resume_id=resume_id)
            try:
                logger.info("starting_ai_resume_parsing", resume_id=resume_id, pdf_path=resume.file_path)
                parsed_data = ai_parser.parse_with_ai(raw_text, pdf_path=resume.file_path, force_reprocess=True)
                logger.info("ai_resume_parsing_complete", resume_id=resume_id, 
                           parser_version=parsed_data.get("_metadata", {}).get("parser_version", "unknown"))
        except Exception as e:
            logger.warning("ai_parsing_failed_fallback", resume_id=resume_id, error=str(e), exc_info=True)
            # Fallback to rule-based parsing
            try:
                parsed_data = parser.parse(raw_text)
                logger.info("fallback_parsing_success", resume_id=resume_id)
                # Calculate quality score for fallback parsing
                if "quality_score" not in parsed_data or parsed_data.get("quality_score") is None:
                    # Use the already imported ai_parser instance
                    quality_score = ai_parser._calculate_quality_score(parsed_data, raw_text)
                    parsed_data["quality_score"] = quality_score
                    logger.info("fallback_quality_score_calculated", resume_id=resume_id, score=quality_score)
            except Exception as e2:
                logger.error("resume_parsing_failed", resume_id=resume_id, error=str(e2), exc_info=True)
                resume.processing_status = "failed"
                resume.processing_error = str(e2)
                db.commit()
                return
        
        # Mark old versions as not current
        db.query(ResumeVersion).filter(
            ResumeVersion.resume_id == resume_id,
            ResumeVersion.is_current == True,
        ).update({"is_current": False})
        
        # Create new version
        latest_version = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .first()
        )
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Get quality score from parsed data (should be calculated by parser)
        quality_score = parsed_data.get("quality_score")
        logger.info("quality_score_from_parsed_data", resume_id=resume_id, quality_score=quality_score)
        if quality_score is None:
            # Fallback: Calculate quality score if parser didn't provide it
            logger.warning("quality_score_missing_from_parser", resume_id=resume_id)
            # Use the already imported ai_parser instance
            quality_score = ai_parser._calculate_quality_score(parsed_data, raw_text)
            logger.info("quality_score_calculated_in_task", resume_id=resume_id, score=quality_score)
        
        logger.info("final_quality_score", resume_id=resume_id, quality_score=quality_score, version=version_number)
        
        resume_version = ResumeVersion(
            resume_id=resume_id,
            version_number=version_number,
            parsed_data=parsed_data,
            skills=parsed_data.get("skills"),
            experience_years=parsed_data.get("experience_years"),
            education=parsed_data.get("education"),
            experience=parsed_data.get("experience"),
            projects=parsed_data.get("projects"),
            certifications=parsed_data.get("certifications"),
            languages=parsed_data.get("languages"),
            is_current=True,
            parser_version="3.0-ai-enhanced",  # Updated version for enhanced AI parsing
            quality_score=quality_score,
        )
        db.add(resume_version)
        
        # Update resume status
        resume.processing_status = "completed"
        db.commit()
        
        logger.info("resume_processed", resume_id=resume_id, version=version_number)
        
    except Exception as e:
        logger.exception("resume_processing_error", resume_id=resume_id, error=str(e))
        db.rollback()
        
        # Update resume status
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.processing_status = "failed"
            resume.processing_error = str(e)
            db.commit()
        
        # Retry
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()


def _kundali_to_parsed_data(kundali: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Candidate Kundali to legacy parsed_data format"""
    identity = kundali.get("identity", {})
    skills = kundali.get("skills", {})
    
    # Convert skills dict to list format
    all_skills = []
    for category, skill_list in skills.items():
        if isinstance(skill_list, list):
            all_skills.extend(skill_list)
    
    return {
        "name": identity.get("name", "unknown"),
        "email": identity.get("email", "unknown"),
        "phone": identity.get("phone", "unknown"),
        "contact": {
            "email": identity.get("email", "unknown"),
            "phone": identity.get("phone", "unknown"),
            "location": identity.get("location", "unknown"),
            "linkedin": kundali.get("online_presence", {}).get("linkedin", [None])[0] if kundali.get("online_presence", {}).get("linkedin") else None,
            "github": kundali.get("online_presence", {}).get("github", [None])[0] if kundali.get("online_presence", {}).get("github") else None,
            "portfolio": kundali.get("online_presence", {}).get("portfolio", [None])[0] if kundali.get("online_presence", {}).get("portfolio") else None,
        },
        "experience": kundali.get("experience", []),
        "education": kundali.get("education", []),
        "projects": kundali.get("projects", []),
        "skills": {
            "technical": all_skills,
            "languages": skills.get("soft_skills", []),
            "tools": skills.get("tools", []),
            "frameworks": []
        },
        "certifications": kundali.get("certifications", []),
        "languages": kundali.get("languages", []),
        "experience_years": kundali.get("total_experience_years", 0),
        "quality_score": int(kundali.get("overall_confidence_score", 0.0) * 100),
        # Store full Kundali for advanced features
        "_kundali": kundali
    }


def _create_candidate_from_kundali(db: Session, resume_id: int, kundali: Dict[str, Any]):
    """Create or update Candidate and CandidateKundali from Kundali data"""
    from app.models.candidate import Candidate
    from app.models.candidate_kundali import CandidateKundali
    
    identity = kundali.get("identity", {})
    online_presence = kundali.get("online_presence", {})
    skills = kundali.get("skills", {})
    personality = kundali.get("personality_inference", {})
    seniority = kundali.get("seniority_assessment", {})
    
    # Find or create Candidate
    candidate = db.query(Candidate).filter(Candidate.resume_id == resume_id).first()
    if not candidate:
        # Extract name
        name = identity.get("name", "unknown")
        name_parts = name.split(" ", 1)
        candidate = Candidate(
            resume_id=resume_id,
            first_name=name_parts[0] if name_parts else "unknown",
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            email=identity.get("email", "unknown"),
            phone=identity.get("phone", "unknown"),
            linkedin_url=online_presence.get("linkedin", [None])[0] if online_presence.get("linkedin") else None,
            portfolio_url=online_presence.get("portfolio", [None])[0] if online_presence.get("portfolio") else None,
        )
        db.add(candidate)
        db.flush()  # Get candidate.id
    else:
        # Update existing candidate
        name = identity.get("name", "unknown")
        name_parts = name.split(" ", 1)
        candidate.first_name = name_parts[0] if name_parts else candidate.first_name
        candidate.last_name = name_parts[1] if len(name_parts) > 1 else candidate.last_name
        candidate.email = identity.get("email", candidate.email)
        candidate.phone = identity.get("phone", candidate.phone)
        candidate.linkedin_url = online_presence.get("linkedin", [None])[0] if online_presence.get("linkedin") else candidate.linkedin_url
        candidate.portfolio_url = online_presence.get("portfolio", [None])[0] if online_presence.get("portfolio") else candidate.portfolio_url
    
    # Create or update CandidateKundali
    kundali_record = db.query(CandidateKundali).filter(CandidateKundali.candidate_id == candidate.id).first()
    if not kundali_record:
        kundali_record = CandidateKundali(
            candidate_id=candidate.id,
            name=identity.get("name", "unknown"),
            email=identity.get("email", "unknown"),
            phone=identity.get("phone", "unknown"),
            location=identity.get("location", "unknown"),
            portfolio_urls=online_presence.get("portfolio", []),
            github_urls=online_presence.get("github", []),
            linkedin_urls=online_presence.get("linkedin", []),
            other_links=online_presence.get("other_links", []),
            summary=kundali.get("summary", ""),
            total_experience_years=kundali.get("total_experience_years", 0),
            experience_data=kundali.get("experience", []),
            education_data=kundali.get("education", []),
            projects_data=kundali.get("projects", []),
            skills_frontend=skills.get("frontend", []),
            skills_backend=skills.get("backend", []),
            skills_data=skills.get("data", []),
            skills_devops=skills.get("devops", []),
            skills_ai_ml=skills.get("ai_ml", []),
            skills_tools=skills.get("tools", []),
            skills_soft=skills.get("soft_skills", []),
            certifications_data=kundali.get("certifications", []),
            languages=kundali.get("languages", []),
            seniority_level=seniority.get("level", "unknown"),
            seniority_confidence=seniority.get("confidence", 0.0),
            seniority_evidence=seniority.get("evidence", []),
            work_style=personality.get("work_style", "unknown"),
            ownership_level=personality.get("ownership_level", "unknown"),
            learning_orientation=personality.get("learning_orientation", "unknown"),
            communication_strength=personality.get("communication_strength", "unknown"),
            risk_profile=personality.get("risk_profile", "unknown"),
            personality_confidence=personality.get("confidence", 0.0),
            leadership_signals=kundali.get("leadership_signals", []),
            red_flags=kundali.get("red_flags", []),
            overall_confidence_score=kundali.get("overall_confidence_score", 0.0),
        )
        db.add(kundali_record)
    else:
        # Update existing Kundali
        kundali_record.name = identity.get("name", kundali_record.name)
        kundali_record.email = identity.get("email", kundali_record.email)
        kundali_record.phone = identity.get("phone", kundali_record.phone)
        kundali_record.location = identity.get("location", kundali_record.location)
        kundali_record.portfolio_urls = online_presence.get("portfolio", [])
        kundali_record.github_urls = online_presence.get("github", [])
        kundali_record.linkedin_urls = online_presence.get("linkedin", [])
        kundali_record.other_links = online_presence.get("other_links", [])
        kundali_record.summary = kundali.get("summary", kundali_record.summary)
        kundali_record.total_experience_years = kundali.get("total_experience_years", kundali_record.total_experience_years)
        kundali_record.experience_data = kundali.get("experience", [])
        kundali_record.education_data = kundali.get("education", [])
        kundali_record.projects_data = kundali.get("projects", [])
        kundali_record.skills_frontend = skills.get("frontend", [])
        kundali_record.skills_backend = skills.get("backend", [])
        kundali_record.skills_data = skills.get("data", [])
        kundali_record.skills_devops = skills.get("devops", [])
        kundali_record.skills_ai_ml = skills.get("ai_ml", [])
        kundali_record.skills_tools = skills.get("tools", [])
        kundali_record.skills_soft = skills.get("soft_skills", [])
        kundali_record.certifications_data = kundali.get("certifications", [])
        kundali_record.languages = kundali.get("languages", [])
        kundali_record.seniority_level = seniority.get("level", kundali_record.seniority_level)
        kundali_record.seniority_confidence = seniority.get("confidence", kundali_record.seniority_confidence)
        kundali_record.seniority_evidence = seniority.get("evidence", [])
        kundali_record.work_style = personality.get("work_style", kundali_record.work_style)
        kundali_record.ownership_level = personality.get("ownership_level", kundali_record.ownership_level)
        kundali_record.learning_orientation = personality.get("learning_orientation", kundali_record.learning_orientation)
        kundali_record.communication_strength = personality.get("communication_strength", kundali_record.communication_strength)
        kundali_record.risk_profile = personality.get("risk_profile", kundali_record.risk_profile)
        kundali_record.personality_confidence = personality.get("confidence", kundali_record.personality_confidence)
        kundali_record.leadership_signals = kundali.get("leadership_signals", [])
        kundali_record.red_flags = kundali.get("red_flags", [])
        kundali_record.overall_confidence_score = kundali.get("overall_confidence_score", kundali_record.overall_confidence_score)
    
    db.commit()
    logger.info("candidate_kundali_created", candidate_id=candidate.id, resume_id=resume_id)

