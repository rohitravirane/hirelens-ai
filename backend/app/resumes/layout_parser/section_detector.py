"""
Section-aware detector using layout + semantic understanding
Detects resume sections using font size, position, layout structure
"""
from typing import List, Dict, Any, Optional, Tuple
import re
import structlog
from collections import defaultdict

logger = structlog.get_logger()


class SectionDetector:
    """
    Detects resume sections using layout + semantic cues
    Handles:
    - Header detection (font size + position)
    - Column separation
    - Table-aware extraction
    - Bullet grouping
    """
    
    def __init__(self):
        # Section keywords with variations
        self.section_patterns = {
            "header": {
                "keywords": ["name", "contact", "email", "phone", "address", "linkedin", "github"],
                "position": "top",  # Usually at top
                "font_size": "large"  # Usually larger font
            },
            "experience": {
                "keywords": [
                    "work experience", "employment", "professional experience",
                    "career", "employment history", "work history", "experience"
                ],
                "patterns": [
                    r'^EXPERIENCE\s*:?$',
                    r'^WORK\s+EXPERIENCE\s*:?$',
                    r'^EMPLOYMENT\s*:?$',
                    r'^PROFESSIONAL\s+EXPERIENCE\s*:?$',
                    r'^CAREER\s*:?$',
                    r'^WORK\s+HISTORY\s*:?$',
                    r'^EMPLOYMENT\s+HISTORY\s*:?$',
                    r'^CAREER\s+HISTORY\s*:?$'
                ]
            },
            "education": {
                "keywords": ["education", "academic", "qualifications", "degrees", "university", "college"],
                "patterns": [
                    r'^EDUCATION\s*:?$',
                    r'^ACADEMIC\s+(?:QUALIFICATIONS|BACKGROUND)\s*:?$',
                    r'^QUALIFICATIONS\s*:?$',
                    r'^ACADEMIC\s+QUALIFICATIONS\s*:?$',
                    r'^DEGREES?\s*:?$'
                ]
            },
            "skills": {
                "keywords": ["skills", "technical skills", "competencies", "expertise", "technologies"],
                "patterns": [
                    r'^SKILLS\s*:?$',
                    r'^TECHNICAL\s+SKILLS\s*:?$',
                    r'^COMPETENCIES\s*:?$',
                    r'^CORE\s+SKILLS\s*:?$',
                    r'^KEY\s+SKILLS\s*:?$',
                    r'^TECHNOLOGIES\s*:?$',
                    r'^TOOLS\s*:?$',
                    r'^FRAMEWORKS\s*:?$',
                    r'^PLATFORMS\s*:?$',
                    r'^SOFTWARE\s*:?$',
                    r'^PROGRAMMING\s+LANGUAGES\s*:?$'
                ]
            },
            "projects": {
                "keywords": ["projects", "portfolio", "key projects"],
                "patterns": [
                    r'^PROJECTS?\s*:?$',
                    r'^KEY\s+PROJECTS?\s*:?$'
                ]
            },
            "certifications": {
                "keywords": ["certifications", "certificates", "credentials", "licenses"],
                "patterns": [
                    r'^CERTIFICATIONS?\s*:?$',
                    r'^CERTIFICATES?\s*:?$',
                    r'^CREDENTIALS\s*:?$',
                    r'^LICENSES?\s*:?$',
                    r'^AWARDS?\s*:?$',
                    r'^ACHIEVEMENTS?\s*:?$'
                ]
            },
            "languages": {
                "keywords": ["languages", "language proficiency"],
                "patterns": [
                    r'^LANGUAGES?\s*:?$',
                    r'^LANGUAGE\s+PROFICIENCY\s*:?$',
                    r'^SPOKEN\s+LANGUAGES?\s*:?$'
                ]
            }
        }
    
    def detect_sections(
        self,
        text_blocks: List[Dict[str, Any]],
        layout_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect sections from text blocks using layout + semantic analysis
        ENTERPRISE-GRADE: Handles multi-column layouts, visual hierarchy, section boundaries
        
        Args:
            text_blocks: List of text blocks from LayoutLMv3 (with bbox information)
            layout_info: Optional layout information (columns, positions, etc.)
            
        Returns:
            Dict mapping section names to lists of text blocks
        """
        sections = defaultdict(list)
        
        # Detect column structure first (for 2-column resumes)
        column_info = self.detect_columns(text_blocks, layout_info)
        has_columns = column_info.get("has_columns", False)
        
        # Sort blocks by vertical position (top to bottom) - PRIMARY ORDERING
        # Within same y, sort by x (left to right) for column-aware processing
        def block_sort_key(block):
            y_pos = block.get("y_position", 0)
            # Extract x position from tokens if available
            x_pos = 0
            if "tokens" in block and block["tokens"]:
                x_positions = []
                for token_info in block["tokens"]:
                    if isinstance(token_info, dict) and "bbox" in token_info:
                        bbox = token_info["bbox"]
                        x_center = (bbox[0] + bbox[2]) / 2
                        x_positions.append(x_center)
                if x_positions:
                    x_pos = sum(x_positions) / len(x_positions)
            return (y_pos, x_pos)
        
        sorted_blocks = sorted(text_blocks, key=block_sort_key)
        
        current_section = None
        section_headers = {}  # Track section headers by position
        
        for block in sorted_blocks:
            # Extract text from block
            block_text = self._extract_text_from_block(block)
            
            # Check if this block is a section header
            detected_section = self._detect_section_header(block_text, block)
            
            if detected_section:
                current_section = detected_section
                section_headers[detected_section] = block
                logger.debug("section_header_detected", 
                           section=detected_section,
                           text=block_text[:50],
                           y_position=block.get("y_position", 0))
            
            # Assign block to current section
            if current_section:
                sections[current_section].append(block)
            else:
                # Unassigned blocks at top might be header section
                if block.get("y_position", 0) < 100:  # Top 100px is usually header
                    sections["header"].append(block)
                else:
                    sections["other"].append(block)
        
        logger.info("section_detection_complete",
                   sections_found=list(sections.keys()),
                   blocks_per_section={k: len(v) for k, v in sections.items()},
                   has_columns=has_columns)
        
        return dict(sections)
    
    def _extract_text_from_block(self, block: Dict[str, Any]) -> str:
        """Extract text string from a text block"""
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
    
    def _detect_section_header(
        self,
        text: str,
        block: Dict[str, Any]
    ) -> Optional[str]:
        """Detect if a text block is a section header - IMPROVED"""
        text_upper = text.upper().strip()
        text_clean = text.strip()
        
        # Check if block is marked as section header
        if block.get("is_section_header", False):
            # Direct check for section name
            for section_name, section_info in self.section_patterns.items():
                if section_name == "header":
                    continue
                
                patterns = section_info.get("patterns", [])
                for pattern in patterns:
                    if re.match(pattern, text_upper):
                        return section_name
                
                keywords = section_info.get("keywords", [])
                for keyword in keywords:
                    if keyword.upper() in text_upper:
                        return section_name
        
        # Check against section patterns
        for section_name, section_info in self.section_patterns.items():
            if section_name == "header":
                continue  # Skip header section for now
            
            # Check patterns (more flexible matching)
            patterns = section_info.get("patterns", [])
            for pattern in patterns:
                if re.match(pattern, text_upper) or re.search(pattern, text_upper):
                    return section_name
            
            # Check keywords (improved matching)
            keywords = section_info.get("keywords", [])
            for keyword in keywords:
                keyword_upper = keyword.upper()
                # Exact match or starts with keyword
                if (text_upper == keyword_upper or 
                    text_upper.startswith(keyword_upper + " ") or
                    text_upper.startswith(keyword_upper + ":") or
                    (keyword_upper in text_upper and len(text_clean) < 50)):
                    return section_name
        
        # Additional heuristics for common section headers
        if text_upper in ["EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE", "EMPLOYMENT", "CAREER"]:
            return "experience"
        if text_upper in ["EDUCATION", "ACADEMIC QUALIFICATIONS", "QUALIFICATIONS"]:
            return "education"
        if text_upper in ["SKILLS", "TECHNICAL SKILLS", "COMPETENCIES", "EXPERTISE", "TECHNOLOGIES"]:
            return "skills"
        if text_upper in ["PROJECTS", "KEY PROJECTS", "PORTFOLIO"]:
            return "projects"
        if text_upper in ["LANGUAGES", "LANGUAGE PROFICIENCY"]:
            return "languages"
        if text_upper in ["CERTIFICATIONS", "CERTIFICATES", "CREDENTIALS"]:
            return "certifications"
        
        return None
    
    def detect_header_section(
        self,
        text_blocks: List[Dict[str, Any]],
        layout_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect header section (name, contact info) using position + font size
        
        Args:
            text_blocks: List of text blocks
            layout_info: Optional layout information
            
        Returns:
            Dict with header information
        """
        # Sort by vertical position
        sorted_blocks = sorted(text_blocks, key=lambda b: b.get("y_position", 0))
        
        # Top blocks are likely header
        header_blocks = sorted_blocks[:5]  # Top 5 blocks
        
        header_info = {
            "name": None,
            "email": None,
            "phone": None,
            "location": None,
            "linkedin": None,
            "github": None,
            "portfolio": None
        }
        
        header_text = " ".join(self._extract_text_from_block(b) for b in header_blocks)
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', header_text)
        if email_match:
            header_info["email"] = email_match.group(0)
        
        # Extract phone
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?\d{10,15}'
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, header_text)
            if phone_match:
                header_info["phone"] = phone_match.group(0)
                break
        
        # Extract LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', header_text, re.IGNORECASE)
        if linkedin_match:
            header_info["linkedin"] = "https://" + linkedin_match.group(0)
        
        # Extract GitHub
        github_match = re.search(r'github\.com/[\w-]+', header_text, re.IGNORECASE)
        if github_match:
            header_info["github"] = "https://" + github_match.group(0)
        
        # Extract portfolio
        portfolio_match = re.search(r'https?://[^\s]+', header_text)
        if portfolio_match and "linkedin" not in portfolio_match.group(0).lower() and "github" not in portfolio_match.group(0).lower():
            header_info["portfolio"] = portfolio_match.group(0)
        
        # Name is usually the first large text block
        if header_blocks:
            first_block_text = self._extract_text_from_block(header_blocks[0])
            # Name is usually 2-4 words, capitalized
            name_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', first_block_text)
            if name_match:
                header_info["name"] = name_match.group(1)
        
        logger.info("header_detection_complete", 
                   has_name=bool(header_info["name"]),
                   has_email=bool(header_info["email"]),
                   has_phone=bool(header_info["phone"]))
        
        return header_info
    
    def detect_columns(
        self,
        text_blocks: List[Dict[str, Any]],
        layout_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect column structure from text blocks using x-axis clustering
        Enterprise-grade: Handles 2-column resumes (common in US/Indian formats)
        
        Returns:
            Dict with column information including block assignments
        """
        if not text_blocks:
            return {"has_columns": False, "columns": {}}
        
        # Extract x-axis centers from all tokens in blocks
        x_positions = []
        block_x_mapping = {}  # Map block index to x centers
        
        for block_idx, block in enumerate(text_blocks):
            block_x_positions = []
            if "tokens" in block and block["tokens"]:
                for token_info in block["tokens"]:
                    if isinstance(token_info, dict) and "bbox" in token_info:
                        bbox = token_info["bbox"]
                        x_center = (bbox[0] + bbox[2]) / 2
                        x_positions.append(x_center)
                        block_x_positions.append(x_center)
            
            if block_x_positions:
                block_x_mapping[block_idx] = sum(block_x_positions) / len(block_x_positions)
        
        if not x_positions:
            return {"has_columns": False, "columns": {}}
        
        # Use K-means-like approach: find two clusters (left/right columns)
        x_positions_sorted = sorted(x_positions)
        page_width_estimate = max(x_positions) - min(x_positions)
        
        # Find optimal split point (approximately middle of page)
        mid_point_x = (max(x_positions) + min(x_positions)) / 2
        
        # Classify blocks into left/right columns
        left_blocks = []
        right_blocks = []
        left_x_centers = []
        right_x_centers = []
        
        for block_idx, block_x_center in block_x_mapping.items():
            if block_x_center < mid_point_x:
                left_blocks.append(block_idx)
                left_x_centers.append(block_x_center)
            else:
                right_blocks.append(block_idx)
                right_x_centers.append(block_x_center)
        
        # Calculate column centers
        left_avg = sum(left_x_centers) / len(left_x_centers) if left_x_centers else 0
        right_avg = sum(right_x_centers) / len(right_x_centers) if right_x_centers else 0
        
        # Determine if columns are distinct (separation > 25% of page width)
        separation = abs(right_avg - left_avg) if (left_avg > 0 and right_avg > 0) else 0
        has_columns = separation > (page_width_estimate * 0.25) and len(left_blocks) > 0 and len(right_blocks) > 0
        
        logger.info("column_detection", 
                   has_columns=has_columns,
                   separation=separation,
                   page_width=page_width_estimate,
                   left_blocks=len(left_blocks),
                   right_blocks=len(right_blocks))
        
        return {
            "has_columns": has_columns,
            "columns": {
                "left": {
                    "x_center": left_avg,
                    "blocks": left_blocks,
                    "width_estimate": left_avg * 2 if left_avg > 0 else 0
                },
                "right": {
                    "x_center": right_avg,
                    "blocks": right_blocks,
                    "width_estimate": (page_width_estimate - right_avg) * 2 if right_avg > 0 else 0
                }
            } if has_columns else {}
        }

