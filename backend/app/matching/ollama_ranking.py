"""
World-Class Ollama-Based Ranking System
Deep, consistent, structured candidate-job matching using Ollama LLM
"""
from typing import Dict, List, Any, Optional
import json
import requests
import structlog
from datetime import datetime

logger = structlog.get_logger()

# Ollama configuration
OLLAMA_ENDPOINT = "http://host.docker.internal:11434"
OLLAMA_MODEL = "qwen2.5:7b-instruct-q4_K_M"  # Same model used for resume parsing


class OllamaRankingEngine:
    """
    World-Class Ranking Engine using Ollama for Deep Candidate-Job Matching
    
    Features:
    - Deep semantic analysis of candidate and job profiles
    - Multi-dimensional scoring (skills, experience, projects, domain, culture fit)
    - Consistent, structured output format
    - World-class matching accuracy
    """
    
    def __init__(self):
        self.ollama_endpoint = OLLAMA_ENDPOINT
        self.model = OLLAMA_MODEL
        self.available = self._check_ollama_availability()
        
        if self.available:
            logger.info("ollama_ranking_engine_initialized", model=self.model)
        else:
            logger.warning("ollama_ranking_engine_unavailable", endpoint=self.ollama_endpoint)
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning("ollama_not_available_for_ranking", error=str(e))
            return False
    
    def _build_world_class_prompt(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        base_scores: Dict[str, float]
    ) -> str:
        """
        Build world-class comprehensive prompt for deep matching analysis
        """
        # Extract candidate information
        candidate_skills = candidate_data.get("skills", [])
        candidate_exp_years = candidate_data.get("experience_years", 0)
        candidate_experience = candidate_data.get("experience", [])
        candidate_projects = candidate_data.get("projects", [])
        candidate_education = candidate_data.get("education", [])
        
        # Extract job information
        job_title = job_data.get("title", "")
        job_company = job_data.get("company", "")
        job_required_skills = job_data.get("required_skills", [])
        job_nice_to_have = job_data.get("nice_to_have_skills", [])
        job_exp_required = job_data.get("experience_years_required", 0)
        job_description = job_data.get("raw_text", "")
        
        prompt = f"""You are an expert HR and technical recruiter with 20+ years of experience in candidate-job matching. Your task is to perform a DEEP, COMPREHENSIVE analysis of how well a candidate matches a job position.

# TASK: Deep Candidate-Job Matching Analysis

## JOB REQUIREMENTS:
**Position:** {job_title}
**Company:** {job_company}
**Required Experience:** {job_exp_required} years
**Required Skills:** {', '.join(job_required_skills) if job_required_skills else 'Not specified'}
**Nice-to-Have Skills:** {', '.join(job_nice_to_have) if job_nice_to_have else 'None'}
**Job Description:** {job_description[:2000] if job_description else 'Not provided'}

## CANDIDATE PROFILE:
**Experience Years:** {candidate_exp_years} years
**Skills:** {', '.join(candidate_skills) if candidate_skills else 'Not specified'}
**Work Experience:** {json.dumps(candidate_experience[:5], indent=2) if candidate_experience else 'Not provided'}
**Projects:** {json.dumps(candidate_projects[:5], indent=2) if candidate_projects else 'Not provided'}
**Education:** {json.dumps(candidate_education, indent=2) if candidate_education else 'Not provided'}

## BASE SCORES (from rule-based matching):
- Skill Match: {base_scores.get('skill_match_score', 0):.1f}/100
- Experience: {base_scores.get('experience_score', 0):.1f}/100
- Project Similarity: {base_scores.get('project_similarity_score', 0):.1f}/100
- Domain Familiarity: {base_scores.get('domain_familiarity_score', 0):.1f}/100
- Overall: {base_scores.get('overall_score', 0):.1f}/100

## YOUR TASK:
Perform a DEEP, MULTI-DIMENSIONAL analysis and provide a comprehensive matching assessment. Consider:

1. **SKILL MATCHING (40% weight)**
   - Exact skill matches vs required skills
   - Transferable skills (e.g., React → Vue, Java → Spring)
   - Skill depth and proficiency level
   - Missing critical skills and their impact
   - Nice-to-have skills bonus

2. **EXPERIENCE ALIGNMENT (25% weight)**
   - Years of experience vs required
   - Relevant industry experience
   - Role similarity (e.g., Senior Dev → Senior Dev)
   - Career progression and growth trajectory
   - Experience quality over quantity

3. **PROJECT SIMILARITY (20% weight)**
   - Project complexity and scale
   - Technology stack alignment
   - Domain/industry relevance
   - Problem-solving approaches
   - Impact and achievements

4. **DOMAIN & CULTURE FIT (15% weight)**
   - Industry/domain knowledge
   - Team collaboration experience
   - Communication skills (from projects/experience)
   - Adaptability and learning ability
   - Cultural alignment indicators

5. **OVERALL ASSESSMENT**
   - Strengths (top 3-5)
   - Weaknesses/Gaps (top 3-5)
   - Recommendations for improvement
   - Hiring recommendation (Strong Match / Good Match / Moderate Match / Weak Match)
   - Confidence level (High / Medium / Low)

## OUTPUT FORMAT (JSON ONLY):
Provide your analysis in this EXACT JSON structure:

{{
  "overall_score": <0-100 float>,
  "confidence_level": "<high|medium|low>",
  "hiring_recommendation": "<Strong Match|Good Match|Moderate Match|Weak Match>",
  "dimension_scores": {{
    "skill_match": <0-100 float>,
    "experience_alignment": <0-100 float>,
    "project_similarity": <0-100 float>,
    "domain_culture_fit": <0-100 float>
  }},
  "detailed_analysis": {{
    "skill_analysis": {{
      "matched_skills": ["skill1", "skill2"],
      "missing_critical_skills": ["skill1", "skill2"],
      "transferable_skills": ["skill1 → skill2"],
      "nice_to_have_matches": ["skill1", "skill2"],
      "skill_depth_score": <0-100 float>,
      "overall_skill_match": <0-100 float>
    }},
    "experience_analysis": {{
      "years_match": <0-100 float>,
      "relevance_score": <0-100 float>,
      "career_progression_score": <0-100 float>,
      "quality_score": <0-100 float>,
      "overall_experience_match": <0-100 float>
    }},
    "project_analysis": {{
      "complexity_match": <0-100 float>,
      "tech_stack_alignment": <0-100 float>,
      "domain_relevance": <0-100 float>,
      "impact_score": <0-100 float>,
      "overall_project_match": <0-100 float>
    }},
    "domain_culture_analysis": {{
      "industry_knowledge": <0-100 float>,
      "team_collaboration": <0-100 float>,
      "adaptability": <0-100 float>,
      "communication": <0-100 float>,
      "overall_culture_fit": <0-100 float>
    }}
  }},
  "strengths": [
    "Strength 1 with brief explanation",
    "Strength 2 with brief explanation",
    "Strength 3 with brief explanation"
  ],
  "weaknesses": [
    "Weakness 1 with brief explanation",
    "Weakness 2 with brief explanation",
    "Weakness 3 with brief explanation"
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2",
    "Recommendation 3"
  ],
  "reasoning": "2-3 sentence explanation of overall assessment"
}}

## CRITICAL REQUIREMENTS:
1. Be CONSISTENT: Use the same evaluation criteria for all candidates
2. Be DEEP: Analyze beyond surface-level matches, consider context and nuances
3. Be ACCURATE: Base scores on actual evidence from candidate profile
4. Be STRUCTURED: Follow the JSON format exactly
5. Be FAIR: Consider transferable skills and growth potential
6. Be COMPREHENSIVE: Cover all dimensions thoroughly

## SCORING GUIDELINES:
- 90-100: Exceptional match, exceeds requirements
- 80-89: Strong match, meets all critical requirements
- 70-79: Good match, meets most requirements with minor gaps
- 60-69: Moderate match, meets basic requirements but has gaps
- 50-59: Weak match, significant gaps in requirements
- 0-49: Poor match, major misalignment

Now provide your analysis in the JSON format above. Be thorough, accurate, and consistent."""

        return prompt
    
    def generate_ranking_analysis(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        base_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive ranking analysis using Ollama
        
        Returns:
            Dict with detailed matching analysis and scores
        """
        if not self.available:
            logger.warning("ollama_not_available_falling_back_to_base_scores")
            return self._fallback_analysis(candidate_data, job_data, base_scores)
        
        try:
            prompt = self._build_world_class_prompt(candidate_data, job_data, base_scores)
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Low temperature for consistency
                        "top_p": 0.9,
                        "max_tokens": 4000,  # Enough for comprehensive analysis
                    }
                },
                timeout=120  # 2 minutes timeout for deep analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Extract JSON from response (handle markdown code blocks)
                json_text = self._extract_json_from_response(response_text)
                
                if json_text:
                    analysis = json.loads(json_text)
                    logger.info("ollama_ranking_analysis_generated", 
                              overall_score=analysis.get("overall_score", 0))
                    return analysis
                else:
                    logger.error("failed_to_parse_ollama_response", response_preview=response_text[:200])
                    return self._fallback_analysis(candidate_data, job_data, base_scores)
            else:
                logger.error("ollama_api_error", status_code=response.status_code)
                return self._fallback_analysis(candidate_data, job_data, base_scores)
                
        except Exception as e:
            logger.error("ollama_ranking_generation_failed", error=str(e))
            return self._fallback_analysis(candidate_data, job_data, base_scores)
    
    def _extract_json_from_response(self, response_text: str) -> Optional[str]:
        """Extract JSON from LLM response (handles markdown code blocks)"""
        # Remove markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                return response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                return response_text[start:end].strip()
        
        # Try to find JSON object directly
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            return response_text[start:end].strip()
        
        return None
    
    def _fallback_analysis(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        base_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Fallback analysis when Ollama is unavailable"""
        overall_score = base_scores.get("overall_score", 0)
        
        return {
            "overall_score": overall_score,
            "confidence_level": "medium",
            "hiring_recommendation": "Moderate Match" if overall_score >= 60 else "Weak Match",
            "dimension_scores": {
                "skill_match": base_scores.get("skill_match_score", 0),
                "experience_alignment": base_scores.get("experience_score", 0),
                "project_similarity": base_scores.get("project_similarity_score", 0),
                "domain_culture_fit": base_scores.get("domain_familiarity_score", 0),
            },
            "detailed_analysis": {
                "skill_analysis": {
                    "overall_skill_match": base_scores.get("skill_match_score", 0),
                },
                "experience_analysis": {
                    "overall_experience_match": base_scores.get("experience_score", 0),
                },
                "project_analysis": {
                    "overall_project_match": base_scores.get("project_similarity_score", 0),
                },
                "domain_culture_analysis": {
                    "overall_culture_fit": base_scores.get("domain_familiarity_score", 0),
                }
            },
            "strengths": ["Rule-based matching used (Ollama unavailable)"],
            "weaknesses": ["Deep analysis unavailable"],
            "recommendations": ["Ensure Ollama is running for comprehensive analysis"],
            "reasoning": "Fallback to rule-based scoring. Ollama analysis unavailable."
        }


# Global instance
ollama_ranking_engine = OllamaRankingEngine()

