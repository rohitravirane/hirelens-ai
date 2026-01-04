"""
Matching routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.matching.service import matching_service
from app.matching.schemas import (
    MatchResultResponse,
    MatchDetailResponse,
    CandidateRankingResponse,
    AIExplanationResponse,
    CandidateKundaliSummaryResponse,
)
from app.models.matching import MatchResult, AIExplanation
from app.models.candidate import Candidate
from app.models.job import JobDescription
from app.models.candidate_kundali import CandidateKundali

router = APIRouter(prefix="/api/v1/matching", tags=["Matching"])
logger = structlog.get_logger()


@router.post("/match", response_model=MatchDetailResponse, status_code=status.HTTP_201_CREATED)
def create_match(
    candidate_id: int,
    job_id: int,
    force_recalculate: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Match a candidate to a job"""
    try:
        match_result = matching_service.match_candidate_to_job(
            db, candidate_id, job_id, force_recalculate
        )
        
        # Get AI explanation
        ai_explanation = (
            db.query(AIExplanation)
            .filter(AIExplanation.match_result_id == match_result.id)
            .first()
        )
        
        return MatchDetailResponse(
            id=match_result.id,
            candidate_id=match_result.candidate_id,
            job_description_id=match_result.job_description_id,
            overall_score=match_result.overall_score,
            confidence_level=match_result.confidence_level,
            skill_match_score=match_result.skill_match_score,
            experience_score=match_result.experience_score,
            project_similarity_score=match_result.project_similarity_score,
            domain_familiarity_score=match_result.domain_familiarity_score,
            percentile_rank=match_result.percentile_rank,
            calculated_at=match_result.calculated_at,
            ai_explanation=AIExplanationResponse(
                summary=ai_explanation.summary if ai_explanation else None,
                strengths=ai_explanation.strengths if ai_explanation else None,
                weaknesses=ai_explanation.weaknesses if ai_explanation else None,
                recommendations=ai_explanation.recommendations if ai_explanation else None,
                confidence_score=ai_explanation.confidence_score if ai_explanation else None,
                reasoning_quality=ai_explanation.reasoning_quality if ai_explanation else None,
            ) if ai_explanation else None,
        )
    except ValueError as e:
        raise NotFoundError("Resource", str(e))


@router.get("/job/{job_id}/rankings", response_model=List[CandidateRankingResponse])
def get_candidate_rankings(
    job_id: int,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get ranked candidates for a job.
    This recalculates matches and percentile ranks for all candidates.
    """
    # Verify job exists
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise NotFoundError("Job", str(job_id))
    
    # Rank all candidates for this job (recalculates matches and percentile ranks)
    match_results = matching_service.rank_candidates_for_job(db, job_id, limit)
    
    rankings = []
    for match_result in match_results:
        candidate = db.query(Candidate).filter(Candidate.id == match_result.candidate_id).first()
        if not candidate:
            logger.warning("candidate_not_found_for_ranking", candidate_id=match_result.candidate_id)
            continue
            
        ai_explanation = (
            db.query(AIExplanation)
            .filter(AIExplanation.match_result_id == match_result.id)
            .first()
        )
        
        # Get Kundali data if available
        kundali = (
            db.query(CandidateKundali)
            .filter(CandidateKundali.candidate_id == candidate.id)
            .first()
        )
        
        kundali_summary = None
        if kundali:
            kundali_summary = CandidateKundaliSummaryResponse(
                name=kundali.name,
                total_experience_years=kundali.total_experience_years,
                seniority_level=kundali.seniority_level,
                skills_frontend=kundali.skills_frontend,
                skills_backend=kundali.skills_backend,
                skills_devops=kundali.skills_devops,
                skills_ai_ml=kundali.skills_ai_ml,
                skills_tools=kundali.skills_tools,
                skills_soft=kundali.skills_soft,
                summary=kundali.summary,
                overall_confidence_score=kundali.overall_confidence_score,
            )
        
        rankings.append(CandidateRankingResponse(
            candidate_id=candidate.id,
            candidate_name=f"{candidate.first_name or ''} {candidate.last_name or ''}".strip() or None,
            candidate_email=candidate.email,
            match_result=MatchDetailResponse(
                id=match_result.id,
                candidate_id=match_result.candidate_id,
                job_description_id=match_result.job_description_id,
                overall_score=match_result.overall_score,
                confidence_level=match_result.confidence_level,
                skill_match_score=match_result.skill_match_score,
                experience_score=match_result.experience_score,
                project_similarity_score=match_result.project_similarity_score,
                domain_familiarity_score=match_result.domain_familiarity_score,
                percentile_rank=match_result.percentile_rank,
                calculated_at=match_result.calculated_at,
                ai_explanation=AIExplanationResponse(
                    summary=ai_explanation.summary if ai_explanation else None,
                    strengths=ai_explanation.strengths if ai_explanation else None,
                    weaknesses=ai_explanation.weaknesses if ai_explanation else None,
                    recommendations=ai_explanation.recommendations if ai_explanation else None,
                    confidence_score=ai_explanation.confidence_score if ai_explanation else None,
                    reasoning_quality=ai_explanation.reasoning_quality if ai_explanation else None,
                ) if ai_explanation else None,
            ),
            kundali=kundali_summary,
        ))
    
    logger.info("rankings_fetched", job_id=job_id, count=len(rankings))
    return rankings


@router.get("/match/{match_id}", response_model=MatchDetailResponse)
def get_match(
    match_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get match details"""
    match_result = db.query(MatchResult).filter(MatchResult.id == match_id).first()
    if not match_result:
        raise NotFoundError("Match result", str(match_id))
    
    ai_explanation = (
        db.query(AIExplanation)
        .filter(AIExplanation.match_result_id == match_result.id)
        .first()
    )
    
    return MatchDetailResponse(
        id=match_result.id,
        candidate_id=match_result.candidate_id,
        job_description_id=match_result.job_description_id,
        overall_score=match_result.overall_score,
        confidence_level=match_result.confidence_level,
        skill_match_score=match_result.skill_match_score,
        experience_score=match_result.experience_score,
        project_similarity_score=match_result.project_similarity_score,
        domain_familiarity_score=match_result.domain_familiarity_score,
        percentile_rank=match_result.percentile_rank,
        calculated_at=match_result.calculated_at,
        ai_explanation=AIExplanationResponse(
            summary=ai_explanation.summary if ai_explanation else None,
            strengths=ai_explanation.strengths if ai_explanation else None,
            weaknesses=ai_explanation.weaknesses if ai_explanation else None,
            recommendations=ai_explanation.recommendations if ai_explanation else None,
            confidence_score=ai_explanation.confidence_score if ai_explanation else None,
            reasoning_quality=ai_explanation.reasoning_quality if ai_explanation else None,
        ) if ai_explanation else None,
    )


@router.post("/candidate/{candidate_id}/find-best-match", response_model=MatchDetailResponse)
def find_best_match_for_candidate(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Match candidate to all active jobs and return the job with highest match score.
    This is used for "Match" button that automatically finds the best job for a candidate.
    """
    # Verify candidate exists
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise NotFoundError("Candidate", str(candidate_id))
    
    # Get all active jobs
    active_jobs = (
        db.query(JobDescription)
        .filter(JobDescription.is_active == True)
        .all()
    )
    
    if not active_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active jobs found"
        )
    
    # Match candidate to all jobs
    best_match = None
    best_score = -1.0
    
    for job in active_jobs:
        try:
            match_result = matching_service.match_candidate_to_job(
                db, candidate_id, job.id, force_recalculate=False
            )
            if match_result.overall_score > best_score:
                best_score = match_result.overall_score
                best_match = match_result
        except Exception as e:
            logger.warning(
                "match_failed_for_best_match",
                candidate_id=candidate_id,
                job_id=job.id,
                error=str(e)
            )
            continue
    
    if not best_match:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to match candidate to any job"
        )
    
    # Get AI explanation for best match
    ai_explanation = (
        db.query(AIExplanation)
        .filter(AIExplanation.match_result_id == best_match.id)
        .first()
    )
    
    logger.info(
        "best_match_found",
        candidate_id=candidate_id,
        job_id=best_match.job_description_id,
        score=best_match.overall_score
    )
    
    return MatchDetailResponse(
        id=best_match.id,
        candidate_id=best_match.candidate_id,
        job_description_id=best_match.job_description_id,
        overall_score=best_match.overall_score,
        confidence_level=best_match.confidence_level,
        skill_match_score=best_match.skill_match_score,
        experience_score=best_match.experience_score,
        project_similarity_score=best_match.project_similarity_score,
        domain_familiarity_score=best_match.domain_familiarity_score,
        percentile_rank=best_match.percentile_rank,
        calculated_at=best_match.calculated_at,
        ai_explanation=AIExplanationResponse(
            summary=ai_explanation.summary if ai_explanation else None,
            strengths=ai_explanation.strengths if ai_explanation else None,
            weaknesses=ai_explanation.weaknesses if ai_explanation else None,
            recommendations=ai_explanation.recommendations if ai_explanation else None,
            confidence_score=ai_explanation.confidence_score if ai_explanation else None,
            reasoning_quality=ai_explanation.reasoning_quality if ai_explanation else None,
        ) if ai_explanation else None,
    )
