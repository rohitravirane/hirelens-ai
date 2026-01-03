"""
Main Layout Parser - Orchestrates vision + layout + semantic pipeline
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import structlog

from app.resumes.layout_parser.pdf_to_image import PDFToImageConverter
from app.resumes.layout_parser.ocr_engine import OCREngine
from app.resumes.layout_parser.layoutlm_processor import LayoutLMProcessor
from app.resumes.layout_parser.section_detector import SectionDetector
from app.resumes.layout_parser.semantic_normalizer import SemanticNormalizer

logger = structlog.get_logger()


class LayoutParser:
    """
    Main layout-aware resume parser
    Pipeline: PDF → Images → LayoutLMv3 → Section Detection → Semantic Normalization
    """
    
    def __init__(self, use_gpu: Optional[bool] = None):
        """
        Initialize layout parser - VISION-FIRST architecture
        
        Args:
            use_gpu: Whether to use GPU (None = auto-detect from CUDA availability)
        """
        from app.core.config import settings
        import torch
        
        # MANDATORY: Auto-detect GPU for vision-first pipeline
        # This is production-grade: use GPU when available for LayoutLMv3-large
        # IMPORTANT: CUDA calls in forked processes (Celery workers) can fail
        # Wrap all CUDA calls in try-except to handle fork issues gracefully
        try:
            if use_gpu is None:
                # Auto-detect: prefer GPU if available (RTX 4060 will be detected)
                # Safe CUDA check - wrapped in try-except for fork compatibility
                try:
                    cuda_available = torch.cuda.is_available()
                except RuntimeError as e:
                    # CUDA can't be re-initialized in forked process
                    logger.warning("cuda_check_failed_in_fork", error=str(e))
                    cuda_available = False
                
                if cuda_available:
                    self.device = "cuda"
                    logger.info("gpu_auto_detected_fork_safe")
                    # Device name/memory will be logged by LayoutLMProcessor when it initializes
                else:
                    self.device = "cpu"
                    logger.warning("gpu_not_available_using_cpu")
            elif use_gpu:
                # Explicitly requested GPU
                try:
                    cuda_available = torch.cuda.is_available()
                except RuntimeError as e:
                    logger.warning("cuda_check_failed_in_fork", error=str(e))
                    cuda_available = False
                
                if cuda_available:
                    self.device = "cuda"
                    logger.info("gpu_explicitly_requested_fork_safe")
                else:
                    logger.warning("gpu_requested_but_not_available_using_cpu")
                    self.device = "cpu"
            else:
                # Explicitly requested CPU
                self.device = "cpu"
                logger.info("cpu_explicitly_requested")
        except Exception as e:
            # Fallback to CPU if anything goes wrong
            logger.error("device_detection_failed_using_cpu", error=str(e))
            self.device = "cpu"
        
        # Initialize components
        self.pdf_converter = PDFToImageConverter(dpi=200)
        self.ocr_engine = OCREngine()
        self.layoutlm_processor = LayoutLMProcessor(device=self.device)
        self.section_detector = SectionDetector()
        
        # Use Qwen2.5-7B or Mistral-7B for semantic normalization
        # Prefer Qwen2.5-7B as it's better for structured output
        try:
            self.semantic_normalizer = SemanticNormalizer(
                model_name="Qwen/Qwen2.5-7B-Instruct",
                device=self.device
            )
        except Exception as e:
            logger.warning("qwen_not_available_trying_mistral", error=str(e))
            try:
                self.semantic_normalizer = SemanticNormalizer(
                    model_name="mistralai/Mistral-7B-Instruct-v0.1",
                    device=self.device
                )
            except Exception as e2:
                logger.warning("mistral_not_available_using_rule_based", error=str(e2))
                self.semantic_normalizer = None
        
        logger.info("layout_parser_initialized", 
                   device=self.device,
                   layoutlm_available=self.layoutlm_processor.is_available,
                   semantic_normalizer_available=self.semantic_normalizer is not None and self.semantic_normalizer.is_available)
    
    def parse(
        self,
        pdf_path: str,
        text_from_pdf: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse resume using vision + layout + semantic pipeline
        
        Args:
            pdf_path: Path to PDF file
            text_from_pdf: Optional pre-extracted text (for text-based PDFs)
            
        Returns:
            Structured parsed data with quality metadata
        """
        try:
            logger.info("starting_layout_aware_parsing", pdf_path=pdf_path)
            
            # Step 1: Convert PDF to images
            logger.info("pdf_to_image_conversion_starting", pdf_path=pdf_path)
            try:
                images = self.pdf_converter.convert(pdf_path)
                logger.info("pdf_to_image_conversion_complete", 
                           images_count=len(images) if images else 0,
                           first_image_size=images[0].size if images and len(images) > 0 else None)
                if not images:
                    logger.warning("no_images_from_pdf_fallback_to_text")
                    return self._fallback_to_text_parsing(text_from_pdf or "")
            except Exception as e:
                logger.warning("pdf_to_image_conversion_failed", error=str(e), exc_info=True)
                # Fallback to text-based section detection
                if text_from_pdf:
                    logger.info("using_text_based_parsing_due_to_image_conversion_failure")
                    text_blocks = self._create_text_blocks_from_text(text_from_pdf)
                    layoutlm_result = {
                        "text_blocks": text_blocks,
                        "layout_structure": {},
                        "raw_text": text_from_pdf
                    }
                    
                    # Detect sections from text
                    sections = self.section_detector.detect_sections(text_blocks)
                    header_info = self.section_detector.detect_header_section(text_blocks)
                    
                    # Normalize
                    if self.semantic_normalizer and self.semantic_normalizer.is_available:
                        normalized = self.semantic_normalizer.normalize(sections, header_info)
                    else:
                        if self.semantic_normalizer:
                            normalized = self.semantic_normalizer._rule_based_normalize(sections, header_info)
                        else:
                            normalized = self._basic_normalize(sections, header_info)
                    
                    # Ensure skills format
                    if isinstance(normalized.get("skills"), list):
                        normalized["skills"] = {
                            "technical": normalized["skills"],
                            "languages": [],
                            "tools": [],
                            "frameworks": []
                        }
                    
                    normalized["_metadata"] = {
                        "parser_version": "layout-aware-v1.0",
                        "used_layoutlm": False,
                        "used_text_based_detection": True,
                        "used_ocr": False,
                        "used_semantic_normalizer": self.semantic_normalizer is not None and self.semantic_normalizer.is_available,
                        "pages_processed": 0,
                        "sections_detected": list(sections.keys())
                    }
                    
                    return normalized
                else:
                    return self._fallback_to_text_parsing(text_from_pdf or "")
            
            # Step 2: Determine if scanned PDF (needs OCR)
            is_scanned = self.ocr_engine.is_scanned_pdf(images[0], text_from_pdf or "")
            
            # Step 3: Process first page with LayoutLMv3
            first_page_image = images[0]
            page_text = text_from_pdf or ""
            
            if is_scanned:
                logger.info("detected_scanned_pdf_using_ocr")
                ocr_result = self.ocr_engine.extract_text(first_page_image)
                page_text = ocr_result["text"]
            
            # Step 4: VISION-FIRST - Run LayoutLMv3 processing (PRIMARY PATH)
            # This is the core of vision-first architecture - LayoutLM is MANDATORY
            layoutlm_used = False
            layoutlm_error = None
            
            # CRITICAL: Log LayoutLMv3 availability status
            logger.info("layoutlmv3_availability_check", 
                       is_available=self.layoutlm_processor.is_available,
                       processor_exists=self.layoutlm_processor.processor is not None,
                       model_exists=self.layoutlm_processor.model is not None,
                       device=self.layoutlm_processor.device)
            
            if not self.layoutlm_processor.is_available:
                logger.error("layoutlmv3_not_available_critical",
                           processor_exists=self.layoutlm_processor.processor is not None,
                           model_exists=self.layoutlm_processor.model is not None,
                           device=self.layoutlm_processor.device,
                           message="LayoutLMv3 is MANDATORY for vision-first architecture. Check model loading logs.")
            
            if self.layoutlm_processor.is_available:
                try:
                    logger.info("attempting_layoutlmv3_processing", 
                               image_size=first_page_image.size,
                               text_length=len(page_text) if page_text else 0)
                    
                    # Process with LayoutLMv3 - this is the primary extraction method
                    layoutlm_result = self.layoutlm_processor.process_page(
                        first_page_image,
                        text=page_text
                    )
                    
                    # Check if LayoutLMv3 actually produced results
                    text_blocks = layoutlm_result.get("text_blocks")
                    tokens = layoutlm_result.get("tokens")
                    
                    has_text_blocks = text_blocks is not None and len(text_blocks) > 0
                    has_tokens = tokens is not None and len(tokens) > 0
                    
                    # CRITICAL: Log detailed result structure
                    logger.info("layoutlmv3_processing_result",
                               has_text_blocks=has_text_blocks,
                               text_blocks_type=type(text_blocks).__name__ if text_blocks is not None else "None",
                               text_blocks_count=len(text_blocks) if text_blocks else 0,
                               has_tokens=has_tokens,
                               tokens_type=type(tokens).__name__ if tokens is not None else "None",
                               tokens_count=len(tokens) if tokens else 0,
                               result_keys=list(layoutlm_result.keys()))
                    
                    # CRITICAL: Set flag if LayoutLMv3 produced any results
                    # LayoutLMv3 is considered "used" if it processed and returned results
                    if has_text_blocks or has_tokens:
                        layoutlm_used = True
                        logger.info("layoutlmv3_processing_successful_flag_set", 
                                   blocks_count=len(text_blocks) if text_blocks else 0,
                                   tokens_count=len(tokens) if tokens else 0,
                                   layoutlm_used_flag=True,
                                   layoutlm_used_variable=layoutlm_used,
                                   has_text_blocks=has_text_blocks,
                                   has_tokens=has_tokens)
                        # CRITICAL: Double-check the flag was set
                        if not layoutlm_used:
                            logger.error("layoutlm_used_flag_not_set_after_processing",
                                       has_text_blocks=has_text_blocks,
                                       has_tokens=has_tokens)
                    else:
                        # Even if blocks are empty, if LayoutLMv3 processed (not fallback), mark as used
                        # Check if this is a fallback result (empty dict/None) vs actual LayoutLM result
                        is_fallback_result = (
                            not layoutlm_result.get("tokens") and 
                            not layoutlm_result.get("text_blocks") and
                            layoutlm_result.get("raw_text") == (page_text or "")
                        )
                        if not is_fallback_result:
                            # LayoutLMv3 processed but returned empty results - still mark as used
                            layoutlm_used = True
                            logger.info("layoutlmv3_processed_but_empty_results_still_marking_as_used")
                        else:
                            logger.warning("layoutlmv3_no_blocks_using_text_fallback",
                                         text_blocks_exists=text_blocks is not None,
                                         tokens_exists=tokens is not None,
                                         result_keys=list(layoutlm_result.keys()))
                except Exception as e:
                    layoutlm_error = str(e)
                    logger.error("layoutlmv3_processing_exception", 
                               error=layoutlm_error, 
                               error_type=type(e).__name__,
                               exc_info=True)
                    # Only fallback on actual errors, not availability checks
            
            # If LayoutLMv3 not available or failed, use text-based section detection (FALLBACK ONLY)
            if not layoutlm_used:
                logger.warning("layoutlmv3_not_used_fallback_to_text",
                             reason="not_available" if not self.layoutlm_processor.is_available else "processing_failed",
                             error=layoutlm_error if layoutlm_error else None)
                
                if page_text:
                    logger.info("using_text_based_section_detection", text_length=len(page_text))
                    # Create text blocks from raw text for section detection
                    text_blocks = self._create_text_blocks_from_text(page_text)
                    layoutlm_result = {
                        "text_blocks": text_blocks,
                        "layout_structure": {},
                        "raw_text": page_text
                    }
                else:
                    logger.warning("no_text_available_fallback")
                    return self._fallback_to_text_parsing(page_text)
            
            # Step 5: Detect sections (with column awareness from LayoutLM bboxes)
            # This is FIRST-CLASS section detection using layout structure
            sections = self.section_detector.detect_sections(
                layoutlm_result["text_blocks"],
                layout_info=layoutlm_result.get("layout_structure")
            )
            
            # Step 6: Detect header
            header_info = self.section_detector.detect_header_section(
                layoutlm_result["text_blocks"]
            )
            
            # Step 7: Semantic normalization
            if self.semantic_normalizer and self.semantic_normalizer.is_available:
                normalized = self.semantic_normalizer.normalize(sections, header_info)
            else:
                logger.warning("semantic_normalizer_not_available_using_rule_based")
                if self.semantic_normalizer:
                    normalized = self.semantic_normalizer._rule_based_normalize(sections, header_info)
                else:
                    normalized = self._basic_normalize(sections, header_info)
            
            # Step 8: Add metadata
            # Ensure skills is a dict if it's a list (for backward compatibility)
            if isinstance(normalized.get("skills"), list):
                normalized["skills"] = {
                    "technical": normalized["skills"],
                    "languages": [],
                    "tools": [],
                    "frameworks": []
                }
            
            # Track if LayoutLM was actually used (use the layoutlm_used flag set during processing)
            # CRITICAL: Use layoutlm_used variable that was set when LayoutLMv3 processing succeeded
            # This ensures accurate tracking of whether LayoutLMv3 was actually used
            
            # FINAL CHECK: If LayoutLMv3 processed successfully (we have layoutlm_result with data),
            # and it's not a fallback result, mark as used
            if not layoutlm_used and self.layoutlm_processor.is_available:
                # Double-check: if we have LayoutLM result with actual data, mark as used
                has_actual_layoutlm_data = (
                    layoutlm_result.get("tokens") and len(layoutlm_result.get("tokens", [])) > 0
                ) or (
                    layoutlm_result.get("text_blocks") and len(layoutlm_result.get("text_blocks", [])) > 0
                )
                if has_actual_layoutlm_data:
                    layoutlm_used = True
                    logger.warning("layoutlm_used_flag_corrected_to_true",
                                 reason="layoutlm_result_has_data_but_flag_was_false")
            
            normalized["_metadata"] = {
                "parser_version": "layout-aware-v1.0",
                "used_layoutlm": layoutlm_used,  # Use the actual flag from processing
                "used_text_based_detection": not layoutlm_used,  # Inverse of LayoutLM usage
                "used_ocr": is_scanned,
                "used_semantic_normalizer": self.semantic_normalizer is not None and self.semantic_normalizer.is_available,
                "pages_processed": len(images),
                "sections_detected": list(sections.keys())
            }
            
            # CRITICAL: Log before setting metadata to debug flag value
            logger.info("metadata_set_with_layoutlm_status",
                       used_layoutlm=layoutlm_used,
                       used_text_detection=not layoutlm_used,
                       layoutlm_available=self.layoutlm_processor.is_available,
                       layoutlm_used_flag_value=layoutlm_used,
                       layoutlm_used_flag_type=type(layoutlm_used).__name__,
                       final_metadata_used_layoutlm=normalized["_metadata"]["used_layoutlm"])
            
            logger.info("layout_aware_parsing_complete",
                       sections=len(sections),
                       has_experience=bool(normalized.get("experience")),
                       has_education=bool(normalized.get("education")))
            
            return normalized
            
        except Exception as e:
            logger.error("layout_parsing_failed", error=str(e), exc_info=True)
            # Fallback to text-based parsing
            return self._fallback_to_text_parsing(text_from_pdf or "")
    
    def _fallback_to_text_parsing(self, text: str) -> Dict[str, Any]:
        """Fallback to text-based parsing when layout parsing fails"""
        logger.warning("falling_back_to_text_parsing")
        
        # Return basic structure - will be enhanced by NER parser
        return {
            "name": None,
            "email": None,
            "phone": None,
            "contact": {},
            "experience": [],
            "education": [],
            "skills": {"technical": [], "languages": [], "tools": [], "frameworks": []},
            "projects": [],
            "certifications": [],
            "languages": [],
            "leadership_signals": [],
            "metrics_extracted": [],
            "_metadata": {
                "parser_version": "text-fallback",
                "used_layoutlm": False,
                "used_ocr": False,
                "used_semantic_normalizer": False,
                "fallback_reason": "layout_parsing_failed"
            }
        }
    
    def _basic_normalize(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        header_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Basic normalization without LLM"""
        normalized = {
            "name": header_info.get("name"),
            "email": header_info.get("email"),
            "phone": header_info.get("phone"),
            "contact": header_info,
            "experience": [],
            "education": [],
            "skills": {"technical": [], "languages": [], "tools": [], "frameworks": []},
            "projects": [],
            "certifications": [],
            "languages": [],
            "leadership_signals": [],
            "metrics_extracted": []
        }
        
        # Extract text from sections
        for section_name, blocks in sections.items():
            section_text = "\n".join(
                self._extract_text_from_block(block)
                for block in blocks
            )
            
            if section_name == "skills":
                # Basic skills extraction - handle comma, semicolon, pipe separated
                skills = []
                for separator in [",", ";", "|", "\n"]:
                    if separator in section_text:
                        skills.extend([s.strip() for s in section_text.split(separator) if s.strip() and len(s.strip()) > 2])
                        break
                if not skills:
                    # Try space-separated if no other separator
                    skills = [s.strip() for s in section_text.split() if s.strip() and len(s.strip()) > 2]
                normalized["skills"]["technical"] = list(set(skills))  # Remove duplicates
            
            elif section_name == "experience":
                # Basic experience extraction - look for job titles and companies
                import re
                lines = section_text.split('\n')
                current_exp = {}
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_exp:
                            normalized["experience"].append(current_exp)
                            current_exp = {}
                        continue
                    
                    # Look for date patterns
                    date_match = re.search(r'(\d{4}|\w+\s+\d{4})\s*[-–—]\s*(\d{4}|\w+\s+\d{4}|present|current)', line, re.IGNORECASE)
                    if date_match:
                        current_exp["start_date"] = date_match.group(1)
                        current_exp["end_date"] = date_match.group(2).lower() if date_match.group(2).lower() in ["present", "current"] else date_match.group(2)
                    
                    # Look for job titles (common patterns)
                    if not current_exp.get("title"):
                        title_match = re.search(r'\b(?:Senior|Junior|Lead|Principal|Staff|Associate|Full\s+Stack|Backend|Frontend|DevOps|Data|ML|AI|Cloud|Systems|Product|Project|Business|Technical|QA|Test)\s+[A-Z][a-z]+', line, re.IGNORECASE)
                        if title_match:
                            current_exp["title"] = line
                    
                    # Look for company names
                    if not current_exp.get("company"):
                        company_match = re.search(r'\b(?:Pvt|Ltd|LLC|Inc|Corp|Corporation|Technologies|Solutions|Services|Systems|Group|Company|Co)\b', line, re.IGNORECASE)
                        if company_match:
                            current_exp["company"] = line
                    
                    # Description
                    if "description" not in current_exp:
                        current_exp["description"] = line
                    else:
                        current_exp["description"] += " " + line
                
                if current_exp:
                    normalized["experience"].append(current_exp)
            
            elif section_name == "education":
                # Basic education extraction
                import re
                lines = section_text.split('\n')
                current_edu = {}
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_edu:
                            normalized["education"].append(current_edu)
                            current_edu = {}
                        continue
                    
                    # Look for degree keywords
                    if not current_edu.get("degree"):
                        degree_match = re.search(r'\b(?:Bachelor|Master|PhD|Ph\.D|Doctorate|MBA|MCA|BSc|MSc|BTech|MTech|Degree|Diploma|Certificate)\b', line, re.IGNORECASE)
                        if degree_match:
                            current_edu["degree"] = line
                    
                    # Look for institution keywords
                    if not current_edu.get("institution"):
                        inst_match = re.search(r'\b(?:University|College|Institute|School|Academy)\b', line, re.IGNORECASE)
                        if inst_match:
                            current_edu["institution"] = line
                    
                    # Look for year
                    if not current_edu.get("year"):
                        year_match = re.search(r'\b(19|20)\d{2}\b', line)
                        if year_match:
                            current_edu["year"] = year_match.group(0)
                
                if current_edu:
                    normalized["education"].append(current_edu)
        
        return normalized
    
    def _create_text_blocks_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Create text blocks from raw text for section detection when LayoutLM is not available
        Improved version that better handles section headers and multi-line content"""
        import re
        lines = text.split('\n')
        blocks = []
        current_y = 0
        
        # Section header patterns (uppercase, short lines)
        section_header_pattern = re.compile(
            r'^(?:WORK\s+)?EXPERIENCE|EDUCATION|SKILLS|PROJECTS?|CERTIFICATIONS?|LANGUAGES?|'
            r'CONTACT|PROFILE\s+SUMMARY|SUMMARY|OBJECTIVE|ACHIEVEMENTS?|AWARDS?|INTERESTS?|'
            r'REFERENCES?|TECHNICAL\s+SKILLS?|COMPETENCIES?|EXPERIENCE|PROFESSIONAL\s+EXPERIENCE'
            r'|EMPLOYMENT|CAREER|WORK\s+HISTORY)$',
            re.IGNORECASE
        )
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                current_y += 20
                i += 1
                continue
            
            # Check if this line is a section header
            is_section_header = (
                section_header_pattern.match(line) or
                (line.isupper() and len(line) < 50 and len(line.split()) <= 3)
            )
            
            if is_section_header:
                # Section header block
                blocks.append({
                    "tokens": [{"token": line, "bbox": [0, current_y, 200, current_y + 20]}],
                    "y_position": current_y,
                    "text": line,
                    "is_section_header": True
                })
                current_y += 30
                i += 1
                
                # Collect content until next section header or empty line
                content_lines = []
                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line:
                        if content_lines:
                            break
                        i += 1
                        current_y += 10
                        continue
                    
                    # Check if next section header
                    if section_header_pattern.match(next_line) or (next_line.isupper() and len(next_line) < 50):
                        break
                    
                    content_lines.append(next_line)
                    i += 1
                
                # Create content block
                if content_lines:
                    content_text = "\n".join(content_lines)
                    tokens = [{"token": cl, "bbox": [0, current_y, 500, current_y + 20]} for cl in content_lines]
                    blocks.append({
                        "tokens": tokens,
                        "y_position": current_y,
                        "text": content_text,
                        "is_section_header": False
                    })
                    current_y += len(content_lines) * 25
            else:
                # Regular content line
                blocks.append({
                    "tokens": [{"token": line, "bbox": [0, current_y, 500, current_y + 20]}],
                    "y_position": current_y,
                    "text": line,
                    "is_section_header": False
                })
                current_y += 25
                i += 1
        
        return blocks
    
    def _extract_text_from_block(self, block: Dict[str, Any]) -> str:
        """Extract text from a text block"""
        if "text" in block:
            return block["text"]
        if "tokens" in block:
            tokens = block["tokens"]
            if isinstance(tokens, list):
                if isinstance(tokens[0], dict):
                    return " ".join(t.get("token", "") for t in tokens)
                else:
                    return " ".join(str(t) for t in tokens)
        return block.get("text", "")

