"""
AI-powered resume parser using LLM for intelligent extraction
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from pathlib import Path
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
    
    def parse_with_ai(self, raw_text: str, pdf_path: Optional[str] = None, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Parse resume using Vision + Layout + Semantic hybrid approach
        Strategy: LayoutLMv3 (vision+layout) -> Section-aware extraction -> NER (within sections) -> Optional LLM refinement
        
        Args:
            raw_text: Raw text from resume
            pdf_path: Optional path to PDF file
            force_reprocess: If True, skip cache and reprocess
        """
        cache_key = get_cache_key("ai_parse", "resume", raw_text[:200])
        
        # Skip cache if force_reprocess is True
        if not force_reprocess:
            cached = get_cache(cache_key)
            if cached:
                logger.info("using_cached_ai_parse", cache_key=cache_key[:50])
                # If we have PDF path and cache doesn't have layout metadata, try layout parsing
                if pdf_path and not cached.get("_metadata", {}).get("parser_version") == "layout-aware-v1.0":
                    logger.info("cache_missing_layout_metadata_trying_layout_parsing")
                    # Don't return cached, continue to layout parsing
                else:
                    return cached
        else:
            logger.info("force_reprocess_skipping_cache")
        
        try:
            # STEP 1: VISION-FIRST PIPELINE (PRIMARY PATH) - MANDATORY
            # This is the mandatory first step for production-grade parsing
            # LayoutLMv3-large provides vision + layout + text understanding
            logger.info("ai_parser_parse_with_ai_called", 
                       has_pdf_path=bool(pdf_path),
                       pdf_path=pdf_path if pdf_path else None,
                       text_length=len(raw_text) if raw_text else 0,
                       force_reprocess=force_reprocess)
            
            if pdf_path:
                logger.info("starting_vision_first_parsing", pdf_path=pdf_path, force_reprocess=force_reprocess)
                try:
                    parsed_data = self._parse_with_layout(raw_text, pdf_path)
                    
                    if parsed_data:
                        metadata = parsed_data.get("_metadata", {})
                        parser_version = metadata.get("parser_version", "")
                        
                        logger.info("layout_parser_returned_data", 
                                   parser_version=parser_version,
                                   has_metadata=bool(metadata),
                                   used_layoutlm=metadata.get("used_layoutlm", False))
                        
                        # Accept layout-aware parsing if it succeeded (even if LayoutLM wasn't used due to fallback)
                        if parser_version in ["layout-aware-v1.0", "text-fallback"]:
                            used_layoutlm = metadata.get("used_layoutlm", False)
                            used_text_detection = metadata.get("used_text_based_detection", False)
                            
                            logger.info("vision_first_parsing_complete", 
                                       used_layoutlm=used_layoutlm,
                                       used_text_detection=used_text_detection,
                                       used_ocr=metadata.get("used_ocr", False),
                                       sections=metadata.get("sections_detected", []))
                            
                            # Post-process: Calculate experience years
                            parsed_data["experience_years"] = self._calculate_experience_years(parsed_data.get("experience", []))
                            
                            # Calculate quality score (higher weight for LayoutLM success)
                            quality_score = self._calculate_quality_score(parsed_data, raw_text, used_layoutlm=used_layoutlm)
                            parsed_data["quality_score"] = quality_score
                            logger.info("vision_first_quality_score", score=quality_score, used_layoutlm=used_layoutlm)
                            
                            # Only proceed to NER merge if quality is acceptable or LayoutLM was used
                            # If LayoutLM was used, trust the vision-first result
                            if used_layoutlm or quality_score >= 60:
                                # Merge with NER for enhanced accuracy (skills, entities within sections)
                                try:
                                    from app.resumes.ner_parser import NERParser
                                    ner_parser = NERParser()
                                    ner_data = ner_parser.parse_with_ner(raw_text, pdf_path)
                                    
                                    # Enhance with NER insights (union of skills, validate entities)
                                    layout_skills = parsed_data.get("skills", {}).get("technical", [])
                                    if isinstance(layout_skills, list):
                                        ner_skills = ner_data.get("skills", [])
                                        if isinstance(ner_skills, list):
                                            all_skills = list(set(layout_skills + ner_skills))
                                            parsed_data["skills"]["technical"] = all_skills
                                            logger.info("ner_skills_merged", total_skills=len(all_skills))
                                    
                                    # Merge experience if layout parsing missed some
                                    # BUT: Only merge if layout parser has NO experience entries
                                    # AND: Filter out education entries from NER results
                                    layout_experience = parsed_data.get("experience", [])
                                    ner_experience = ner_data.get("experience", [])
                                    
                                    if not layout_experience and ner_experience:
                                        # Filter out education entries from NER experience
                                        filtered_ner_experience = []
                                        for exp in ner_experience:
                                            company = exp.get("company", "").upper() if exp.get("company") else ""
                                            # Skip if company is an educational institution
                                            if not any(word in company for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL", "ACADEMY"]):
                                                filtered_ner_experience.append(exp)
                                            else:
                                                logger.info("filtered_education_from_ner_experience", company=exp.get("company"))
                                        
                                        if filtered_ner_experience:
                                            parsed_data["experience"] = filtered_ner_experience
                                            logger.info("ner_experience_merged_filtered", count=len(filtered_ner_experience))
                                    elif layout_experience and ner_experience:
                                        # Layout parser has experience, but check if NER has better dates
                                        # Only merge if layout experience has missing/wrong dates
                                        logger.info("layout_experience_exists_checking_ner_for_improvements", 
                                                   layout_count=len(layout_experience),
                                                   ner_count=len(ner_experience))
                                    
                                    # Merge education if missing
                                    if not parsed_data.get("education") and ner_data.get("education"):
                                        parsed_data["education"] = ner_data.get("education")
                                        logger.info("ner_education_merged")
                                    
                                except Exception as merge_error:
                                    logger.warning("ner_merge_failed", error=str(merge_error))
                            
                            # Cache and return vision-first result
                            set_cache(cache_key, parsed_data, ttl=3600 * 24)
                            return parsed_data
                        else:
                            logger.warning("layout_parsing_unexpected_version", 
                                         parser_version=parser_version,
                                         metadata_keys=list(metadata.keys()) if metadata else [])
                            # Still use the data if it has content, even if version is unexpected
                            if parsed_data.get("skills") or parsed_data.get("experience"):
                                logger.info("using_layout_data_despite_version_mismatch")
                                parsed_data["experience_years"] = self._calculate_experience_years(parsed_data.get("experience", []))
                                quality_score = self._calculate_quality_score(parsed_data, raw_text, used_layoutlm=metadata.get("used_layoutlm", False))
                                parsed_data["quality_score"] = quality_score
                                set_cache(cache_key, parsed_data, ttl=3600 * 24)
                                return parsed_data
                    else:
                        logger.warning("layout_parsing_returned_empty", pdf_path=pdf_path)
                        # Even if empty, check if we should still use it
                        if parsed_data and parsed_data.get("_metadata", {}).get("parser_version") == "layout-aware-v1.0":
                            # Use it even if empty - it's still layout-aware parsing
                            logger.info("using_empty_layout_aware_result")
                            used_layoutlm = parsed_data.get("_metadata", {}).get("used_layoutlm", False)
                            parsed_data["experience_years"] = self._calculate_experience_years(parsed_data.get("experience", []))
                            quality_score = self._calculate_quality_score(parsed_data, raw_text, used_layoutlm=used_layoutlm)
                            parsed_data["quality_score"] = quality_score
                            set_cache(cache_key, parsed_data, ttl=3600 * 24)
                            return parsed_data
                except ImportError as e:
                    logger.error("layout_parser_import_failed", error=str(e), exc_info=True)
                    # Layout parser not available - fallback to NER
                except Exception as e:
                    logger.error("vision_first_parsing_failed", 
                               error=str(e), 
                               error_type=type(e).__name__,
                               exc_info=True,
                               pdf_path=pdf_path)
                    # Continue to NER fallback
            
            # STEP 2: FALLBACK - NER-based parsing (only if vision-first failed or no PDF)
            # This is now the fallback path, not primary
            logger.info("using_ner_based_parsing_fallback", has_pdf_path=bool(pdf_path))
            parsed_data = self._parse_with_ner(raw_text, pdf_path)
            
            # Step 2: Post-process: Calculate experience years
            parsed_data["experience_years"] = self._calculate_experience_years(parsed_data.get("experience", []))
            
            # Step 3: Calculate quality score
            quality_score = self._calculate_quality_score(parsed_data, raw_text)
            parsed_data["quality_score"] = quality_score
            logger.info("ner_quality_score_calculated", score=quality_score)
            
            # Step 4: Optional LLM refinement (only if quality is low or OpenAI is available)
            # Skip LLM on CPU for HuggingFace (too slow), use OpenAI if available
            use_llm_refinement = (
                quality_score < 70 and  # Low quality - needs refinement
                self.ai_engine.provider == "openai" and 
                self.ai_engine.openai_client
            )
            
            if use_llm_refinement:
                logger.info("applying_llm_refinement", quality_score=quality_score)
                try:
                    refined_data = self._parse_with_openai(raw_text)
                    refined_score = refined_data.get("quality_score", 0)
                    # Use refined data if it's significantly better
                    if refined_score > quality_score + 10:
                        logger.info("llm_refinement_improved", 
                                   old_score=quality_score, 
                                   new_score=refined_score)
                        parsed_data = refined_data
                    else:
                        logger.info("llm_refinement_no_improvement", 
                                   ner_score=quality_score, 
                                   llm_score=refined_score)
                except Exception as e:
                    logger.warning("llm_refinement_failed", error=str(e))
                    # Continue with NER result
            
            # Cache the result
            set_cache(cache_key, parsed_data, ttl=3600 * 24)  # Cache for 24 hours
            
            return parsed_data
            
        except Exception as e:
            logger.error("ner_parsing_failed", error=str(e), exc_info=True)
            # Fallback to rule-based parsing
            parsed_data = self._parse_with_rules(raw_text)
            parsed_data["experience_years"] = self._calculate_experience_years(parsed_data.get("experience", []))
            quality_score = self._calculate_quality_score(parsed_data, raw_text)
            parsed_data["quality_score"] = quality_score
            logger.info("fallback_quality_score_calculated", score=quality_score)
            return parsed_data
    
    def _parse_with_layout(self, text: str, pdf_path: str) -> Dict[str, Any]:
        """
        Parse resume using layout-aware pipeline (LayoutLMv3 + Section Detection + Semantic Normalization)
        This is the new primary method for complex resumes
        """
        logger.info("_parse_with_layout_called", 
                   pdf_path=pdf_path, 
                   text_length=len(text) if text else 0,
                   pdf_path_exists=Path(pdf_path).exists() if pdf_path else False)
        try:
            from app.resumes.layout_parser import LayoutParser
            logger.info("layout_parser_imported_successfully")
            
            # Check if LayoutParser can be instantiated
            try:
                layout_parser = LayoutParser()
                logger.info("layout_parser_initialized", 
                           pdf_path=pdf_path,
                           layoutlm_available=layout_parser.layoutlm_processor.is_available,
                           device=layout_parser.device)
            except Exception as init_error:
                logger.error("layout_parser_initialization_failed", 
                           error=str(init_error),
                           error_type=type(init_error).__name__,
                           exc_info=True)
                return None
            
            # Call parse method
            logger.info("calling_layout_parser_parse", pdf_path=pdf_path)
            parsed_data = layout_parser.parse(pdf_path, text_from_pdf=text)
            logger.info("layout_parser_parse_completed", 
                       has_data=bool(parsed_data),
                       parser_version=parsed_data.get("_metadata", {}).get("parser_version", "unknown") if parsed_data else "none",
                       has_experience=bool(parsed_data.get("experience")) if parsed_data else False,
                       has_skills=bool(parsed_data.get("skills")) if parsed_data else False)
            
            if not parsed_data:
                logger.warning("layout_parser_returned_none", pdf_path=pdf_path)
                return None
            
            # Merge with NER parsing for enhanced accuracy within sections
            # This gives us the best of both worlds: layout understanding + NER precision
            try:
                from app.resumes.ner_parser import NERParser
                ner_parser = NERParser()
                ner_data = ner_parser.parse_with_ner(text, pdf_path)
                
                # Enhance parsed_data with NER insights
                # Merge skills (union)
                layout_skills = parsed_data.get("skills", {}).get("technical", [])
                ner_skills = ner_data.get("skills", [])
                if isinstance(layout_skills, list) and isinstance(ner_skills, list):
                    all_skills = list(set(layout_skills + ner_skills))
                    parsed_data["skills"]["technical"] = all_skills
                
                # Merge experience (prefer layout if available, else NER)
                if not parsed_data.get("experience") and ner_data.get("experience"):
                    parsed_data["experience"] = ner_data.get("experience")
                
                # Merge education
                if not parsed_data.get("education") and ner_data.get("education"):
                    parsed_data["education"] = ner_data.get("education")
                
                logger.info("layout_ner_merge_complete")
            except Exception as e:
                logger.warning("ner_merge_failed", error=str(e))
            
            return parsed_data
        except ImportError as e:
            logger.error("layout_parser_import_failed_in_method", error=str(e), exc_info=True)
            return None
        except Exception as e:
            logger.error("layout_parsing_failed", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        exc_info=True)
            return None
    
    def _parse_with_ner(self, text: str, pdf_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse resume using NER-based extraction (fast, accurate)
        This is the fallback parsing method - much faster than LLMs
        Uses HURIDOCS layout analysis if PDF path provided
        """
        try:
            from app.resumes.ner_parser import NERParser
            ner_parser = NERParser()
            parsed_data = ner_parser.parse_with_ner(text, pdf_path)
            logger.info("ner_parsing_success")
            return parsed_data
        except Exception as e:
            logger.warning("ner_parser_not_available", error=str(e))
            # Fallback to rule-based
            return self._parse_with_rules(text)
    
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
        
        Note: Large models like Mistral-7B are very slow on CPU. For CPU-only systems,
        we skip AI parsing and use rule-based parsing for faster processing.
        """
        # Skip AI parsing on CPU for large models - they're too slow (15+ minutes)
        # Use GPU or OpenAI API for better quality AI parsing
        device = settings.MODEL_DEVICE
        if not settings.USE_GPU and device == "cpu":
            logger.info("skipping_ai_parsing_on_cpu", 
                       reason="Large models too slow on CPU, using rule-based for faster processing",
                       model=settings.HUGGINGFACE_PARSER_MODEL)
            return self._parse_with_rules(text)
        
        try:
            # Try using specialized Hugging Face PDF parser (only if GPU available)
            logger.info("attempting_hf_pdf_parser", model=settings.HUGGINGFACE_PARSER_MODEL, device=device)
            from app.resumes.hf_pdf_parser import hf_pdf_parser
            parsed_data = hf_pdf_parser.parse_resume(text)
            if parsed_data and parsed_data.get("quality_score", 0) > 0:
                logger.info("hf_pdf_parser_success", quality_score=parsed_data.get("quality_score"))
                return parsed_data
            else:
                logger.warning("hf_pdf_parser_returned_empty_or_low_quality", 
                            has_data=bool(parsed_data),
                            quality_score=parsed_data.get("quality_score") if parsed_data else None)
        except ImportError as e:
            logger.warning("hf_pdf_parser_not_available", error=str(e), exc_info=True)
        except Exception as e:
            logger.error("huggingface_parsing_failed", error=str(e), exc_info=True)
        
        # Fallback to rule-based
        logger.warning("falling_back_to_rule_based_parsing")
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
    
    def _calculate_quality_score(self, parsed_data: Dict[str, Any], raw_text: str, used_layoutlm: bool = False) -> int:
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
        
        # Layout confidence scoring (15 points)
        # VISION-FIRST architecture: LayoutLM success significantly boosts quality
        metadata = parsed_data.get("_metadata", {})
        if used_layoutlm and metadata.get("used_layoutlm"):
            # LayoutLM was successfully used - highest confidence
            score += 15
            logger.info("layoutlm_bonus_applied", bonus=15)
        elif metadata.get("used_text_based_detection"):
            # Text-based section detection (still layout-aware via position)
            score += 8
            logger.info("text_based_layout_bonus_applied", bonus=8)
        
        # Penalize fallback usage (indicates layout parsing failed)
        if metadata.get("parser_version") == "text-fallback":
            score = max(0, score - 20)  # Strong penalty for fallback
            logger.warning("fallback_penalty_applied", penalty=20)
        
        # OCR usage bonus (scanned PDFs are harder but handled correctly)
        if metadata.get("used_ocr"):
            # OCR was used successfully - don't penalize, it's correct handling
            logger.info("ocr_used_quality_maintained")
        
        return min(score, max_score)


# Global instance
ai_parser = AIParser()

