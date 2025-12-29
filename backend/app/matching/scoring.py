"""
Scoring engine for candidate-job matching
"""
from typing import Dict, List, Any, Optional
import structlog

from app.ai_engine.service import ai_engine

logger = structlog.get_logger()


class ScoringEngine:
    """Multi-dimensional scoring engine"""
    
    # Scoring weights (configurable)
    WEIGHTS = {
        "skill_match": 0.40,  # Highest weight
        "experience": 0.25,
        "project_similarity": 0.20,
        "domain_familiarity": 0.15,
    }
    
    def calculate_match_score(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Calculate comprehensive match score
        Returns scores for all dimensions plus overall score
        """
        scores = {
            "skill_match_score": self._calculate_skill_match(candidate_data, job_data),
            "experience_score": self._calculate_experience_score(candidate_data, job_data),
            "project_similarity_score": self._calculate_project_similarity(candidate_data, job_data),
            "domain_familiarity_score": self._calculate_domain_familiarity(candidate_data, job_data),
        }
        
        # Calculate weighted overall score
        overall_score = (
            scores["skill_match_score"] * self.WEIGHTS["skill_match"] +
            scores["experience_score"] * self.WEIGHTS["experience"] +
            scores["project_similarity_score"] * self.WEIGHTS["project_similarity"] +
            scores["domain_familiarity_score"] * self.WEIGHTS["domain_familiarity"]
        )
        
        scores["overall_score"] = round(overall_score, 2)
        
        # Determine confidence level
        if overall_score >= 80:
            scores["confidence_level"] = "high"
        elif overall_score >= 60:
            scores["confidence_level"] = "medium"
        else:
            scores["confidence_level"] = "low"
        
        return scores
    
    def _calculate_skill_match(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> float:
        """Calculate skill match score (0-100)"""
        candidate_skills = set(skill.lower() for skill in candidate_data.get("skills", []))
        required_skills = set(skill.lower() for skill in job_data.get("required_skills", []))
        nice_to_have_skills = set(skill.lower() for skill in job_data.get("nice_to_have_skills", []))
        
        if not required_skills:
            # If no required skills specified, give base score
            return 50.0
        
        # Required skills match (70% weight)
        matched_required = candidate_skills.intersection(required_skills)
        required_score = (len(matched_required) / len(required_skills)) * 70 if required_skills else 0
        
        # Nice-to-have skills match (30% weight)
        matched_nice = candidate_skills.intersection(nice_to_have_skills)
        nice_score = (len(matched_nice) / len(nice_to_have_skills)) * 30 if nice_to_have_skills else 0
        
        total_score = required_score + nice_score
        
        # Bonus for having extra relevant skills
        if len(candidate_skills) > len(required_skills):
            bonus = min(10, (len(candidate_skills) - len(required_skills)) * 2)
            total_score = min(100, total_score + bonus)
        
        return round(total_score, 2)
    
    def _calculate_experience_score(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> float:
        """Calculate experience relevance score (0-100)"""
        candidate_years = candidate_data.get("experience_years", 0) or 0
        required_years = job_data.get("experience_years_required", 0) or 0
        
        if required_years == 0:
            return 70.0  # Neutral score if no requirement
        
        if candidate_years >= required_years:
            # Has required or more experience
            excess = candidate_years - required_years
            if excess == 0:
                return 100.0
            elif excess <= 2:
                return 95.0
            elif excess <= 5:
                return 90.0
            else:
                return 85.0  # Overqualified
        else:
            # Less than required
            deficit = required_years - candidate_years
            if deficit <= 1:
                return 80.0
            elif deficit <= 2:
                return 60.0
            elif deficit <= 3:
                return 40.0
            else:
                return 20.0
    
    def _calculate_project_similarity(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> float:
        """Calculate project similarity score (0-100)"""
        candidate_projects = candidate_data.get("projects", [])
        if not candidate_projects:
            return 30.0  # Low score if no projects
        
        # Extract keywords from job description
        job_text = job_data.get("raw_text", "").lower()
        job_keywords = set(job_data.get("required_skills", []) + job_data.get("nice_to_have_skills", []))
        
        # Check project descriptions for relevance
        relevant_projects = 0
        for project in candidate_projects[:5]:  # Check top 5 projects
            project_text = str(project.get("description", "") + " " + project.get("name", "")).lower()
            
            # Count keyword matches
            matches = sum(1 for keyword in job_keywords if keyword.lower() in project_text)
            if matches >= 2:
                relevant_projects += 1
        
        if not candidate_projects:
            return 30.0
        
        score = (relevant_projects / min(len(candidate_projects), 5)) * 100
        return round(score, 2)
    
    def _calculate_domain_familiarity(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> float:
        """Calculate domain familiarity score (0-100)"""
        # Use semantic similarity of experience descriptions
        candidate_experience = candidate_data.get("experience", [])
        job_text = job_data.get("raw_text", "")
        
        if not candidate_experience or not job_text:
            return 50.0
        
        # Generate embeddings and calculate similarity
        try:
            # Combine candidate experience into text
            candidate_text = " ".join([
                exp.get("description", "") + " " + exp.get("title", "")
                for exp in candidate_experience[:3]
            ])
            
            # Generate embeddings
            candidate_embedding = ai_engine.generate_embedding(candidate_text[:1000])
            job_embedding = ai_engine.generate_embedding(job_text[:1000])
            
            # Calculate similarity
            similarity = ai_engine.calculate_semantic_similarity(candidate_embedding, job_embedding)
            
            # Convert to 0-100 score
            score = (similarity + 1) * 50  # Cosine similarity is -1 to 1, convert to 0-100
            return round(score, 2)
        except Exception as e:
            logger.error("domain_familiarity_calculation_failed", error=str(e))
            return 50.0  # Neutral score on error
    
    def calculate_percentile_rank(
        self,
        score: float,
        all_scores: List[float],
    ) -> float:
        """Calculate percentile rank of a score"""
        if not all_scores:
            return 0.0
        
        sorted_scores = sorted(all_scores, reverse=True)
        rank = sum(1 for s in sorted_scores if s < score)
        percentile = (rank / len(sorted_scores)) * 100
        return round(percentile, 2)


# Global instance
scoring_engine = ScoringEngine()

