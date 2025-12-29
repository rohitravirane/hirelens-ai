"""
AI engine service for semantic matching and explainability
"""
from typing import Dict, List, Any, Optional
import openai
from sentence_transformers import SentenceTransformer
import structlog
import numpy as np

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache, get_cache_key

logger = structlog.get_logger()

# Initialize OpenAI client
if settings.OPENAI_API_KEY:
    openai.api_key = settings.OPENAI_API_KEY

# Initialize sentence transformer for embeddings (fallback)
embedding_model = None
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.warning("sentence_transformer_init_failed", error=str(e))


class AIEngine:
    """AI engine for matching and reasoning"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        cache_key = get_cache_key("embedding", text[:100])  # Use first 100 chars for cache key
        cached = get_cache(cache_key)
        if cached:
            return cached
        
        try:
            if self.openai_client:
                response = self.openai_client.embeddings.create(
                    model=settings.EMBEDDING_MODEL,
                    input=text,
                )
                embedding = response.data[0].embedding
            elif embedding_model:
                embedding = embedding_model.encode(text).tolist()
            else:
                # Fallback: simple hash-based embedding (not semantic)
                logger.warning("no_embedding_model_available")
                embedding = self._simple_embedding(text)
            
            set_cache(cache_key, embedding, ttl=settings.REDIS_CACHE_TTL * 24)  # Cache for 24 hours
            return embedding
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Simple fallback embedding (not semantic)"""
        # This is a placeholder - in production, always use proper embeddings
        return [0.0] * 384
    
    def calculate_semantic_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error("similarity_calculation_failed", error=str(e))
            return 0.0
    
    def generate_explanation(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Generate human-readable explanation for match result
        This is the CORE explainability feature
        """
        cache_key = get_cache_key(
            "explanation",
            str(candidate_data.get("id", "")),
            str(job_data.get("id", "")),
            str(scores.get("overall_score", 0)),
        )
        cached = get_cache(cache_key)
        if cached:
            return cached
        
        try:
            if not self.openai_client:
                return self._fallback_explanation(candidate_data, job_data, scores)
            
            prompt = self._build_explanation_prompt(candidate_data, job_data, scores)
            
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert hiring intelligence assistant. Provide clear, actionable, and business-friendly explanations for candidate-job matches. Be specific, honest, and helpful.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=settings.AI_TEMPERATURE,
                max_tokens=settings.AI_MAX_TOKENS,
            )
            
            explanation_text = response.choices[0].message.content
            
            # Parse the explanation into structured format
            explanation = self._parse_explanation(explanation_text, candidate_data, job_data, scores)
            
            set_cache(cache_key, explanation, ttl=settings.REDIS_CACHE_TTL)
            return explanation
            
        except Exception as e:
            logger.error("explanation_generation_failed", error=str(e))
            return self._fallback_explanation(candidate_data, job_data, scores)
    
    def _build_explanation_prompt(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        scores: Dict[str, float],
    ) -> str:
        """Build prompt for AI explanation"""
        candidate_skills = candidate_data.get("skills", [])
        job_required = job_data.get("required_skills", [])
        job_nice_to_have = job_data.get("nice_to_have_skills", [])
        
        prompt = f"""
Analyze this candidate-job match and provide a comprehensive explanation.

JOB: {job_data.get('title', 'N/A')} at {job_data.get('company', 'N/A')}
Required Skills: {', '.join(job_required[:10])}
Nice-to-Have Skills: {', '.join(job_nice_to_have[:10])}
Experience Required: {job_data.get('experience_years_required', 'N/A')} years

CANDIDATE:
Skills: {', '.join(candidate_skills[:20])}
Experience: {candidate_data.get('experience_years', 'N/A')} years
Education: {str(candidate_data.get('education', []))[:200]}

SCORES:
Overall: {scores.get('overall_score', 0):.1f}/100
Skill Match: {scores.get('skill_match_score', 0):.1f}/100
Experience: {scores.get('experience_score', 0):.1f}/100

Provide a structured explanation with:
1. Summary (2-3 sentences)
2. Strengths (3-5 specific points)
3. Weaknesses/Gaps (3-5 specific points)
4. Recommendations (2-3 actionable items)

Format as JSON with keys: summary, strengths (array), weaknesses (array), recommendations (array).
"""
        return prompt
    
    def _parse_explanation(
        self,
        explanation_text: str,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Parse AI explanation into structured format"""
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', explanation_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                return {
                    "summary": parsed.get("summary", explanation_text[:200]),
                    "strengths": parsed.get("strengths", []),
                    "weaknesses": parsed.get("weaknesses", []),
                    "recommendations": parsed.get("recommendations", []),
                    "confidence_score": scores.get("overall_score", 0) / 100,
                    "reasoning_quality": "high",
                }
        except Exception:
            pass
        
        # Fallback: structure the text response
        return {
            "summary": explanation_text[:300],
            "strengths": self._extract_list_items(explanation_text, "strength"),
            "weaknesses": self._extract_list_items(explanation_text, "weakness"),
            "recommendations": self._extract_list_items(explanation_text, "recommendation"),
            "confidence_score": scores.get("overall_score", 0) / 100,
            "reasoning_quality": "medium",
        }
    
    def _extract_list_items(self, text: str, keyword: str) -> List[str]:
        """Extract list items from text"""
        items = []
        lines = text.split('\n')
        in_section = False
        
        for line in lines:
            if keyword.lower() in line.lower():
                in_section = True
                continue
            if in_section and line.strip():
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    items.append(line.strip().lstrip('-•').strip())
                elif len(items) < 5:  # Limit items
                    items.append(line.strip())
        
        return items[:5]
    
    def _fallback_explanation(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Fallback explanation when AI is unavailable"""
        candidate_skills = set(candidate_data.get("skills", []))
        required_skills = set(job_data.get("required_skills", []))
        nice_to_have_skills = set(job_data.get("nice_to_have_skills", []))
        
        matched_required = candidate_skills.intersection(required_skills)
        matched_nice = candidate_skills.intersection(nice_to_have_skills)
        missing_required = required_skills - candidate_skills
        
        strengths = [
            f"Has {len(matched_required)} out of {len(required_skills)} required skills",
            f"Matches {len(matched_nice)} nice-to-have skills",
        ]
        if matched_required:
            strengths.append(f"Key skills: {', '.join(list(matched_required)[:3])}")
        
        weaknesses = []
        if missing_required:
            weaknesses.append(f"Missing required skills: {', '.join(list(missing_required)[:3])}")
        
        experience_diff = candidate_data.get("experience_years", 0) - job_data.get("experience_years_required", 0)
        if experience_diff < 0:
            weaknesses.append(f"Has {abs(experience_diff)} fewer years of experience than required")
        elif experience_diff > 0:
            strengths.append(f"Has {experience_diff} more years of experience than required")
        
        return {
            "summary": f"Candidate has an overall match score of {scores.get('overall_score', 0):.1f}/100. "
                      f"Key strengths include matching {len(matched_required)} required skills. "
                      f"Main gaps: {len(missing_required)} missing required skills.",
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": [
                "Review candidate's portfolio for practical experience",
                "Consider skills transferability from similar technologies",
            ],
            "confidence_score": scores.get("overall_score", 0) / 100,
            "reasoning_quality": "low",
        }


# Global instance
ai_engine = AIEngine()

