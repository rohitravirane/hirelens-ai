"""
AI-powered resume parser using LLM for intelligent extraction
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import re
import json
import structlog
from dateutil.relativedelta import relativedelta

from app.ai_engine.service import ai_engine
from app.core.config import settings
from app.core.redis_client import get_cache, set_cache, get_cache_key

logger = structlog.get_logger()


class AIParser:
    """AI-powered resume parser using LLM for intelligent data extraction"""
    
    def __init__(self):
        self.ai_engine = ai_engine
    
    def parse_with_ai(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse resume using AI/LLM to extract structured data
        This is the heart of the system - intelligent extraction
        """
        cache_key = get_cache_key("ai_parse", "resume", raw_text[:200])
        cached = get_cache(cache_key)
        if cached:
            logger.info("using_cached_ai_parse")
            return cached
        
        try:
            # Use AI to extract structured data
            if self.ai_engine.provider == "openai" and self.ai_engine.openai_client:
                parsed_data = self._parse_with_openai(raw_text)
            elif self.ai_engine.provider == "huggingface":
                parsed_data = self._parse_with_huggingface(raw_text)
            else:
                # Fallback to rule-based
                parsed_data = self._parse_with_rules(raw_text)
            
            # Post-process: Calculate experience years from date ranges
            parsed_data["experience_years"] = self._calculate_experience_years(parsed_data.get("experience", []))
            
            # Calculate quality score if not already calculated
            if "quality_score" not in parsed_data or parsed_data.get("quality_score") is None:
                quality_score = self._calculate_quality_score(parsed_data, raw_text)
                parsed_data["quality_score"] = quality_score
                logger.info("quality_score_calculated", score=quality_score)
            
            # Cache the result
            set_cache(cache_key, parsed_data, ttl=3600 * 24)  # Cache for 24 hours
            
            return parsed_data
            
        except Exception as e:
            logger.error("ai_parsing_failed", error=str(e))
            # Fallback to rule-based parsing
            parsed_data = self._parse_with_rules(raw_text)
            # Calculate quality score for fallback parsing too
            parsed_data["experience_years"] = self._calculate_experience_years(parsed_data.get("experience", []))
            quality_score = self._calculate_quality_score(parsed_data, raw_text)
            parsed_data["quality_score"] = quality_score
            logger.info("fallback_quality_score_calculated", score=quality_score)
            return parsed_data
    
    def _parse_with_openai(self, text: str) -> Dict[str, Any]:
        """Parse resume using OpenAI GPT with world-class extraction"""
        # Enhanced prompt for better extraction
        prompt = f"""You are an expert resume parser with deep understanding of different resume formats, layouts, and structures. Your task is to extract ALL information accurately from this resume, regardless of format.

CRITICAL INSTRUCTIONS:
1. Extract EVERY skill mentioned (technical, soft skills, tools, frameworks, languages)
2. For experience: Extract ALL jobs with EXACT dates (start_date and end_date in YYYY-MM format or YYYY)
3. Calculate dates carefully - handle formats like "Jan 2020", "01/2020", "2020-01", "2020", "Present", "Current"
4. Extract full job descriptions, responsibilities, achievements
5. Extract ALL education entries with degrees, institutions, fields, graduation years
6. Extract ALL projects with names, descriptions, technologies used
7. Extract certifications, licenses, awards
8. Extract languages (both programming and spoken)
9. Be thorough - don't miss any information

Return ONLY valid JSON with this EXACT structure (all fields required, use empty arrays/lists if not found):

{{
  "name": "Full name as written",
  "email": "Email address if found",
  "phone": "Phone number if found",
  "skills": ["skill1", "skill2", ...],  // ALL skills mentioned
  "experience": [
    {{
      "title": "Exact job title",
      "company": "Company name",
      "start_date": "YYYY-MM or YYYY",  // MUST be in this format
      "end_date": "YYYY-MM or YYYY or 'present'",  // Use 'present' if current job
      "location": "Location if mentioned",
      "description": "Full job description with responsibilities and achievements",
      "technologies": ["tech1", "tech2", ...]  // Technologies used in this role
    }}
  ],
  "education": [
    {{
      "degree": "Degree name (e.g., Bachelor of Science, Master of Engineering)",
      "institution": "Full institution name",
      "field": "Field of study (e.g., Computer Science, Electrical Engineering)",
      "year": "YYYY",  // Graduation year
      "gpa": "GPA if mentioned",
      "location": "Location if mentioned"
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "Detailed project description",
      "technologies": ["tech1", "tech2", ...],
      "url": "URL if mentioned",
      "duration": "Duration if mentioned"
    }}
  ],
  "certifications": ["cert1", "cert2", ...],  // All certifications/licenses
  "languages": ["language1", "language2", ...],  // Both programming and spoken
  "summary": "Professional summary or objective if available"
}}

Resume text (extract from ALL of this):
{text[:6000]}

IMPORTANT: 
- Extract dates in YYYY-MM format when possible (e.g., "2020-01" for January 2020)
- If only year is available, use YYYY format
- For current jobs, use "present" as end_date
- Extract ALL information - be comprehensive
- Return ONLY valid JSON, no markdown, no explanations"""

        try:
            response = self.ai_engine.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a world-class resume parser. You understand all resume formats (chronological, functional, hybrid, ATS-friendly). Extract ALL information accurately. Always return ONLY valid JSON, no markdown, no explanations, no code blocks."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Zero temperature for maximum consistency
                max_tokens=4000,  # Increased for comprehensive extraction
                response_format={"type": "json_object"} if hasattr(settings, 'OPENAI_MODEL') and 'gpt-4' in settings.OPENAI_MODEL.lower() else None,
            )
            
            content = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            parsed = json.loads(content)
            logger.info("openai_parsing_success", skills_count=len(parsed.get("skills", [])), exp_count=len(parsed.get("experience", [])))
            
            normalized = self._normalize_parsed_data(parsed)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(normalized, text)
            normalized["quality_score"] = quality_score
            logger.info("parsing_quality_score", score=quality_score)
            
            return normalized
            
        except json.JSONDecodeError as e:
            logger.error("openai_json_parse_error", error=str(e), content=content[:200])
            return self._parse_with_rules(text)
        except Exception as e:
            logger.error("openai_parsing_error", error=str(e))
            return self._parse_with_rules(text)
    
    def _parse_with_huggingface(self, text: str) -> Dict[str, Any]:
        """
        Parse resume using HuggingFace models for world-class extraction
        Uses advanced document understanding models from Hugging Face Hub
        """
        try:
            # Try using specialized Hugging Face PDF parser
            from app.resumes.hf_pdf_parser import hf_pdf_parser
            parsed_data = hf_pdf_parser.parse_resume(text)
            if parsed_data:
                logger.info("hf_pdf_parser_success")
                return parsed_data
        except ImportError:
            logger.warning("hf_pdf_parser_not_available")
        except Exception as e:
            logger.warning("huggingface_parsing_failed", error=str(e))
        
        # Fallback to rule-based
        return self._parse_with_rules(text)
    
    def _parse_with_rules(self, text: str) -> Dict[str, Any]:
        """Rule-based parsing with enhanced heuristics"""
        from app.resumes.parser import ResumeParser
        parser = ResumeParser()
        return parser.parse(text)
    
    def _calculate_experience_years(self, experience_list: List[Dict[str, Any]]) -> Optional[int]:
        """
        Calculate total years of experience from date ranges
        This is the intelligent calculation - heart of experience extraction
        """
        if not experience_list:
            return None
        
        total_days = 0
        date_ranges = []
        
        for exp in experience_list:
            start_date = self._parse_date(exp.get("start_date"))
            end_date = self._parse_date(exp.get("end_date"), is_end=True)
            
            if start_date and end_date:
                # Calculate days between dates
                delta = end_date - start_date
                days = delta.days
                
                # Avoid overlapping periods (take maximum)
                date_ranges.append((start_date, end_date, days))
        
        if not date_ranges:
            return None
        
        # Sort by start date
        date_ranges.sort(key=lambda x: x[0])
        
        # Merge overlapping periods
        merged_ranges = []
        for start, end, days in date_ranges:
            if not merged_ranges:
                merged_ranges.append((start, end, days))
            else:
                last_start, last_end, last_days = merged_ranges[-1]
                # Check if overlapping
                if start <= last_end:
                    # Merge: take the later end date
                    new_end = max(end, last_end)
                    new_days = (new_end - last_start).days
                    merged_ranges[-1] = (last_start, new_end, new_days)
                else:
                    merged_ranges.append((start, end, days))
        
        # Sum all non-overlapping periods
        total_days = sum(days for _, _, days in merged_ranges)
        
        # Convert to years (approximate)
        years = total_days / 365.25
        
        # Round to nearest 0.5 years
        years_rounded = round(years * 2) / 2
        
        logger.info("experience_calculated", years=years_rounded, periods=len(merged_ranges))
        return int(years_rounded) if years_rounded >= 1 else None
    
    def _parse_date(self, date_str: Optional[str], is_end: bool = False) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            if is_end:
                return date.today()  # Current date for "present"
            return None
        
        date_str = date_str.lower().strip()
        
        # Handle "present", "current", "now"
        if date_str in ["present", "current", "now", ""]:
            return date.today() if is_end else None
        
        # Try different date formats
        formats = [
            "%Y-%m",      # 2020-01
            "%Y-%m-%d",   # 2020-01-15
            "%Y",         # 2020
            "%B %Y",      # January 2020
            "%b %Y",      # Jan 2020
            "%m/%Y",      # 01/2020
            "%d/%m/%Y",   # 15/01/2020
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                # If only year, set to January 1st for start, December 31st for end
                if fmt == "%Y":
                    if is_end:
                        return date(parsed.year, 12, 31)
                    else:
                        return date(parsed.year, 1, 1)
                return parsed
            except ValueError:
                continue
        
        # Try to extract year from string
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            year = int(year_match.group(0))
            if is_end:
                return date(year, 12, 31)
            else:
                return date(year, 1, 1)
        
        logger.warning("date_parse_failed", date_str=date_str)
        return None
    
    def _normalize_parsed_data(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parsed data to standard format"""
        normalized = {
            "skills": parsed.get("skills", []),
            "experience": parsed.get("experience", []),
            "education": parsed.get("education", []),
            "projects": parsed.get("projects", []),
            "certifications": parsed.get("certifications", []),
            "languages": parsed.get("languages", []),
            "experience_years": None,  # Will be calculated
        }
        
        # Ensure all lists are lists
        for key in ["skills", "experience", "education", "projects", "certifications", "languages"]:
            if not isinstance(normalized[key], list):
                normalized[key] = []
        
        # Clean and validate experience dates
        for exp in normalized["experience"]:
            if isinstance(exp, dict):
                # Ensure dates are in correct format
                start_date = exp.get("start_date", "")
                end_date = exp.get("end_date", "")
                
                # Normalize date formats
                if start_date:
                    exp["start_date"] = self._normalize_date_string(start_date)
                if end_date:
                    exp["end_date"] = self._normalize_date_string(end_date, is_end=True)
        
        return normalized
    
    def _normalize_date_string(self, date_str: str, is_end: bool = False) -> str:
        """Normalize date string to YYYY-MM or YYYY format"""
        if not date_str:
            return "present" if is_end else ""
        
        date_str = date_str.lower().strip()
        
        # Handle present/current
        if date_str in ["present", "current", "now", ""]:
            return "present" if is_end else ""
        
        # Try to parse and normalize
        parsed_date = self._parse_date(date_str, is_end)
        if parsed_date:
            if parsed_date.day == 1 and parsed_date.month == 1:
                # Only year available
                return str(parsed_date.year)
            else:
                # Full date available
                return parsed_date.strftime("%Y-%m")
        
        return date_str  # Return as-is if can't parse
    
    def _calculate_quality_score(self, parsed_data: Dict[str, Any], raw_text: str) -> int:
        """
        Calculate quality score (0-100) for parsed resume data
        This is critical for determining if reprocessing is needed
        """
        score = 0
        max_score = 100
        
        # Skills (20 points)
        skills = parsed_data.get("skills", [])
        if len(skills) >= 10:
            score += 20
        elif len(skills) >= 5:
            score += 15
        elif len(skills) >= 3:
            score += 10
        elif len(skills) > 0:
            score += 5
        
        # Experience years calculated (20 points)
        if parsed_data.get("experience_years") is not None:
            score += 20
        
        # Experience details (20 points)
        experience = parsed_data.get("experience", [])
        if len(experience) >= 3:
            score += 20
        elif len(experience) >= 2:
            score += 15
        elif len(experience) >= 1:
            # Check if experience has dates
            has_dates = any(
                exp.get("start_date") or exp.get("end_date") 
                for exp in experience if isinstance(exp, dict)
            )
            score += 10 if has_dates else 5
        
        # Education (15 points)
        education = parsed_data.get("education", [])
        if len(education) >= 2:
            score += 15
        elif len(education) >= 1:
            score += 10
        
        # Projects (10 points)
        projects = parsed_data.get("projects", [])
        if len(projects) >= 2:
            score += 10
        elif len(projects) >= 1:
            score += 5
        
        # Raw text quality (10 points)
        if raw_text and len(raw_text) > 500:
            score += 10
        elif raw_text and len(raw_text) > 200:
            score += 5
        
        # Data completeness (5 points)
        # Check if we have at least some data in multiple categories
        categories_with_data = sum([
            1 if skills else 0,
            1 if experience else 0,
            1 if education else 0,
            1 if projects else 0,
        ])
        if categories_with_data >= 3:
            score += 5
        
        return min(score, max_score)


# Global instance
ai_parser = AIParser()

