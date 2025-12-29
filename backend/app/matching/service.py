"""
Matching service - orchestrates scoring and AI explanation
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import structlog

from app.matching.scoring import scoring_engine
from app.ai_engine.service import ai_engine
from app.core.config import settings
from app.models.resume import ResumeVersion
from app.models.job import JobDescription
from app.models.candidate import Candidate
from app.models.matching import MatchResult, AIExplanation

logger = structlog.get_logger()


class MatchingService:
    """Service for matching candidates to jobs"""
    
    def match_candidate_to_job(
        self,
        db: Session,
        candidate_id: int,
        job_id: int,
        force_recalculate: bool = False,
    ) -> MatchResult:
        """
        Match a candidate to a job and generate scores + explanation
        """
        # Check if match already exists
        if not force_recalculate:
            existing_match = (
                db.query(MatchResult)
                .filter(
                    MatchResult.candidate_id == candidate_id,
                    MatchResult.job_description_id == job_id,
                    MatchResult.is_active == True,
                )
                .first()
            )
            if existing_match:
                return existing_match
        
        # Get candidate data
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        # Get resume data
        resume_version = (
            db.query(ResumeVersion)
            .join(ResumeVersion.resume)
            .filter(
                ResumeVersion.resume_id == candidate.resume_id,
                ResumeVersion.is_current == True,
            )
            .first()
        )
        
        if not resume_version:
            raise ValueError(f"Resume not found for candidate {candidate_id}")
        
        # Get job data
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Prepare data for scoring
        candidate_data = {
            "id": candidate.id,
            "skills": resume_version.skills or [],
            "experience_years": resume_version.experience_years,
            "experience": resume_version.experience or [],
            "projects": resume_version.projects or [],
            "education": resume_version.education or [],
        }
        
        job_data = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "required_skills": job.required_skills or [],
            "nice_to_have_skills": job.nice_to_have_skills or [],
            "experience_years_required": job.experience_years_required,
            "raw_text": job.raw_text or "",
        }
        
        # Calculate scores
        scores = scoring_engine.calculate_match_score(candidate_data, job_data)
        
        # Generate AI explanation
        explanation_data = ai_engine.generate_explanation(candidate_data, job_data, scores)
        
        # Create or update match result
        match_result = (
            db.query(MatchResult)
            .filter(
                MatchResult.candidate_id == candidate_id,
                MatchResult.job_description_id == job_id,
            )
            .first()
        )
        
        if match_result:
            # Update existing
            match_result.overall_score = scores["overall_score"]
            match_result.confidence_level = scores["confidence_level"]
            match_result.skill_match_score = scores["skill_match_score"]
            match_result.experience_score = scores["experience_score"]
            match_result.project_similarity_score = scores["project_similarity_score"]
            match_result.domain_familiarity_score = scores["domain_familiarity_score"]
        else:
            # Create new
            match_result = MatchResult(
                candidate_id=candidate_id,
                job_description_id=job_id,
                overall_score=scores["overall_score"],
                confidence_level=scores["confidence_level"],
                skill_match_score=scores["skill_match_score"],
                experience_score=scores["experience_score"],
                project_similarity_score=scores["project_similarity_score"],
                domain_familiarity_score=scores["domain_familiarity_score"],
            )
            db.add(match_result)
        
        db.flush()
        
        # Create or update AI explanation
        ai_explanation = (
            db.query(AIExplanation)
            .filter(AIExplanation.match_result_id == match_result.id)
            .first()
        )
        
        if ai_explanation:
            ai_explanation.summary = explanation_data.get("summary")
            ai_explanation.strengths = explanation_data.get("strengths", [])
            ai_explanation.weaknesses = explanation_data.get("weaknesses", [])
            ai_explanation.recommendations = explanation_data.get("recommendations", [])
            ai_explanation.confidence_score = explanation_data.get("confidence_score", 0)
            ai_explanation.reasoning_quality = explanation_data.get("reasoning_quality", "medium")
        else:
            ai_explanation = AIExplanation(
                match_result_id=match_result.id,
                summary=explanation_data.get("summary"),
                strengths=explanation_data.get("strengths", []),
                weaknesses=explanation_data.get("weaknesses", []),
                recommendations=explanation_data.get("recommendations", []),
                confidence_score=explanation_data.get("confidence_score", 0),
                reasoning_quality=explanation_data.get("reasoning_quality", "medium"),
                model_used=settings.HUGGINGFACE_LLM_MODEL if ai_engine.provider == "huggingface" else (settings.OPENAI_MODEL if ai_engine.provider == "openai" else "fallback"),
            )
            db.add(ai_explanation)
        
        db.commit()
        db.refresh(match_result)
        
        logger.info(
            "match_calculated",
            candidate_id=candidate_id,
            job_id=job_id,
            score=scores["overall_score"],
        )
        
        return match_result
    
    def rank_candidates_for_job(
        self,
        db: Session,
        job_id: int,
        limit: int = 100,
    ) -> List[MatchResult]:
        """
        Rank all candidates for a job
        """
        # Get all active candidates with resumes
        candidates = (
            db.query(Candidate)
            .join(Candidate.resume)
            .filter(Candidate.status != "rejected")
            .all()
        )
        
        match_results = []
        for candidate in candidates:
            try:
                match_result = self.match_candidate_to_job(db, candidate.id, job_id)
                match_results.append(match_result)
            except Exception as e:
                logger.error(
                    "match_calculation_failed",
                    candidate_id=candidate.id,
                    job_id=job_id,
                    error=str(e),
                )
                continue
        
        # Sort by overall score
        match_results.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Calculate percentile ranks
        scores = [mr.overall_score for mr in match_results]
        for match_result in match_results:
            match_result.percentile_rank = scoring_engine.calculate_percentile_rank(
                match_result.overall_score, scores
            )
        
        db.commit()
        
        return match_results[:limit]


# Global instance
matching_service = MatchingService()

