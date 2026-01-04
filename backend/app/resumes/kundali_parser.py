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
            text_from_pdf: Optional extracted text (used for text-only models)
        
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
            
            # Step 2: Extract using Qwen
            if self.ollama_available:
                try:
                    # Try vision model first if available
                    if self.use_vision and self.vision_model:
                        kundali = self._extract_with_pdf_direct(pdf_data, pdf_path)
                    else:
                        # Use text-only model with extracted text (better than PDF base64)
                        if text_from_pdf:
                            logger.info("using_extracted_text_for_text_model", text_length=len(text_from_pdf))
                            kundali = self._extract_with_text(text_from_pdf)
                        else:
                            # Fallback: try PDF base64 (may not work well)
                            logger.warning("no_extracted_text_available_using_pdf_base64")
                            kundali = self._extract_with_pdf_direct(pdf_data, pdf_path, use_text_model=True)
                except Exception as e:
                    logger.error("pdf_extraction_failed", error=str(e), exc_info=True)
                    return self._empty_kundali()
            else:
                logger.error("ollama_not_available")
                # Even if Ollama is not available, try to extract basic info from text
                kundali = self._empty_kundali()
            
            # Step 3: Post-process and validate (with text-based fallback enhancement)
            kundali = self._post_process_kundali(kundali, text_from_pdf=text_from_pdf)
            
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

CRITICAL CONSTRAINTS - READ CAREFULLY:
- Extract ONLY what is VISIBLE in the resume PDF document - NOTHING ELSE
- If data is missing → return "unknown" (NEVER invent, NEVER guess, NEVER assume)
- NEVER invent company names, job titles, or roles that are not explicitly written
- NEVER create fake experience entries - only extract what is actually listed
- If you see "Deloitte" → extract "Deloitte", NOT "Tech Innovations Inc."
- If you see "Full-Stack Developer" → extract "Full-Stack Developer", NOT "Software Engineer"
- Extract ALL experience entries listed - don't combine or merge them
- Extract ALL skills mentioned - don't skip any
- Personality traits MUST have confidence scores (0.0-1.0)
- Evidence-based inference only (back claims with resume content)
- If uncertain about ANY field → use "unknown" instead of guessing

TASK:
Analyze the resume PDF document and extract a complete Candidate Kundali (360° profile).

OUTPUT FORMAT (STRICT JSON):
{{
  "candidate_kundali": {{
    "identity": {{
      "name": "string (FULL name from header: first name + last name, e.g., 'John Doe' or 'Aleks Ludkee')",
      "email": "string (extract email address, validate format like user@domain.com)",
      "phone": "string (extract phone number, normalize format like (123) 456-7890 or +1-123-456-7890)",
      "location": "string (city, state/country if visible, e.g., 'Nashville, TN' or 'Bangalore, India')"
    }},
    "online_presence": {{
      "portfolio": ["array of portfolio/personal website URLs - extract ALL portfolio links found"],
      "github": ["array of GitHub profile URLs - extract ALL GitHub links (github.com/username)"],
      "linkedin": ["array of LinkedIn profile URLs - extract ALL LinkedIn links (linkedin.com/in/username)"],
      "other_links": ["array of ALL other URLs found: Twitter, Kaggle, Medium, Behance, Stack Overflow, personal websites, etc. - include full URLs with https://"]
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
        "company": "string (EXACT company name as written, e.g., 'Deloitte' or 'Randstad Technologies')",
        "role": "string (EXACT job title as written, e.g., 'Full-Stack Developer' or 'Jr. Full-Stack Developer')",
        "start_date": "string (YYYY-MM format, extract from dates like 'August 2020' → '2020-08')",
        "end_date": "string ('present' if current, else YYYY-MM format)",
        "is_current": boolean (true if end date is 'present', 'current', or 'now'),
        "responsibilities": ["array of ALL responsibility bullets for this role"],
        "technologies_used": ["array of technologies mentioned in this role"],
        "quantified_impact": ["array of metrics/numbers/percentages mentioned"],
        "promotions": ["array of role changes within same company if visible"]
      }}
    ],
    NOTE: Include ALL experience entries found. If resume has 2 jobs, return 2 entries. If resume has 3 jobs, return 3 entries. DO NOT combine or merge them.
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
      "frontend": ["array of ALL frontend technologies mentioned: JavaScript, HTML, CSS, React.js, Angular.js, Vue.js, etc."],
      "backend": ["array of ALL backend technologies mentioned: Node.js, .NET, Spring, Express, Django, etc."],
      "data": ["array of ALL data technologies mentioned: SQL, NoSQL, MongoDB, MySQL, PostgreSQL, etc."],
      "devops": ["array of ALL DevOps tools mentioned: Docker, Kubernetes, Git, CI/CD, etc."],
      "ai_ml": ["array of AI/ML technologies if mentioned"],
      "tools": ["array of ALL development tools mentioned: Git, Jira, Webpack, etc."],
      "soft_skills": ["array of soft skills mentioned: Scrum/Agile, communication, leadership, etc."]
    }},
    NOTE: Extract EVERY skill mentioned in the Skills section. Common skills include: JavaScript, HTML, CSS, .NET, React.js, Angular.js, Node.js, REST APIs, Spring, SOAP, Scrum/Agile. DO NOT skip any skills.
    "certifications": [
      {{
        "name": "string (EXACT certification name as written, e.g., 'MTA' or 'AWS')",
        "issuer": "string (if visible, otherwise null)",
        "year": "string (if visible, otherwise null)"
      }}
    ],
    NOTE: Extract ALL certifications mentioned. Common formats: "MTA", "AWS", "Certified XYZ". Extract exactly as written.
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

EXTRACTION RULES - FOLLOW STRICTLY:

1. IDENTITY: Extract FULL name (exactly as written), email, phone number, and location/address from header section

2. ONLINE PRESENCE: Extract ALL URLs found anywhere in resume:
   - LinkedIn: linkedin.com/in/* or linkedin.com/profile/*
   - GitHub: github.com/* 
   - Portfolio: personal websites, portfolios, blogs
   - Other: Twitter, Kaggle, Medium, Behance, Stack Overflow, etc.
   - Include full URLs (with https:// if visible, otherwise add it)

3. EXPERIENCE - CRITICAL: Extract EVERY experience entry listed:
   - Look for ALL work experience sections
   - Each job/role is a SEPARATE entry in the array
   - Extract company name EXACTLY as written (e.g., "Deloitte" not "Tech Innovations")
   - Extract job title EXACTLY as written (e.g., "Full-Stack Developer" not "Software Engineer")
   - Extract dates EXACTLY as shown (e.g., "August 2020 - current" or "June 2019 - August 2020")
   - Extract ALL responsibilities/bullet points for each role
   - Extract technologies mentioned in each role
   - DO NOT combine multiple jobs into one entry
   - DO NOT invent companies or roles that are not visible
   - If you see "Deloitte" → use "Deloitte", if you see "Randstad Technologies" → use "Randstad Technologies"

4. PROJECTS: Distinguish personal vs company projects (look for "personal project", "side project", GitHub links)

5. SKILLS - EXTRACT ALL MENTIONED (BUT EXCLUDE COMPANY NAMES):
   - Look for a Skills section in the resume
   - Extract EVERY skill/technology mentioned
   - Common skills: JavaScript, HTML, CSS, .NET, React.js, Angular.js, Node.js, REST APIs, Spring, SOAP, Scrum/Agile
   - Categorize properly:
     * Frontend: React, Angular, HTML, CSS, JavaScript, Vue.js, etc.
     * Backend: Node.js, .NET, Spring, Express, Django, etc.
     * Data: SQL, NoSQL, MongoDB, MySQL, etc.
     * DevOps: Docker, Kubernetes, Git, CI/CD, etc.
     * Tools: Git, Jira, Webpack, etc.
   - CRITICAL: DO NOT include company names in skills (e.g., "Deloitte", "Kanishka Software Pvt Ltd", "Team 4 Progress Technologies" are COMPANIES, not skills)
   - DO NOT skip skills - extract ALL of them
   - If you see "JavaScript" → include it, if you see "HTML" → include it, if you see ".NET" → include it
   - Company names belong in experience.company field, NOT in skills arrays

6. CERTIFICATIONS - EXTRACT ALL:
   - Look for Certifications section
   - Extract ALL certifications mentioned (e.g., "MTA", "AWS")
   - Extract issuer if visible, year if visible
   - DO NOT invent certifications

7. EDUCATION: Extract degree, field, institution, and dates EXACTLY as written

8. SENIORITY: Base on years of experience, role titles, leadership indicators

9. PERSONALITY: Infer from resume structure, use of metrics, project ownership, communication clarity

10. RED FLAGS: Be honest about gaps, inconsistencies, missing information

ANTI-HALLUCINATION - STRICT RULES:
- If email not visible → "unknown" (NEVER invent like "john@example.com")
- If dates unclear → "unknown" (NEVER guess dates)
- If company name unclear → "unknown" (NEVER invent company names like "Tech Innovations Inc.")
- If job title unclear → "unknown" (NEVER invent titles like "Software Engineer")
- NEVER invent companies, roles, skills, or links
- NEVER create experience entries that don't exist in the resume
- NEVER combine multiple jobs into one entry
- NEVER skip experience entries - extract ALL of them
- NEVER skip skills - extract ALL mentioned skills
- If you see "Deloitte" in resume → extract "Deloitte" (not "Tech Innovations")
- If you see "Randstad Technologies" → extract "Randstad Technologies" (not something else)
- If you see "Full-Stack Developer" → extract "Full-Stack Developer" (not "Software Engineer")
- If you see "JavaScript, HTML, CSS" → extract ALL of them (don't skip any)
- Personality inference MUST have confidence < 0.7 if evidence is weak
- When in doubt → use "unknown" or empty array, NEVER invent data

CRITICAL EXTRACTION REQUIREMENTS - EXTRACT EVERYTHING VISIBLE:

1. NAME: 
   - Look at the TOP of the resume, usually in header section
   - Extract COMPLETE name (first name + last name)
   - Example: "ALEKS LUDKEE" → name: "Aleks Ludkee"
   - Example: "John Smith" → name: "John Smith"
   - If only first name visible → use that, but prefer full name

2. EMAIL:
   - Look for email addresses in header/contact section (usually at the top of resume)
   - Common patterns: user@domain.com, user.name@company.com, user_name@domain.co.uk
   - Email addresses contain @ symbol - scan for this pattern
   - Extract the COMPLETE email address exactly as shown (including dots, hyphens, etc.)
   - Example: "a.ludkee@email.com" → email: "a.ludkee@email.com"
   - Example: "john.doe@company.com" → email: "john.doe@company.com"
   - If email has icon next to it, still extract it
   - Email is usually on the same line as phone number or location
   - CRITICAL: If you see ANY text with @ symbol followed by domain, that's the email - extract it!
   - ONLY return "unknown" if NO email with @ symbol is visible anywhere in the entire document

3. PHONE:
   - Look for phone numbers in header/contact section
   - Common formats: (123) 456-7890, +1-123-456-7890, 123-456-7890
   - Extract phone number in ANY format found
   - Keep original format, don't change it unnecessarily
   - Example: "(123) 456-7890" → phone: "(123) 456-7890"
   - If phone has icon next to it, still extract it

4. LOCATION/ADDRESS:
   - Look for city, state, country in header/contact section
   - Extract location information
   - Example: "Nashville, TN" → location: "Nashville, TN"
   - Example: "Bangalore, India" → location: "Bangalore, India"

5. LINKS - EXTRACT ALL URLs FOUND:
   - SCAN THE ENTIRE RESUME for ANY URLs
   - LinkedIn: 
     * Look for "LinkedIn" text with URL
     * Look for linkedin.com/in/* or linkedin.com/profile/* patterns
     * Extract FULL URL (add https:// if missing)
     * Example: "LinkedIn: linkedin.com/in/aleksludkee" → "https://linkedin.com/in/aleksludkee"
   - GitHub:
     * Look for "Github" or "GitHub" text with URL
     * Look for github.com/* patterns
     * Extract FULL URL (add https:// if missing)
     * Example: "Github: github.com/aleksludkee" → "https://github.com/aleksludkee"
   - Portfolio/Personal Websites:
     * Look for personal website URLs
     * Look for portfolio links
     * Extract ALL portfolio/personal website URLs
   - Other Links:
     * Extract ALL other URLs found: Twitter, Kaggle, Medium, Behance, Stack Overflow, personal blogs, etc.
     * Don't miss any URLs - scan carefully
     * Always add https:// prefix if URL doesn't have http:// or https://
     * Store in other_links array

IMPORTANT: 
- Be THOROUGH - extract EVERY piece of contact information visible
- Don't skip links just because they're in different sections
- If you see "LinkedIn" or "Github" text, the URL is nearby - find it!
- URLs might be hyperlinked (clickable) - extract the actual URL, not just the text

QUALITY PRINCIPLES:
- Prefer fewer, correct fields over noisy output
- Conservative personality inference (low confidence if uncertain)
- Evidence-based seniority (back with years, roles, responsibilities)
- Honest red flags (missing info, gaps, inconsistencies)

Return ONLY valid JSON. No explanations, no markdown, just JSON.
"""
        return prompt
    
    def _extract_with_text(self, text: str) -> Dict[str, Any]:
        """Extract using text-only model with extracted text (better than PDF base64)"""
        try:
            prompt = self._build_master_prompt()
            # Add the extracted text to the prompt
            full_prompt = f"{prompt}\n\nRESUME TEXT CONTENT:\n{text}\n\nNow extract the Candidate Kundali from the above resume text."
            
            response = requests.post(
                f"{self.ollama_endpoint}/api/chat",
                json={
                    "model": self.fallback_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for structured output
                        "num_predict": 4096  # Enough for full kundali
                    }
                },
                timeout=300.0
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("message", {}).get("content", "")
                kundali_json = self._extract_json_from_response(generated_text)
                kundali = json.loads(kundali_json)
                
                logger.info("qwen_text_extraction_successful", 
                           model=self.fallback_model,
                           response_length=len(generated_text))
                return kundali
            else:
                logger.error("ollama_text_api_error", 
                           status_code=response.status_code,
                           response_text=response.text[:200])
                return self._empty_kundali()
        except json.JSONDecodeError as e:
            logger.error("failed_to_parse_kundali_json", error=str(e))
            return self._empty_kundali()
        except Exception as e:
            logger.error("text_extraction_failed", error=str(e), exc_info=True)
            return self._empty_kundali()
    
    def _parse_text_only(self, text: str) -> Dict[str, Any]:
        """Fallback: Parse text-only using Qwen (no vision) - deprecated, use _extract_with_text instead"""
        return self._extract_with_text(text)
    
    def _extract_json_from_response(self, text: str) -> str:
        """Extract JSON from model response"""
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return '{"candidate_kundali": {}}'
    
    def _post_process_kundali(self, kundali: Dict[str, Any], text_from_pdf: Optional[str] = None) -> Dict[str, Any]:
        """Post-process and validate Kundali data, with text-based fallback enhancement"""
        kundali_data = kundali.get("candidate_kundali", {})
        
        # Ensure all required fields exist
        if "identity" not in kundali_data:
            kundali_data["identity"] = {}
        if "online_presence" not in kundali_data:
            kundali_data["online_presence"] = {}
        if "skills" not in kundali_data:
            kundali_data["skills"] = {}
        
        identity = kundali_data.get("identity", {})
        online_presence = kundali_data.get("online_presence", {})
        
        # TEXT-BASED FALLBACK ENHANCEMENT: If fields are missing/unknown, extract from text
        if text_from_pdf:
            # Enhance name extraction if missing
            if not identity.get("name") or identity.get("name") == "unknown":
                extracted_name = self._extract_name_from_text(text_from_pdf)
                if extracted_name and extracted_name != "unknown":
                    identity["name"] = extracted_name
                    logger.info("name_extracted_from_text_fallback", name=extracted_name)
            
            # Enhance email if missing (already done in tasks, but double-check)
            if not identity.get("email") or identity.get("email") == "unknown":
                from app.tasks.resume_tasks import _extract_email_from_text
                extracted_email = _extract_email_from_text(text_from_pdf)
                if extracted_email and extracted_email != "unknown":
                    identity["email"] = extracted_email
            
            # Enhance phone if missing (already done in tasks, but double-check)
            if not identity.get("phone") or identity.get("phone") == "unknown":
                from app.tasks.resume_tasks import _extract_phone_from_text
                extracted_phone = _extract_phone_from_text(text_from_pdf)
                if extracted_phone and extracted_phone != "unknown":
                    identity["phone"] = extracted_phone
            
            # Enhance URLs if missing
            if not isinstance(online_presence, dict):
                online_presence = {"portfolio": [], "github": [], "linkedin": [], "other_links": []}
            
            # Extract URLs from text if not found
            if not online_presence.get("linkedin") and not online_presence.get("github") and not online_presence.get("portfolio"):
                extracted_urls = self._extract_urls_from_text(text_from_pdf)
                if extracted_urls:
                    if not online_presence.get("linkedin"):
                        online_presence["linkedin"] = extracted_urls.get("linkedin", [])
                    if not online_presence.get("github"):
                        online_presence["github"] = extracted_urls.get("github", [])
                    if not online_presence.get("portfolio"):
                        online_presence["portfolio"] = extracted_urls.get("portfolio", [])
                    if not online_presence.get("other_links"):
                        online_presence["other_links"] = extracted_urls.get("other_links", [])
                    logger.info("urls_extracted_from_text_fallback", 
                               linkedin_count=len(online_presence.get("linkedin", [])),
                               github_count=len(online_presence.get("github", [])),
                               portfolio_count=len(online_presence.get("portfolio", [])))
        
        # Normalize online presence
        if not isinstance(online_presence, dict):
            kundali_data["online_presence"] = {"portfolio": [], "github": [], "linkedin": [], "other_links": []}
        else:
            kundali_data["online_presence"] = online_presence
        kundali_data["identity"] = identity
        
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
        
        # CLEAN SKILLS: Remove company names from skills arrays
        # Extract all company names from experience
        experience = kundali_data.get("experience", [])
        company_names = set()
        for exp_entry in experience:
            company = exp_entry.get("company", "")
            if company and company != "unknown":
                # Normalize: lowercase, remove common suffixes
                company_normalized = company.lower().strip()
                company_names.add(company_normalized)
                # Also add partial matches (e.g., "Kanishka Software" matches "Kanishka Software Pvt Ltd")
                words = company_normalized.split()
                if len(words) > 1:
                    # Add company without common suffixes
                    for suffix in ["pvt", "ltd", "inc", "llc", "corp", "corporation", "technologies", "tech", "software", "solutions", "services"]:
                        if words[-1] == suffix and len(words) > 1:
                            company_names.add(" ".join(words[:-1]))
                    # Add first word (e.g., "Kanishka" from "Kanishka Software Pvt Ltd")
                    if len(words) >= 2:
                        company_names.add(words[0])
        
        # Filter out company names from all skill categories
        skill_categories = ["frontend", "backend", "data", "devops", "ai_ml", "tools", "soft_skills"]
        cleaned_count = 0
        for category in skill_categories:
            if category in skills and isinstance(skills[category], list):
                original_count = len(skills[category])
                skills[category] = [
                    skill for skill in skills[category]
                    if skill and isinstance(skill, str) and not self._is_company_name(skill, company_names)
                ]
                cleaned_count += original_count - len(skills[category])
        
        if cleaned_count > 0:
            logger.info("cleaned_company_names_from_skills", 
                       removed_count=cleaned_count,
                       companies=list(company_names)[:5])  # Log first 5 companies
            kundali_data["skills"] = skills
        
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
    
    def _is_company_name(self, skill: str, company_names: set) -> bool:
        """Check if a skill string is actually a company name"""
        if not skill or not isinstance(skill, str):
            return False
        
        skill_lower = skill.lower().strip()
        
        # Direct match
        if skill_lower in company_names:
            return True
        
        # Partial match: check if skill contains or is contained in any company name
        for company in company_names:
            # Skill is part of company name (e.g., "Kanishka" in "Kanishka Software Pvt Ltd")
            if company and skill_lower in company:
                # But exclude very short matches (e.g., "Tech" is too generic)
                if len(skill_lower) >= 4:  # Only match if skill is at least 4 chars
                    return True
            # Company name is part of skill (e.g., "Kanishka Software Pvt Ltd" contains "Kanishka")
            if company and company in skill_lower:
                return True
        
        # Common company name patterns (extra safety check)
        company_patterns = [
            r'\b(pvt|ltd|inc|llc|corp|corporation)\b',
            r'\b(technologies|tech|software|solutions|services|systems|consulting)\s+\w+',
        ]
        import re
        for pattern in company_patterns:
            if re.search(pattern, skill_lower):
                # But allow if it's a legitimate technology name (e.g., "Tech Stack" is OK)
                if skill_lower not in ["tech stack", "stack", "backend", "frontend"]:
                    # Check if it matches a known company
                    for company in company_names:
                        if skill_lower in company or company in skill_lower:
                            return True
        
        return False
    
    def _extract_name_from_text(self, text: str) -> str:
        """Extract candidate name from resume text using heuristics"""
        if not text:
            return "unknown"
        
        # Strategy: Name is usually at the top, in large text, or after "RESUME" / before contact info
        lines = text.split('\n')
        
        # Look at first 10 lines (name is usually at the top)
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip common header patterns
            if any(skip in line.upper() for skip in ['RESUME', 'CV', 'CURRICULUM', 'PHONE', 'EMAIL', 'CONTACT', 'ADDRESS']):
                continue
            
            # Name pattern: 2-4 words, mostly capitalized or Title Case, no special chars except hyphens/apostrophes
            # Name usually doesn't contain numbers, @, :, etc.
            words = line.split()
            if 2 <= len(words) <= 4:
                # Check if it looks like a name (Title Case or ALL CAPS, no email/phone patterns)
                if not re.search(r'[@:\d{10,}]', line):  # No email/phone patterns
                    # Check if it's mostly letters and common name characters
                    if re.match(r'^[A-Za-z\s\-\'\.]+$', line):
                        # Skip if it's all lowercase (unlikely to be name at top)
                        if not line.islower():
                            return line
        
        return "unknown"
    
    def _extract_urls_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract URLs from resume text (LinkedIn, GitHub, portfolio, etc.)"""
        if not text:
            return {"linkedin": [], "github": [], "portfolio": [], "other_links": []}
        
        urls = {
            "linkedin": [],
            "github": [],
            "portfolio": [],
            "other_links": []
        }
        
        # Comprehensive URL patterns
        # LinkedIn patterns
        linkedin_patterns = [
            r'linkedin\.com/in/[a-zA-Z0-9\-_]+',
            r'linkedin\.com/profile/view\?id=[a-zA-Z0-9\-_]+',
            r'linkedin\.com/pub/[a-zA-Z0-9\-_]+',
        ]
        
        # GitHub patterns
        github_patterns = [
            r'github\.com/[a-zA-Z0-9\-_]+',
            r'github\.io/[a-zA-Z0-9\-_]+',
        ]
        
        # Portfolio/website patterns (personal domains, common portfolio sites)
        portfolio_patterns = [
            r'www\.[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}',  # www.domain.com
            r'[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[a-zA-Z0-9\-_/]*)?',  # domain.com/path
        ]
        
        # Extract LinkedIn URLs
        for pattern in linkedin_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                url = f"https://{match}" if not match.startswith('http') else match
                if url not in urls["linkedin"]:
                    urls["linkedin"].append(url)
        
        # Extract GitHub URLs
        for pattern in github_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                url = f"https://{match}" if not match.startswith('http') else match
                if url not in urls["github"]:
                    urls["github"].append(url)
        
        # Extract all URLs (including portfolio)
        all_url_pattern = r'(?:https?://)?(?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[a-zA-Z0-9\-_/\.]*)?'
        all_matches = re.findall(all_url_pattern, text, re.IGNORECASE)
        
        for match in all_matches:
            # Skip if already in LinkedIn or GitHub
            if any(site in match.lower() for site in ['linkedin.com', 'github.com']):
                continue
            
            # Skip email domains (common patterns like gmail.com, yahoo.com in contact section)
            if match.lower().split('.')[0] in ['gmail', 'yahoo', 'hotmail', 'outlook', 'icloud', 'aol']:
                continue
            
            url = f"https://{match}" if not match.startswith('http') else match
            
            # Determine category
            if any(site in url.lower() for site in ['portfolio', 'personal', 'blog', 'website', 'www.']):
                if url not in urls["portfolio"]:
                    urls["portfolio"].append(url)
            else:
                # Check if it's a known portfolio/service site
                portfolio_domains = ['behance.net', 'dribbble.com', 'medium.com', 'dev.to', 'hashnode.com', 
                                   'kaggle.com', 'stackoverflow.com', 'twitter.com', 'x.com']
                if any(domain in url.lower() for domain in portfolio_domains):
                    if url not in urls["other_links"]:
                        urls["other_links"].append(url)
                elif url not in urls["portfolio"]:  # Default to portfolio for personal domains
                    urls["portfolio"].append(url)
        
        return urls
    
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

