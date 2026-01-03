"""
Candidate Kundali Parser - Masterpiece Architecture v2.0

Resume-as-Source-of-Truth: Image-First Extraction using Qwen Vision
Extracts structured data + behavioral signals + personality inference
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import re
import structlog
import requests
from PIL import Image
import io
import base64

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache, get_cache_key

logger = structlog.get_logger()

# Ollama configuration
OLLAMA_ENDPOINT = "http://host.docker.internal:11434"  # WSL/Docker access
# Vision model names to try (Ollama model names may vary)
OLLAMA_VISION_MODELS = [
    "qwen2-vl:7b",  # Common Qwen2-VL name
    "qwen2-vl:7b-instruct",  # Alternative
    "qwen2.5-vl:7b-instruct-q4_K_M",  # Original attempt
    "qwen-vl:7b",  # Older version
]
OLLAMA_MODEL = "qwen2.5:7b-instruct-q4_K_M"  # Text-only (confirmed available)
OLLAMA_FALLBACK_MODEL = "qwen2.5:7b-instruct-q4_K_M"  # Text-only fallback


class CandidateKundaliParser:
    """
    Masterpiece Resume Parser using Qwen Vision Model
    
    Philosophy:
    - Resume is the ONLY input (no manual forms)
    - Image-first extraction (preserves layout, design)
    - Structured + behavioral extraction
    - Personality inference with confidence scores
    - Anti-hallucination (unknown > fake data)
    """
    
    def __init__(self):
        self.ollama_endpoint = OLLAMA_ENDPOINT
        self.fallback_model = OLLAMA_FALLBACK_MODEL
        
        # Check Ollama availability and find vision model
        self.ollama_available = self._check_ollama_availability()
        self.vision_model = self._find_available_vision_model() if self.ollama_available else None
        self.use_vision = self.vision_model is not None
        
        logger.info("kundali_parser_initialized", 
                   ollama_available=self.ollama_available,
                   vision_model=self.vision_model,
                   use_vision=self.use_vision)
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning("ollama_not_available", error=str(e))
            return False
    
    def _find_available_vision_model(self) -> Optional[str]:
        """Find available vision model from list of possible names"""
        try:
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                # Try each vision model name
                for vision_model in OLLAMA_VISION_MODELS:
                    if any(vision_model in name or name.startswith(vision_model.split(":")[0]) for name in model_names):
                        # Check if it's actually a vision model (contains 'vl' or 'vision')
                        matching_models = [name for name in model_names if vision_model.split(":")[0] in name.lower() and ('vl' in name.lower() or 'vision' in name.lower())]
                        if matching_models:
                            logger.info("vision_model_found", model=matching_models[0])
                            return matching_models[0]
                
                logger.warning("no_vision_model_found", available_models=model_names)
                return None
        except Exception as e:
            logger.warning("error_finding_vision_model", error=str(e))
            return None
    
    def parse_resume(self, pdf_path: str, text_from_pdf: Optional[str] = None) -> Dict[str, Any]:
        """
        Main parsing method: PDF → Direct to Qwen → Candidate Kundali
        
        Args:
            pdf_path: Path to PDF file
            text_from_pdf: Optional extracted text (not used, kept for compatibility)
        
        Returns:
            Candidate Kundali (structured JSON with confidence scores)
        """
        logger.info("kundali_parsing_started", pdf_path=pdf_path)
        
        try:
            # Step 1: Read PDF file directly (no conversion, no text extraction)
            pdf_data = self._read_pdf_file(pdf_path)
            if not pdf_data:
                logger.error("failed_to_read_pdf", pdf_path=pdf_path)
                return self._empty_kundali()
            
            logger.info("pdf_file_read", pdf_path=pdf_path, size_bytes=len(pdf_data))
            
            # Step 2: Extract using Qwen with PDF directly
            if self.ollama_available:
                try:
                    # Try vision model first if available
                    if self.use_vision and self.vision_model:
                        kundali = self._extract_with_pdf_direct(pdf_data, pdf_path)
                    else:
                        # Use text-only model with PDF
                        kundali = self._extract_with_pdf_direct(pdf_data, pdf_path, use_text_model=True)
                except Exception as e:
                    logger.error("pdf_extraction_failed", error=str(e), exc_info=True)
                    return self._empty_kundali()
            else:
                logger.error("ollama_not_available")
                return self._empty_kundali()
            
            # Step 3: Post-process and validate
            kundali = self._post_process_kundali(kundali)
            
            logger.info("kundali_parsing_complete", 
                       has_identity=bool(kundali.get("candidate_kundali", {}).get("identity", {}).get("name")),
                       experience_count=len(kundali.get("candidate_kundali", {}).get("experience", [])),
                       confidence=kundali.get("candidate_kundali", {}).get("overall_confidence_score", 0.0))
            
            return kundali
            
        except Exception as e:
            logger.error("kundali_parsing_failed", error=str(e), exc_info=True)
            return self._empty_kundali()
    
    def _read_pdf_file(self, pdf_path: str) -> Optional[bytes]:
        """Read PDF file directly as binary (no conversion)"""
        try:
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            return pdf_data
        except Exception as e:
            logger.error("failed_to_read_pdf_file", error=str(e), pdf_path=pdf_path)
            return None
    
    def _extract_with_pdf_direct(self, pdf_data: bytes, pdf_path: str, use_text_model: bool = False) -> Dict[str, Any]:
        """
        Extract Candidate Kundali using Qwen with PDF file directly (no conversion)
        
        Args:
            pdf_data: PDF file as bytes
            pdf_path: Path to PDF file (for logging)
            use_text_model: If True, use text-only model (fallback)
        
        Returns:
            Candidate Kundali dictionary
        """
        try:
            # Convert PDF to base64
            pdf_base64 = base64.b64encode(pdf_data).decode()
            
            # Build master prompt
            prompt = self._build_master_prompt()
            
            # Determine which model to use
            model_to_use = self.fallback_model if use_text_model else (self.vision_model or self.fallback_model)
            
            # Prepare messages - PDF as document/file
            # Ollama API format: PDF can be sent as base64 in messages
            # For vision models, we can send PDF directly
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [pdf_base64] if not use_text_model else None  # PDF as base64 for vision models
                }
            ]
            
            # Remove None values
            messages[0] = {k: v for k, v in messages[0].items() if v is not None}
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_endpoint}/api/chat",
                json={
                    "model": model_to_use,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for structured output
                        "num_predict": 4096  # Enough for full kundali
                    }
                },
                timeout=300.0  # 5 minutes for PDF processing
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("message", {}).get("content", "")
                
                # Extract JSON from response
                kundali_json = self._extract_json_from_response(generated_text)
                
                # Parse and validate
                kundali = json.loads(kundali_json)
                
                logger.info("qwen_pdf_extraction_successful", 
                           model=model_to_use,
                           response_length=len(generated_text))
                return kundali
            else:
                logger.error("ollama_pdf_api_error", 
                           status_code=response.status_code,
                           response_text=response.text[:200])
                return self._empty_kundali()
                
        except json.JSONDecodeError as e:
            logger.error("failed_to_parse_kundali_json", error=str(e))
            return self._empty_kundali()
        except Exception as e:
            logger.error("qwen_pdf_extraction_failed", error=str(e), exc_info=True)
            return self._empty_kundali()
    
    def _build_master_prompt(self) -> str:
        """
        Build the MASTER EXTRACTION PROMPT for Qwen
        
        This is the heart of the system - extracts facts + infers patterns + builds personality
        """
        prompt = """You are an expert resume parser for HireLens AI, a production-grade hiring intelligence platform.

CRITICAL CONSTRAINTS:
- Extract ONLY what is visible in the resume PDF document
- If data is missing → return "unknown" (NEVER invent)
- Personality traits MUST have confidence scores (0.0-1.0)
- Evidence-based inference only (back claims with resume content)

TASK:
Analyze the resume PDF document and extract a complete Candidate Kundali (360° profile).

OUTPUT FORMAT (STRICT JSON):
{{
  "candidate_kundali": {{
    "identity": {{
      "name": "string (extract from header)",
      "email": "string (extract, validate format)",
      "phone": "string (extract, normalize)",
      "location": "string (city, country if visible)"
    }},
    "online_presence": {{
      "portfolio": ["array of portfolio/personal website URLs"],
      "github": ["array of GitHub profile URLs"],
      "linkedin": ["array of LinkedIn profile URLs"],
      "other_links": ["array of other URLs: Twitter, Kaggle, Medium, Behance, etc."]
    }},
    "summary": "string (professional summary/profile if present)",
    "total_experience_years": number (calculated from experience dates),
    "education": [
      {{
        "degree": "string",
        "field": "string (major/specialization)",
        "institution": "string",
        "timeline": "string (e.g., '2019-2021' or '2015-2018')"
      }}
    ],
    "experience": [
      {{
        "company": "string",
        "role": "string (job title)",
        "start_date": "string (YYYY-MM format)",
        "end_date": "string ('present' if current, else YYYY-MM)",
        "is_current": boolean,
        "responsibilities": ["array of responsibility bullets"],
        "technologies_used": ["array of technologies mentioned"],
        "quantified_impact": ["array of metrics/numbers/percentages mentioned"],
        "promotions": ["array of role changes within same company if visible"]
      }}
    ],
    "projects": [
      {{
        "name": "string",
        "is_personal": boolean (true if personal/side project),
        "tech_stack": ["array of technologies"],
        "scope": "string (description of complexity/scale)",
        "ownership_indicators": ["array of signals showing ownership: 'built from scratch', 'solo project', etc."]
      }}
    ],
    "skills": {{
      "frontend": ["array of frontend technologies"],
      "backend": ["array of backend technologies"],
      "data": ["array of data technologies: SQL, NoSQL, etc."],
      "devops": ["array of DevOps tools"],
      "ai_ml": ["array of AI/ML technologies"],
      "tools": ["array of development tools"],
      "soft_skills": ["array of soft skills mentioned: communication, leadership, etc."]
    }},
    "certifications": [
      {{
        "name": "string",
        "issuer": "string",
        "year": "string (if visible)"
      }}
    ],
    "languages": ["array of spoken languages"],
    "seniority_assessment": {{
      "level": "junior|mid|senior|staff|principal",
      "confidence": number (0.0-1.0),
      "evidence": ["array of evidence: years of experience, leadership roles, etc."]
    }},
    "personality_inference": {{
      "work_style": "individual_contributor|leader|hybrid",
      "ownership_level": "low|medium|high",
      "learning_orientation": "low|medium|high",
      "communication_strength": "low|medium|high",
      "risk_profile": "conservative|balanced|experimental",
      "confidence": number (0.0-1.0)
    }},
    "leadership_signals": ["array of evidence: 'led team of X', 'managed projects', etc."],
    "red_flags": ["array of concerns: gaps, inconsistencies, etc. (be honest)"],
    "overall_confidence_score": number (0.0-1.0, based on data completeness and clarity)
  }}
}}

EXTRACTION RULES:
1. ONLINE PRESENCE: Extract ALL URLs found (GitHub, LinkedIn, portfolio, Twitter, etc.)
2. EXPERIENCE: Extract technologies mentioned, metrics (numbers, %), impact statements
3. PROJECTS: Distinguish personal vs company projects (look for "personal project", "side project", GitHub links)
4. SKILLS: Categorize properly (Frontend: React, Angular, etc. | Backend: Django, Node.js, etc.)
5. SENIORITY: Base on years of experience, role titles, leadership indicators
6. PERSONALITY: Infer from resume structure, use of metrics, project ownership, communication clarity
7. RED FLAGS: Be honest about gaps, inconsistencies, missing information

ANTI-HALLUCINATION:
- If email not visible → "unknown"
- If dates unclear → "unknown"
- If company name unclear → "unknown"
- NEVER invent companies, roles, or links
- Personality inference MUST have confidence < 0.7 if evidence is weak

QUALITY PRINCIPLES:
- Prefer fewer, correct fields over noisy output
- Conservative personality inference (low confidence if uncertain)
- Evidence-based seniority (back with years, roles, responsibilities)
- Honest red flags (missing info, gaps, inconsistencies)

Return ONLY valid JSON. No explanations, no markdown, just JSON.
"""
        return prompt
    
    def _parse_text_only(self, text: str) -> Dict[str, Any]:
        """Fallback: Parse text-only using Qwen (no vision)"""
        try:
            prompt = self._build_master_prompt(text)
            
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={
                    "model": self.fallback_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 4096
                    }
                },
                timeout=120.0
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                kundali_json = self._extract_json_from_response(generated_text)
                kundali = json.loads(kundali_json)
                return kundali
            else:
                return self._empty_kundali()
        except Exception as e:
            logger.error("text_only_parsing_failed", error=str(e))
            return self._empty_kundali()
    
    def _extract_json_from_response(self, text: str) -> str:
        """Extract JSON from model response"""
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return '{"candidate_kundali": {}}'
    
    def _post_process_kundali(self, kundali: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process and validate Kundali data"""
        kundali_data = kundali.get("candidate_kundali", {})
        
        # Ensure all required fields exist
        if "identity" not in kundali_data:
            kundali_data["identity"] = {}
        if "online_presence" not in kundali_data:
            kundali_data["online_presence"] = {}
        if "skills" not in kundali_data:
            kundali_data["skills"] = {}
        
        # Normalize online presence
        online_presence = kundali_data.get("online_presence", {})
        if not isinstance(online_presence, dict):
            kundali_data["online_presence"] = {"portfolio": [], "github": [], "linkedin": [], "other_links": []}
        
        # Ensure skills structure
        skills = kundali_data.get("skills", {})
        if not isinstance(skills, dict):
            kundali_data["skills"] = {
                "frontend": [],
                "backend": [],
                "data": [],
                "devops": [],
                "ai_ml": [],
                "tools": [],
                "soft_skills": []
            }
        
        # Calculate total experience years if missing
        if "total_experience_years" not in kundali_data or not kundali_data["total_experience_years"]:
            kundali_data["total_experience_years"] = self._calculate_experience_years(
                kundali_data.get("experience", [])
            )
        
        # Ensure confidence scores exist
        if "overall_confidence_score" not in kundali_data:
            kundali_data["overall_confidence_score"] = self._calculate_confidence(kundali_data)
        
        kundali["candidate_kundali"] = kundali_data
        return kundali
    
    def _calculate_experience_years(self, experience: List[Dict[str, Any]]) -> float:
        """Calculate total years of experience from experience entries"""
        if not experience:
            return 0.0
        
        # Simple calculation: sum of (end_date - start_date) for each entry
        total_years = 0.0
        for exp in experience:
            start = exp.get("start_date", "")
            end = exp.get("end_date", "")
            
            if not start:
                continue
            
            try:
                start_year = int(start.split("-")[0])
                if end and end.lower() not in ["present", "current", "now"]:
                    end_year = int(end.split("-")[0])
                else:
                    from datetime import datetime
                    end_year = datetime.now().year
                
                years = end_year - start_year
                if years > 0:
                    total_years += years
            except:
                continue
        
        return round(total_years, 1)
    
    def _calculate_confidence(self, kundali_data: Dict[str, Any]) -> float:
        """Calculate overall confidence score based on data completeness"""
        score = 0.0
        max_score = 10.0
        
        # Identity (2 points)
        identity = kundali_data.get("identity", {})
        if identity.get("name") and identity.get("name") != "unknown":
            score += 0.5
        if identity.get("email") and identity.get("email") != "unknown":
            score += 0.5
        if identity.get("phone") and identity.get("phone") != "unknown":
            score += 0.5
        if identity.get("location") and identity.get("location") != "unknown":
            score += 0.5
        
        # Experience (3 points)
        experience = kundali_data.get("experience", [])
        if experience:
            score += min(3.0, len(experience) * 0.5)
        
        # Education (1 point)
        education = kundali_data.get("education", [])
        if education:
            score += min(1.0, len(education) * 0.5)
        
        # Skills (2 points)
        skills = kundali_data.get("skills", {})
        total_skills = sum(len(v) if isinstance(v, list) else 0 for v in skills.values())
        if total_skills > 0:
            score += min(2.0, total_skills * 0.1)
        
        # Projects (1 point)
        projects = kundali_data.get("projects", [])
        if projects:
            score += min(1.0, len(projects) * 0.3)
        
        # Personality inference (1 point)
        personality = kundali_data.get("personality_inference", {})
        if personality.get("confidence", 0) > 0.5:
            score += 1.0
        
        return round(score / max_score, 2)
    
    def _empty_kundali(self) -> Dict[str, Any]:
        """Return empty Kundali structure"""
        return {
            "candidate_kundali": {
                "identity": {
                    "name": "unknown",
                    "email": "unknown",
                    "phone": "unknown",
                    "location": "unknown"
                },
                "online_presence": {
                    "portfolio": [],
                    "github": [],
                    "linkedin": [],
                    "other_links": []
                },
                "summary": "",
                "total_experience_years": 0,
                "education": [],
                "experience": [],
                "projects": [],
                "skills": {
                    "frontend": [],
                    "backend": [],
                    "data": [],
                    "devops": [],
                    "ai_ml": [],
                    "tools": [],
                    "soft_skills": []
                },
                "certifications": [],
                "languages": [],
                "seniority_assessment": {
                    "level": "unknown",
                    "confidence": 0.0,
                    "evidence": []
                },
                "personality_inference": {
                    "work_style": "unknown",
                    "ownership_level": "unknown",
                    "learning_orientation": "unknown",
                    "communication_strength": "unknown",
                    "risk_profile": "unknown",
                    "confidence": 0.0
                },
                "leadership_signals": [],
                "red_flags": [],
                "overall_confidence_score": 0.0
            }
        }


# Global instance
kundali_parser = CandidateKundaliParser()

