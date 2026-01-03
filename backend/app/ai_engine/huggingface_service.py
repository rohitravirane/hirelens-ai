"""
Hugging Face AI Service - Local & Production Ready
Runs models locally without API costs
"""
from typing import Dict, List, Any, Optional
import structlog
import numpy as np
from transformers import (
    AutoTokenizer,
    AutoModel,
    AutoModelForCausalLM,
    pipeline,
    BitsAndBytesConfig,
)
from sentence_transformers import SentenceTransformer
import torch

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache, get_cache_key

logger = structlog.get_logger()


class HuggingFaceService:
    """Hugging Face service for local AI inference"""
    
    def __init__(self):
        # Force GPU if available, regardless of settings
        if torch.cuda.is_available():
            self.device = "cuda"
            logger.info("using_gpu", device=torch.cuda.get_device_name(0))
        else:
            self.device = "cpu"
            logger.warning("gpu_not_available_using_cpu")
        
        # Initialize embedding model
        self.embedding_model = None
        self._init_embedding_model()
        
        # Initialize text generation model (lazy loading)
        self.text_generator = None
        self.text_tokenizer = None
    
    def _init_embedding_model(self):
        """Initialize embedding model"""
        try:
            model_name = settings.HUGGINGFACE_EMBEDDING_MODEL
            logger.info("loading_embedding_model", model=model_name)
            self.embedding_model = SentenceTransformer(model_name, device=self.device)
            logger.info("embedding_model_loaded", model=model_name)
        except Exception as e:
            logger.error("embedding_model_init_failed", error=str(e))
            # Fallback to default
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
            except Exception as e2:
                logger.error("fallback_embedding_model_failed", error=str(e2))
    
    def _init_text_generator(self):
        """Lazy load text generation model"""
        if self.text_generator is not None:
            return
        
        try:
            model_name = settings.HUGGINGFACE_LLM_MODEL
            logger.info("loading_text_generator", model=model_name)
            
            # Use smaller model for CPU, larger for GPU
            if self.device == "cpu":
                # Use a smaller, faster model for CPU
                model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            
            # Load tokenizer
            self.text_tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self.text_tokenizer.pad_token is None:
                self.text_tokenizer.pad_token = self.text_tokenizer.eos_token
            
            # Load model with quantization for CPU
            if self.device == "cpu":
                # Use 8-bit quantization to reduce memory
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_threshold=6.0,
                ) if hasattr(BitsAndBytesConfig, 'load_in_8bit') else None
            else:
                quantization_config = None
            
            # Load model
            self.text_generator = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                quantization_config=quantization_config,
                low_cpu_mem_usage=True,
            )
            
            if self.device == "cpu":
                self.text_generator = self.text_generator.to(self.device)
            
            logger.info("text_generator_loaded", model=model_name, device=self.device)
        except Exception as e:
            logger.error("text_generator_init_failed", error=str(e))
            # Use pipeline as fallback
            try:
                model_name = "gpt2"  # Very small fallback
                self.text_generator = pipeline(
                    "text-generation",
                    model=model_name,
                    device=0 if self.device == "cuda" else -1,
                )
                logger.info("using_pipeline_fallback", model=model_name)
            except Exception as e2:
                logger.error("pipeline_fallback_failed", error=str(e2))
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Hugging Face model"""
        cache_key = get_cache_key("embedding_hf", text[:100])
        cached = get_cache(cache_key)
        if cached:
            return cached
        
        try:
            if self.embedding_model is None:
                self._init_embedding_model()
            
            if self.embedding_model:
                # Generate embedding
                embedding = self.embedding_model.encode(text, convert_to_numpy=True)
                embedding_list = embedding.tolist()
                
                set_cache(cache_key, embedding_list, ttl=settings.REDIS_CACHE_TTL * 24)
                return embedding_list
            else:
                logger.warning("no_embedding_model_available")
                return [0.0] * 384
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            return [0.0] * 384
    
    def generate_text(
        self,
        prompt: str,
        max_length: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Hugging Face model"""
        try:
            self._init_text_generator()
            
            if self.text_generator is None:
                logger.warning("text_generator_not_available")
                return ""
            
            # Prepare prompt
            if isinstance(self.text_generator, pipeline):
                # Use pipeline
                result = self.text_generator(
                    prompt,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    num_return_sequences=1,
                )
                return result[0]['generated_text']
            else:
                # Use model directly
                inputs = self.text_tokenizer(prompt, return_tensors="pt").to(self.device)
                
                with torch.no_grad():
                    outputs = self.text_generator.generate(
                        **inputs,
                        max_new_tokens=max_length,
                        temperature=temperature,
                        do_sample=True,
                        pad_token_id=self.text_tokenizer.eos_token_id,
                    )
                
                generated_text = self.text_tokenizer.decode(outputs[0], skip_special_tokens=True)
                # Remove the prompt from output
                if generated_text.startswith(prompt):
                    generated_text = generated_text[len(prompt):].strip()
                
                return generated_text
        except Exception as e:
            logger.error("text_generation_failed", error=str(e))
            return ""
    
    def generate_explanation(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Generate explanation using Hugging Face model"""
        try:
            # Build prompt
            prompt = self._build_explanation_prompt(candidate_data, job_data, scores)
            
            # Generate explanation
            explanation_text = self.generate_text(
                prompt,
                max_length=800,
                temperature=0.7,
            )
            
            # Parse explanation
            return self._parse_explanation(explanation_text, candidate_data, job_data, scores)
        except Exception as e:
            logger.error("explanation_generation_failed", error=str(e))
            return self._fallback_explanation(candidate_data, job_data, scores)
    
    def _build_explanation_prompt(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        scores: Dict[str, float],
    ) -> str:
        """Build prompt for explanation"""
        candidate_skills = candidate_data.get("skills", [])
        job_required = job_data.get("required_skills", [])
        job_nice_to_have = job_data.get("nice_to_have_skills", [])
        
        prompt = f"""Analyze this candidate-job match:

JOB: {job_data.get('title', 'N/A')} at {job_data.get('company', 'N/A')}
Required Skills: {', '.join(job_required[:10])}
Nice-to-Have: {', '.join(job_nice_to_have[:10])}
Experience Required: {job_data.get('experience_years_required', 'N/A')} years

CANDIDATE:
Skills: {', '.join(candidate_skills[:20])}
Experience: {candidate_data.get('experience_years', 'N/A')} years

SCORES:
Overall: {scores.get('overall_score', 0):.1f}/100
Skill Match: {scores.get('skill_match_score', 0):.1f}/100
Experience: {scores.get('experience_score', 0):.1f}/100

Provide a brief analysis with:
1. Summary (2-3 sentences)
2. Key strengths (3-5 points)
3. Gaps/weaknesses (3-5 points)
4. Recommendations (2-3 items)

Analysis:"""
        return prompt
    
    def _parse_explanation(
        self,
        explanation_text: str,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Parse explanation into structured format"""
        # Simple parsing - extract sections
        lines = explanation_text.split('\n')
        summary = ""
        strengths = []
        weaknesses = []
        recommendations = []
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            if 'summary' in line_lower or 'overall' in line_lower:
                current_section = 'summary'
                continue
            elif 'strength' in line_lower or 'strong' in line_lower:
                current_section = 'strengths'
                continue
            elif 'weakness' in line_lower or 'gap' in line_lower or 'missing' in line_lower:
                current_section = 'weaknesses'
                continue
            elif 'recommendation' in line_lower or 'suggest' in line_lower:
                current_section = 'recommendations'
                continue
            
            if current_section == 'summary':
                summary += line + " "
            elif current_section == 'strengths' and (line.startswith('-') or line.startswith('•') or len(strengths) < 5):
                strengths.append(line.lstrip('-•').strip())
            elif current_section == 'weaknesses' and (line.startswith('-') or line.startswith('•') or len(weaknesses) < 5):
                weaknesses.append(line.lstrip('-•').strip())
            elif current_section == 'recommendations' and (line.startswith('-') or line.startswith('•') or len(recommendations) < 3):
                recommendations.append(line.lstrip('-•').strip())
        
        # Fallback if parsing didn't work well
        if not summary:
            summary = explanation_text[:300]
        if not strengths and not weaknesses:
            # Use fallback
            return self._fallback_explanation(candidate_data, job_data, scores)
        
        return {
            "summary": summary.strip() or explanation_text[:200],
            "strengths": strengths[:5] if strengths else [],
            "weaknesses": weaknesses[:5] if weaknesses else [],
            "recommendations": recommendations[:3] if recommendations else [],
            "confidence_score": scores.get("overall_score", 0) / 100,
            "reasoning_quality": "medium",
        }
    
    def _fallback_explanation(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Fallback explanation when model fails"""
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
            "reasoning_quality": "medium",
        }

