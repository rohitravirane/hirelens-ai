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
)
from app.models.matching import MatchResult, AIExplanation
from app.models.candidate import Candidate

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
    """Get ranked candidates for a job"""
    match_results = matching_service.rank_candidates_for_job(db, job_id, limit)
    
    rankings = []
    for match_result in match_results:
        candidate = db.query(Candidate).filter(Candidate.id == match_result.candidate_id).first()
        ai_explanation = (
            db.query(AIExplanation)
            .filter(AIExplanation.match_result_id == match_result.id)
            .first()
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
        ))
    
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

