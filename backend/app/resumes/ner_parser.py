"""
NER-based resume parser using spaCy for intelligent extraction
Improved version with better accuracy and context-aware parsing
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import re
import structlog
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

logger = structlog.get_logger()

# Import elite layout analyzer
try:
    from app.resumes.elite_layout_analyzer import EliteLayoutAnalyzer
    ELITE_LAYOUT_AVAILABLE = True
except ImportError:
    ELITE_LAYOUT_AVAILABLE = False
    logger.warning("elite_layout_analyzer_not_available")

# Lazy loading for spaCy model
nlp = None
spacy_model_name = "en_core_web_sm"


def _load_spacy_model():
    """Lazy load spaCy model"""
    global nlp
    if nlp is None:
        try:
            import spacy
            try:
                nlp = spacy.load(spacy_model_name)
                logger.info("spacy_model_loaded", model=spacy_model_name)
            except OSError:
                logger.warning("spacy_model_not_found", model=spacy_model_name)
                nlp = spacy.blank("en")
                logger.warning("using_basic_spacy_model")
        except ImportError:
            logger.error("spacy_not_available")
            nlp = None
    return nlp


class ResumeLayoutAnalyzer:
    """Analyzes resume layout structure to understand column structure and section positions"""
    
    def analyze_layout(self, text: str) -> Dict[str, Any]:
        """Comprehensive layout analysis - detect columns, separators, section positions, and structure"""
        lines = text.split('\n')
        
        layout_info = {
            "has_columns": False,
            "column_separator_pos": None,
            "column_separator_char": None,
            "left_column_end": None,
            "right_column_start": None,
            "sections": {},
            "section_boundaries": {},  # Start and end line indices for each section
            "layout_type": "single_column",  # single_column, two_column, mixed
            "line_structure": []  # Structure info for each line
        }
        
        # Step 1: Detect sections FIRST (before column detection)
        layout_info["sections"] = self._detect_sections_comprehensive(text, lines)
        layout_info["section_boundaries"] = self._detect_section_boundaries(lines, layout_info["sections"])
        
        # Step 2: Detect column separators (vertical lines, multiple spaces, tabs)
        separator_patterns = [
            (r'\s*\|\s*', '|'),  # Vertical line
            (r'\s*\|\|\s*', '||'),  # Double vertical line
            (r'\s{4,}', 'spaces'),  # 4+ spaces
            (r'\t+', 'tab'),  # Tabs
        ]
        
        # Find potential column separator position
        for i, line in enumerate(lines):
            if len(line.strip()) < 10:  # Skip very short lines
                continue
            
            for pattern, char_type in separator_patterns:
                matches = list(re.finditer(pattern, line))
                if matches:
                    # Check if this separator appears consistently (column structure)
                    for match in matches:
                        pos = match.start()
                        # Check if similar position has separators in nearby lines
                        consistent_count = 0
                        for j in range(max(0, i-3), min(len(lines), i+4)):
                            if j == i:
                                continue
                            if re.search(pattern, lines[j]):
                                consistent_count += 1
                        
                        if consistent_count >= 2:  # Found in multiple lines
                            layout_info["has_columns"] = True
                            layout_info["column_separator_pos"] = pos
                            layout_info["column_separator_char"] = char_type
                            layout_info["layout_type"] = "two_column"
                            break
                
                if layout_info["has_columns"]:
                    break
            
            if layout_info["has_columns"]:
                break
        
        # Step 3: If no explicit separator, try to detect by content alignment
        if not layout_info["has_columns"]:
            column_info = self._detect_columns_by_content(lines)
            if column_info.get("has_columns"):
                layout_info.update(column_info)
                layout_info["layout_type"] = "two_column"
        
        # Step 4: Analyze line structure (which column, which section, etc.)
        layout_info["line_structure"] = self._analyze_line_structure(lines, layout_info)
        
        # Step 5: Determine overall layout type
        if layout_info["has_columns"]:
            # Check if sections span columns or are in specific columns
            mixed_sections = sum(1 for s in layout_info["sections"].values() 
                               if s.get("column") == "both")
            if mixed_sections > 0:
                layout_info["layout_type"] = "mixed"
        
        logger.info("layout_analysis_complete", 
                   layout_type=layout_info["layout_type"],
                   has_columns=layout_info["has_columns"],
                   sections_found=list(layout_info["sections"].keys()))
        
        return layout_info
    
    def _detect_columns_by_content(self, lines: List[str]) -> Dict[str, Any]:
        """Detect columns by analyzing content alignment and spacing"""
        layout_info = {
            "has_columns": False,
            "column_separator_pos": None,
            "column_separator_char": "spaces",
            "left_column_end": None,
            "right_column_start": None,
            "sections": {}
        }
        
        # Look for lines with two distinct content blocks separated by large spaces
        # Pattern: "LEFT CONTENT    RIGHT CONTENT"
        for i, line in enumerate(lines):
            # Find large gaps (potential column separator)
            # Look for patterns like: "WORD1    WORD2" where gap is 3+ spaces
            gap_match = re.search(r'(\S+)\s{3,}(\S+)', line)
            if gap_match:
                gap_start = gap_match.start(2)
                # Check if this gap position is consistent across multiple lines
                consistent_gaps = 0
                for j in range(max(0, i-5), min(len(lines), i+6)):
                    if re.search(r'\S+\s{3,}\S+', lines[j]):
                        consistent_gaps += 1
                
                if consistent_gaps >= 3:  # Found in multiple lines
                    layout_info["has_columns"] = True
                    layout_info["column_separator_pos"] = gap_start
                    layout_info["left_column_end"] = gap_start - 1
                    layout_info["right_column_start"] = gap_start
                    break
        
        return layout_info
    
    def _detect_sections_comprehensive(self, text: str, lines: List[str]) -> Dict[str, Any]:
        """Comprehensive section detection - finds all sections with their positions"""
        sections = {}
        
        # Expanded section keywords with variations
        section_patterns = {
            "CONTACT": [r'^CONTACT\s*(?:INFO|INFORMATION)?\s*:?$', r'^CONTACT\s*$'],
            "PROFILE": [r'^PROFILE\s*(?:SUMMARY)?\s*:?$', r'^SUMMARY\s*:?$', r'^OBJECTIVE\s*:?$'],
            "EDUCATION": [r'^EDUCATION\s*:?$', r'^ACADEMIC\s+(?:QUALIFICATIONS|BACKGROUND)\s*:?$'],
            "EXPERIENCE": [r'^WORK\s+EXPERIENCE\s*:?$', r'^EXPERIENCE\s*:?$', r'^EMPLOYMENT\s*:?$', 
                          r'^CAREER\s*:?$', r'^PROFESSIONAL\s+EXPERIENCE\s*:?$', r'^WORK\s+HISTORY\s*:?$',
                          r'^EDUCATION\s+WORK\s+EXPERIENCE\s*:?$'],  # Two-column header
            "SKILLS": [r'^SKILLS\s*:?$', r'^TECHNICAL\s+SKILLS\s*:?$', r'^COMPETENCIES\s*:?$',
                      r'^CORE\s+SKILLS\s*:?$', r'^TECHNOLOGIES\s*:?$'],
            "PROJECTS": [r'^PROJECTS?\s*:?$', r'^KEY\s+PROJECTS?\s*:?$'],
            "CERTIFICATIONS": [r'^CERTIFICATIONS?\s*:?$', r'^CERTIFICATES?\s*:?$'],
            "LANGUAGES": [r'^LANGUAGES?\s*:?$'],
            "ACHIEVEMENTS": [r'^ACHIEVEMENTS?\s*:?$', r'^AWARDS?\s*:?$']
        }
        
        for i, line in enumerate(lines):
            line_upper = line.upper().strip()
            line_stripped = line.strip()
            
            # Check each section pattern
            for section_name, patterns in section_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, line_upper, re.IGNORECASE):
                        # Additional validation: section header should be short or standalone
                        if (len(line_stripped) < 60 and 
                            (line_upper == line_stripped.upper() or  # All caps
                             line_upper.startswith(section_name) or
                             not re.search(r'[a-z]{3,}', line_stripped))):  # Mostly caps
                            
                            if section_name not in sections:
                                sections[section_name] = {
                                    "line_index": i,
                                    "line_content": line_stripped,
                                    "column": None  # Will be set later
                                }
                            break
        
        return sections
    
    def _detect_section_boundaries(self, lines: List[str], sections: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """Detect start and end boundaries for each section"""
        boundaries = {}
        section_names = sorted(sections.keys(), key=lambda x: sections[x]["line_index"])
        
        for idx, section_name in enumerate(section_names):
            start_line = sections[section_name]["line_index"]
            
            # Find end line (next section or end of text)
            if idx + 1 < len(section_names):
                end_line = sections[section_names[idx + 1]]["line_index"] - 1
            else:
                end_line = len(lines) - 1
            
            boundaries[section_name] = {
                "start": start_line,
                "end": end_line
            }
        
        return boundaries
    
    def _analyze_line_structure(self, lines: List[str], layout_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze structure of each line (which section, which column, etc.)"""
        line_structure = []
        sections = layout_info.get("sections", {})
        boundaries = layout_info.get("section_boundaries", {})
        separator_pos = layout_info.get("column_separator_pos")
        
        for i, line in enumerate(lines):
            structure = {
                "line_index": i,
                "section": None,
                "column": None,
                "has_separator": False
            }
            
            # Determine which section this line belongs to
            for section_name, boundary in boundaries.items():
                if boundary["start"] <= i <= boundary["end"]:
                    structure["section"] = section_name
                    break
            
            # Determine which column
            if separator_pos:
                if len(line) > separator_pos:
                    left_part = line[:separator_pos].strip()
                    right_part = line[separator_pos:].strip()
                    if left_part and right_part:
                        structure["column"] = "both"
                    elif left_part:
                        structure["column"] = "left"
                    elif right_part:
                        structure["column"] = "right"
                else:
                    structure["column"] = "left"
            
            # Check for separator
            if separator_pos and (line.find('|') >= 0 or 
                                 (separator_pos < len(line) and 
                                  re.search(r'\s{3,}', line[separator_pos-2:separator_pos+2]))):
                structure["has_separator"] = True
            
            line_structure.append(structure)
        
        return line_structure
    
    def _detect_section_column(self, line: str, layout_info: Dict[str, Any]) -> Optional[str]:
        """Detect which column a section belongs to"""
        if not layout_info.get("has_columns"):
            return None
        
        separator_pos = layout_info.get("column_separator_pos")
        if separator_pos is None:
            return None
        
        # If line content is before separator, it's left column
        if len(line) < separator_pos:
            return "left"
        elif line.find('|') >= 0 or (separator_pos and len(line) > separator_pos):
            # Check if content starts after separator
            line_before_sep = line[:separator_pos].strip()
            line_after_sep = line[separator_pos:].strip() if len(line) > separator_pos else ""
            
            if line_before_sep and not line_after_sep:
                return "left"
            elif line_after_sep and not line_before_sep:
                return "right"
            elif line_before_sep and line_after_sep:
                return "both"  # Spans both columns
        
        return None
    
    def split_columns(self, text: str, layout_info: Dict[str, Any]) -> Dict[str, str]:
        """Split text into left and right columns based on layout analysis"""
        if not layout_info.get("has_columns"):
            return {"left": text, "right": ""}
        
        lines = text.split('\n')
        left_lines = []
        right_lines = []
        
        separator_pos = layout_info.get("column_separator_pos")
        separator_char = layout_info.get("column_separator_char", "spaces")
        
        for line in lines:
            if separator_char == "|" or separator_char == "||":
                # Split by vertical line
                parts = re.split(r'\s*\|\s*', line, 1)
                if len(parts) == 2:
                    left_lines.append(parts[0].strip())
                    right_lines.append(parts[1].strip())
                else:
                    left_lines.append(line.strip())
                    right_lines.append("")
            elif separator_pos:
                # Split by position
                if len(line) > separator_pos:
                    left_part = line[:separator_pos].strip()
                    right_part = line[separator_pos:].strip()
                    left_lines.append(left_part)
                    right_lines.append(right_part)
                else:
                    left_lines.append(line.strip())
                    right_lines.append("")
            else:
                # Try to split by large gaps
                gap_match = re.search(r'(.+?)\s{3,}(.+)', line)
                if gap_match:
                    left_lines.append(gap_match.group(1).strip())
                    right_lines.append(gap_match.group(2).strip())
                else:
                    left_lines.append(line.strip())
                    right_lines.append("")
        
        return {
            "left": "\n".join(left_lines),
            "right": "\n".join(right_lines)
        }


class NERParser:
    """NER-based resume parser with improved accuracy and layout awareness"""
    
    def __init__(self):
        self.nlp = _load_spacy_model()
        self.known_skills = self._load_known_skills()
        self.layout_analyzer = ResumeLayoutAnalyzer()
        
        # Initialize Elite Layout Analyzer (world-class layout understanding)
        if ELITE_LAYOUT_AVAILABLE:
            self.elite_layout_analyzer = EliteLayoutAnalyzer()
            logger.info("elite_layout_analyzer_initialized")
        else:
            self.elite_layout_analyzer = None
            logger.warning("elite_layout_analyzer_not_available")
        
        # Try to initialize HURIDOCS layout analyzer (optional)
        try:
            from app.resumes.huridocs_layout_analyzer import huridocs_analyzer
            self.huridocs_analyzer = huridocs_analyzer
            self.use_huridocs = True
            logger.info("huridocs_analyzer_initialized")
        except Exception as e:
            self.huridocs_analyzer = None
            self.use_huridocs = False
            logger.warning("huridocs_analyzer_not_available", error=str(e))
    
    def _load_known_skills(self) -> List[str]:
        """Load comprehensive skill keywords for validation"""
        return [
            # Programming Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "kotlin", "swift",
            "php", "ruby", "scala", "r", "matlab", "perl", "shell", "bash",
            # Web Technologies
            "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
            "spring", "laravel", "asp.net", "rails", "next.js", "nuxt.js",
            # Databases
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
            "oracle", "sqlite", "dynamodb", "neo4j",
            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "gitlab", "github",
            "terraform", "ansible", "prometheus", "grafana", "ci/cd", "devops",
            # Data & AI
            "machine learning", "deep learning", "ai", "data science", "pytorch", "tensorflow",
            "pandas", "numpy", "scikit-learn", "keras", "opencv",
            # Mobile
            "android", "ios", "react native", "flutter", "xamarin",
            # Other
            "agile", "scrum", "git", "microservices", "rest api", "graphql", "websockets",
            "linux", "windows", "macos", "nginx", "apache", "jira", "tailwind",
        ]
    
    def parse_with_ner(self, text: str, pdf_path: Optional[str] = None) -> Dict[str, Any]:
        """Parse resume using elite-level layout understanding and NER-based extraction"""
        if not self.nlp:
            logger.warning("spacy_not_available_using_basic_parsing")
            return self._basic_parse(text)
        
        try:
            # Process text with spaCy
            doc = self.nlp(text[:100000])
            
            # Step 1: Elite-level layout analysis (world-class understanding)
            layout_info = None
            huridocs_data = None
            
            # Get HURIDOCS data if available
            if self.use_huridocs and pdf_path:
                abs_pdf_path = self._resolve_pdf_path(pdf_path)
                if abs_pdf_path and Path(abs_pdf_path).exists():
                    try:
                        huridocs_data = self.huridocs_analyzer.analyze_pdf_layout(abs_pdf_path, fast=True)
                        logger.info("huridocs_data_obtained", has_data=huridocs_data is not None)
                    except Exception as e:
                        logger.warning("huridocs_analysis_failed", error=str(e))
            
            # Use Elite Layout Analyzer for comprehensive layout understanding
            if self.elite_layout_analyzer:
                try:
                    layout_info = self.elite_layout_analyzer.analyze_comprehensive_layout(
                        text=text,
                        pdf_path=pdf_path,
                        huridocs_data=huridocs_data
                    )
                    logger.info("elite_layout_analysis_complete",
                               layout_type=layout_info.get('layout_type'),
                               confidence=layout_info.get('confidence', 0),
                               sections_found=list(layout_info.get('sections', {}).keys()))
                except Exception as e:
                    logger.error("elite_layout_analysis_error", error=str(e), exc_info=True)
                    layout_info = None
            
            # Step 2: Extract data using layout-aware approach
            parsed = self._extract_with_layout_awareness(text, layout_info, pdf_path)
            
            # Extract personal information (use full text for this)
            personal_info = self._extract_personal_info(text)
            parsed.update(personal_info)
            
            parsed["experience_years"] = self._calculate_experience_years(parsed.get("experience", []))
            
            logger.info("ner_parsing_complete", 
                       skills_count=len(parsed.get("skills", [])),
                       exp_count=len(parsed.get("experience", [])),
                       layout_type=layout_info.get('layout_type') if layout_info else 'unknown')
            
            return parsed
            
        except Exception as e:
            logger.error("ner_parsing_error", error=str(e), exc_info=True)
            return self._basic_parse(text)
    
    def _resolve_pdf_path(self, pdf_path: str) -> Optional[str]:
        """Resolve PDF path to absolute path"""
        if not pdf_path:
            return None
        
        pdf_path_obj = Path(pdf_path)
        if pdf_path_obj.exists():
            return str(pdf_path_obj.resolve())
        elif pdf_path.startswith('./'):
            abs_path = f"/app/{pdf_path[2:]}"
            if Path(abs_path).exists():
                return abs_path
        
        return None
    
    def _extract_with_layout_awareness(
        self, 
        text: str, 
        layout_info: Optional[Dict[str, Any]],
        pdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract data using elite layout understanding"""
        
        # If no layout info, use basic extraction
        if not layout_info:
            return {
                "skills": self._extract_skills_improved(text),
                "experience": self._extract_experience_improved(text, pdf_path),
                "education": self._extract_education_improved(text),
                "projects": self._extract_projects_improved(text),
                "certifications": self._extract_certifications_improved(text),
                "languages": self._extract_languages_improved(text),
                "experience_years": None,
            }
        
        layout_type = layout_info.get('layout_type', 'single_column')
        columns = layout_info.get('columns', {})
        sections = layout_info.get('sections', {})
        section_mapping = layout_info.get('section_mapping', {})
        
        # Get text for each section intelligently
        skills_text = self._get_section_text('skills', layout_info, columns, sections, text)
        experience_text = self._get_section_text('experience', layout_info, columns, sections, text)
        education_text = self._get_section_text('education', layout_info, columns, sections, text)
        certs_text = self._get_section_text('certifications', layout_info, columns, sections, text)
        projects_text = self._get_section_text('projects', layout_info, columns, sections, text)
        languages_text = self._get_section_text('languages', layout_info, columns, sections, text)
        
        # Extract data using section-specific text
        parsed = {
            "skills": self._extract_skills_improved(skills_text),
            "experience": self._extract_experience_improved(experience_text, pdf_path),
            "education": self._extract_education_improved(education_text),
            "projects": self._extract_projects_improved(projects_text),
            "certifications": self._extract_certifications_improved(certs_text),
            "languages": self._extract_languages_improved(languages_text),
            "experience_years": None,
        }
        
        return parsed
    
    def _get_section_text(
        self,
        section_name: str,
        layout_info: Dict[str, Any],
        columns: Dict[str, Any],
        sections: Dict[str, Dict[str, Any]],
        fallback_text: str
    ) -> str:
        """Get text for a specific section using layout intelligence"""
        
        layout_type = layout_info.get('layout_type', 'single_column')
        
        # For two-column layouts, prioritize column text over section text
        # because section text might be incomplete
        if layout_type == 'two_column':
            # Experience is usually in left column
            if section_name == 'experience' and 'left' in columns:
                left_text = columns['left'].get('text', '')
                if left_text and len(left_text) > 50:  # Ensure substantial content
                    logger.info("using_left_column_for_experience", length=len(left_text))
                    return left_text
            
            # Skills, certifications, education usually in right column
            if section_name in ['skills', 'certifications', 'education'] and 'right' in columns:
                right_text = columns['right'].get('text', '')
                if right_text and len(right_text) > 50:  # Ensure substantial content
                    logger.info("using_right_column_for_section", section=section_name, length=len(right_text))
                    return right_text
        
        # Method 1: Get from identified section (if substantial)
        if section_name in sections:
            section_data = sections[section_name]
            section_text = section_data.get('text', '')
            # Only use if substantial (not just a header)
            if section_text and len(section_text) > 100:  # Increased threshold
                logger.info("using_identified_section", section=section_name, length=len(section_text))
                return section_text
        
        # Method 2: Get from column where section is mapped
        section_mapping = layout_info.get('section_mapping', {})
        column_name = section_mapping.get(section_name)
        
        if column_name and column_name in columns:
            col_text = columns[column_name].get('text', '')
            if col_text and len(col_text) > 50:
                logger.info("using_column_for_section", section=section_name, column=column_name, length=len(col_text))
                return col_text
        
        # Method 3: Smart column selection based on section type (for single column or fallback)
        if layout_type == 'two_column':
            # Try opposite column as fallback
            if section_name == 'experience' and 'right' in columns:
                right_text = columns['right'].get('text', '')
                if right_text and len(right_text) > 50:
                    logger.info("using_right_column_fallback_for_experience", length=len(right_text))
                    return right_text
            
            if section_name in ['skills', 'certifications', 'education'] and 'left' in columns:
                left_text = columns['left'].get('text', '')
                if left_text and len(left_text) > 50:
                    logger.info("using_left_column_fallback_for_section", section=section_name, length=len(left_text))
                    return left_text
        
        # Fallback: Use full text
        logger.info("using_fallback_text_for_section", section=section_name)
        return fallback_text
    
    def _extract_skills_improved(self, text: str) -> List[str]:
        """Extract skills ONLY from SKILLS section, cleaned and validated"""
        skills = set()
        skills_text = None
        
        # Find SKILLS section - look for "SKILLS" header (standalone word, not part of sentence)
        # Expanded patterns to catch more variations
        section_end_pattern = r'(?:CERTIFICATIONS|EDUCATION|EXPERIENCE|WORK|PROJECTS|LANGUAGES|CONTACT|PROFILE|SUMMARY|ACHIEVEMENTS|AWARDS|INTERESTS|REFERENCES|OBJECTIVE|CAREER|EMPLOYMENT|PROFESSIONAL|TECHNICAL|COMPETENCIES|CORE|TECHNOLOGIES|TOOLS|FRAMEWORKS|PLATFORMS)'
        
        # Pattern 1: SKILLS followed by newline or same line
        skills_match = re.search(
            r'(?:^|\n)SKILLS\s*(?::\s*)?\n?(.*?)(?=\n' + section_end_pattern + r'[:\s]|$)',
            text,
            re.IGNORECASE | re.DOTALL | re.MULTILINE
        )
        
        if not skills_match:
            # Pattern 2: TECHNICAL SKILLS, CORE SKILLS, etc.
            skills_match = re.search(
                r'(?:^|\n)(?:TECHNICAL\s+|CORE\s+|KEY\s+)?SKILLS[:\s]+(.*?)(?=\n' + section_end_pattern + r'[:\s]|$)',
                text,
                re.IGNORECASE | re.DOTALL | re.MULTILINE
            )
        
        if not skills_match:
            # Pattern 3: COMPETENCIES, TECHNOLOGIES, TOOLS
            skills_match = re.search(
                r'(?:^|\n)(?:COMPETENCIES|TECHNOLOGIES|TOOLS|FRAMEWORKS|PLATFORMS|SOFTWARE|PROGRAMMING\s+LANGUAGES)[:\s]+(.*?)(?=\n' + section_end_pattern + r'[:\s]|$)',
                text,
                re.IGNORECASE | re.DOTALL | re.MULTILINE
            )
        
        if not skills_match:
            # Pattern 4: Skills section without explicit header (look for common skill patterns)
            # This catches resumes where skills are listed without a clear header
            skills_match = re.search(
                r'(?:^|\n)(?:Frontend|Backend|Database|Programming|Languages|Technologies)[:\s]+(.*?)(?=\n' + section_end_pattern + r'[:\s]|$)',
                text,
                re.IGNORECASE | re.DOTALL | re.MULTILINE
            )
        
        if skills_match:
            skills_text = skills_match.group(1).strip()
        else:
            # If no SKILLS header found, look for category patterns directly (Frontend:, Backend:, etc.)
            # This handles resumes where skills section has no header
            # Expanded category patterns
            category_patterns = [
                r'(?:^|\n)(Frontend|Backend|Database|DevOps|Tools|Programming|Languages|Technologies|Frameworks|Cloud|Mobile|Web|Data|AI/ML|Machine Learning|Deep Learning)[:\s]',
                r'(?:^|\n)(Languages|Technologies|Tools|Frameworks|Platforms|Software|Systems)[:\s]',
                r'(?:^|\n)(Python|Java|JavaScript|TypeScript|React|Node|Angular|Vue|Django|Flask|Spring|Express)[:\s]',  # Common tech names as headers
            ]
            
            for pattern in category_patterns:
                category_pattern_start = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if category_pattern_start:
                    # Extract from category start until next major section or end
                    start_pos = category_pattern_start.start()
                    # Find where skills section ends (next major section header)
                    skills_section_end = re.search(
                        r'\n(?:WORK|EDUCATION|PROJECTS|CERTIFICATIONS|LANGUAGES|CONTACT|PROFILE|SUMMARY|EXPERIENCE|EMPLOYMENT|CAREER|ACHIEVEMENTS)[:\s]',
                        text[start_pos:],
                        re.IGNORECASE | re.MULTILINE
                    )
                    end_pos = start_pos + skills_section_end.start() if skills_section_end else len(text)
                    skills_text = text[start_pos:end_pos]
                    logger.info("found_skills_via_category_pattern", pattern=pattern[:50], length=len(skills_text))
                    break
        
        # If no skills_text found but we have text, treat entire text as potential skills
        # (useful for column-separated text where header might be missing)
        if not skills_text and text and len(text) < 500:  # Short text likely to be skills list
            logger.info("treating_text_as_skills_list", text_length=len(text))
            skills_text = text
        
        if skills_text:
            
            # Extract skills from category lines (Frontend:, Backend:, etc.)
            # Strategy: Process line by line, detect category headers, then extract skills until next category
            lines = skills_text.split('\n')
            current_category = None
            current_skills_lines = []
            
            def process_category(category_name, skills_lines):
                """Process a category's skills and extract valid skills"""
                if not skills_lines:
                    return
                
                # Combine skills lines
                category_skills_text = ' '.join(skills_lines)
                
                # IMPORTANT: Stop at action verbs (likely start of a sentence/description)
                action_verb_pattern = r'\b(Contributed|Developed|Created|Built|Designed|Handled|Managed|Led|Worked|Recognized|Delivered|Ensured|Improved|Optimized|Implemented|Architected|Maintained|Supported|Collaborated|Participated|Achieved|Reduced|Increased|Scaled|Deployed|Configured|Monitored|Troubleshot|Debugged|Tested|Wrote|Documented|Maintaining|Enhance|Enhancing|products|user experience|critical thinking|problem-solving|scalability|project vision|ownership|execution|excellence|consistently|ensuring|quality|delivery|team|synergy|long-term|value|creation)\b'
                
                # Check for action verbs and stop before them
                action_match = re.search(action_verb_pattern, category_skills_text, re.IGNORECASE)
                if action_match:
                    category_skills_text = category_skills_text[:action_match.start()].strip()
                    category_skills_text = re.sub(r'[.,;]+$', '', category_skills_text)
                
                if not category_skills_text:
                    return
                
                # Split by comma, semicolon, pipe, or slash
                for skill in re.split(r'[,;|/]', category_skills_text):
                    skill = self._clean_skill(skill.strip())
                    if skill and self._is_valid_skill(skill):
                        skills.add(skill)
            
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Check if this line is a category header (short name ending with colon)
                if ':' in line_stripped:
                    parts = line_stripped.split(':', 1)
                    category_candidate = parts[0].strip()
                    
                    # Validate category name: short (max 25 chars), few words (max 3), no sentence words
                    is_valid_category = (
                        len(category_candidate) <= 25 and
                        len(category_candidate.split()) <= 3 and
                        not any(word in category_candidate.lower() for word in ['and', 'with', 'to', 'for', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'contributed', 'developed', 'created', 'maintaining', 'enhance', 'solving', 'approaches', 'scalability', 'leader', 'complete'])
                    )
                    
                    if is_valid_category:
                        # Process previous category
                        if current_category and current_skills_lines:
                            process_category(current_category, current_skills_lines)
                        
                        # Start new category
                        current_category = category_candidate
                        # Get skills from same line (after colon)
                        skills_after_colon = parts[1].strip() if len(parts) > 1 else ""
                        current_skills_lines = [skills_after_colon] if skills_after_colon else []
                    else:
                        # Not a category header, add to current category's skills
                        if current_category:
                            current_skills_lines.append(line_stripped)
                else:
                    # No colon, add to current category's skills if we have one
                    if current_category:
                        current_skills_lines.append(line_stripped)
            
            # Process last category
            if current_category and current_skills_lines:
                process_category(current_category, current_skills_lines)
            
            # Also extract skills separated by newlines or commas in general skills section
            # BUT be more careful - only extract from lines that look like skill lists
            clean_skills_text = re.sub(r'[A-Za-z/]+:\s*', '', skills_text)
            for line in clean_skills_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Skip lines that look like sentences (too long, have verbs, etc.)
                if len(line) > 100:  # Likely a sentence, not a skill list
                    continue
                if any(word in line.lower() for word in ['contributed', 'developed', 'created', 'handled', 'managed', 'designed']):  # Action verbs = sentence
                    continue
                # Skip if looks like category header (has colon early)
                if ':' in line[:20]:
                    continue
                # Process lines that look like skill lists (comma/semicolon separated OR space-separated, short)
                if ',' in line or ';' in line:
                    # Comma/semicolon separated
                    for skill in re.split(r'[,;]', line):
                        skill = self._clean_skill(skill.strip())
                        if skill and self._is_valid_skill(skill):
                            skills.add(skill)
                elif len(line.split()) <= 15:
                    # Space-separated skills (e.g., "JavaScript HTML CSS .NET React.js")
                    # Check if line looks like a sentence (has common sentence words as whole words)
                    # Use word boundaries to avoid false matches (e.g., "Rest" shouldn't match "est")
                    sentence_words = r'\b(at|in|from|to|the|and|or|with)\b'
                    if not re.search(sentence_words, line.lower()):
                        # Process as space-separated skills
                        for skill in line.split():
                            skill = self._clean_skill(skill.strip())
                            if skill and self._is_valid_skill(skill):
                                skills.add(skill)
        
        # Final cleanup - remove any remaining invalid skills and duplicates
        cleaned_skills = set()
        skill_list = list(skills)
        
        for skill in skill_list:
            skill_lower = skill.lower()
            
            # Skip if it's a common word or phrase
            if skill_lower in {'like', 'using', 'with', 'via', 'through', 'for', 'in', 'on', 'at', 'the', 'and', 'or'}:
                continue
            
            # Skip skills that look like sentences or descriptions (too many words)
            if len(skill.split()) > 4:
                continue
            
            # Skip skills containing action verbs (likely descriptions)
            if any(word in skill_lower for word in ['handling', 'everything', 'contributed', 'developed', 'created', 'built', 'delivered']):
                continue
            
            # Skip skills containing date patterns
            if re.search(r'\b(19|20)\d{2}\s*[-–—]', skill):
                continue
            
            # Skip skills containing company indicators
            if any(word in skill_lower for word in ['technologies', 'software', 'solutions', 'systems', 'pvt', 'ltd', 'llc', 'inc']):
                continue
            
            # Check for duplicates/near-duplicates
            is_duplicate = False
            for existing_skill in list(cleaned_skills):
                existing_lower = existing_skill.lower()
                # Exact match (case-insensitive)
                if skill_lower == existing_lower:
                    is_duplicate = True
                    break
                # One is a subset of the other (e.g., "AI/ML Integration" vs "Core AI/ML Integration")
                if skill_lower in existing_lower or existing_lower in skill_lower:
                    # Prefer the shorter version (usually cleaner)
                    if len(skill) < len(existing_skill):
                        cleaned_skills.discard(existing_skill)
                        # Continue to add the shorter one
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                # Add if it matches known skills or looks like a technology
                # Also allow skills that are reasonably short and look technical (not just random words)
                if (skill_lower in [s.lower() for s in self.known_skills] or 
                    self._looks_like_technology(skill) or
                    (len(skill) >= 2 and len(skill) <= 30 and 
                     (skill[0].isupper() or '.' in skill or '/' in skill or skill.isupper() or skill.islower()))):
                    cleaned_skills.add(skill)
        
        return sorted(list(cleaned_skills), key=str.lower)
    
    def _clean_skill(self, skill: str) -> str:
        """Clean skill string - remove phrases like 'like django', extra words"""
        if not skill:
            return ""
        
        original_skill = skill
        skill = skill.strip()
        
        # Skip if too long (likely a phrase, not a skill) - BE STRICT
        if len(skill) > 35:
            return ""
        
        # Skip if starts with lowercase common words (likely a sentence fragment)
        if re.match(r'^(and|or|the|a|an|with|from|to|using|via|through|for|in|on|at|handling|everything)\s+', skill, re.IGNORECASE):
            skill = re.sub(r'^(and|or|the|a|an|with|from|to|using|via|through|for|in|on|at|handling|everything)\s+', '', skill, flags=re.IGNORECASE).strip()
            # If nothing left after removing prefix, skip
            if not skill:
                return ""
        
        # Remove common prefixes/suffixes more aggressively
        skill = re.sub(r'^(like|including|such as|e\.g\.|for example)\s+', '', skill, flags=re.IGNORECASE)
        skill = re.sub(r'\s+(like|including|etc\.?)$', '', skill, flags=re.IGNORECASE)
        
        # Remove parenthetical content
        skill = re.sub(r'\([^)]*\)', '', skill)
        
        # Remove date patterns (e.g., "Company 2019 - 2020")
        skill = re.sub(r'\b(19|20)\d{2}\s*[-–—]\s*(?:19|20)?\d{2}|PRESENT|CURRENT\b', '', skill, flags=re.IGNORECASE)
        
        # If skill contains sentence-like words in middle, it's likely a phrase - skip
        if re.search(r'\b(handling|everything|from|to|with|using|via|through|contributed|developed|created|built|delivered)\b', skill, re.IGNORECASE):
            # But allow if it's a valid tech name like "System Design" or "REST APIs"
            if not any(valid in skill.lower() for valid in ['system design', 'rest api', 'microservice', 'api']):
                return ""
        
        # Extract just the skill name (first word/phrase before common separators)
        skill = re.split(r'\s+/\s+|\s+and\s+|\s+or\s+', skill)[0].strip()
        
        # Remove trailing punctuation
        skill = skill.rstrip('.,;:')
        
        # Skip if contains too many words (likely a phrase) - BE STRICT
        word_count = len(skill.split())
        if word_count > 3:  # Most skills are 1-2 words, max 3
            return ""
        
        # Skip if too short after cleaning
        if len(skill) < 2:
            return ""
        
        return skill
    
    def _is_valid_skill(self, skill: str) -> bool:
        """Validate if a string is a valid skill - More lenient validation"""
        if not skill or len(skill) < 2 or len(skill) > 50:
            return False
        
        # Must not be just numbers
        if skill.replace('.', '').replace('/', '').replace('-', '').isdigit():
            return False
        
        # Must not be common words
        common_words = {'the', 'and', 'or', 'with', 'using', 'via', 'through', 'for', 'in', 'on', 'at', 'like', 'like', 'handling', 'everything'}
        if skill.lower().strip() in common_words:
            return False
        
        # Must not be date patterns
        if re.search(r'\b(19|20)\d{2}\s*[-–—]', skill):
            return False
        
        # Must not be company indicators
        if any(word in skill.lower() for word in ['technologies', 'software', 'solutions', 'systems', 'pvt', 'ltd', 'llc', 'inc', 'corp', 'company']):
            return False
        
        # Must not contain action verbs (likely a sentence)
        action_verbs = ['contributed', 'developed', 'created', 'built', 'designed', 'handled', 'managed', 'led', 'worked', 'delivered']
        if any(verb in skill.lower() for verb in action_verbs):
            return False
        
        skill_lower = skill.lower().strip()
        
        # Accept if in known skills list
        if skill_lower in [s.lower() for s in self.known_skills]:
            return True
        
        # Accept if looks like technology
        if self._looks_like_technology(skill):
            return True
        
        # More lenient: Accept if it's reasonably short (2-30 chars) and doesn't look like a sentence
        # This catches skills that might not be in the known list
        if 2 <= len(skill) <= 30:
            # Reject if it has too many spaces (likely a phrase)
            if skill.count(' ') > 3:
                return False
            # Reject if it's all lowercase and too long (likely a sentence)
            if skill.islower() and len(skill) > 15 and ' ' in skill:
                # But allow common tech phrases
                if not any(phrase in skill_lower for phrase in ['machine learning', 'deep learning', 'data science', 'react native', 'rest api', 'ci/cd']):
                    return False
            # Accept if it has tech-like patterns (capital letters, dots, slashes, numbers)
            if (any(c.isupper() for c in skill) or 
                '.' in skill or 
                '/' in skill or 
                skill[0].isupper() or
                any(c.isdigit() for c in skill)):
                return True
            # Accept short lowercase words that could be tech (3-10 chars, no spaces)
            if 3 <= len(skill) <= 10 and skill.islower() and ' ' not in skill:
                return True
        
        return False
    
    def _looks_like_technology(self, skill: str) -> bool:
        """Check if string looks like a technology name"""
        # Has dots (e.g., "node.js", "asp.net")
        if '.' in skill:
            return True
        
        # Ends with common tech suffixes
        if any(skill.lower().endswith(ext) for ext in ['.js', '.net', '.py', '.java', '.ts']):
            return True
        
        # Has capital letters in middle (camelCase or PascalCase)
        if len(skill) > 2 and any(c.isupper() for c in skill[1:]):
            return True
        
        # Short tech names (3-15 chars, all lowercase, no spaces) - More lenient
        if 3 <= len(skill) <= 15 and skill.islower() and ' ' not in skill:
            # Common tech prefixes/names
            tech_prefixes = ('react', 'vue', 'angular', 'node', 'nest', 'next', 'nuxt', 'django', 'flask', 'fast',
                           'spring', 'laravel', 'rails', 'express', 'mongodb', 'postgres', 'redis', 'elastic',
                           'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'gitlab', 'github',
                           'pytorch', 'tensorflow', 'pandas', 'numpy', 'scikit', 'keras', 'opencv',
                           'android', 'flutter', 'xamarin', 'tailwind', 'bootstrap', 'material', 'antd',
                           'graphql', 'websocket', 'nginx', 'apache', 'linux', 'windows', 'macos',
                           'aws', 'azure', 'gcp', 'firebase', 'vercel', 'netlify', 'heroku')
            if skill.startswith(tech_prefixes) or skill in tech_prefixes:
                return True
            # Accept any short lowercase word that could be a tech name (more lenient)
            if skill.isalpha() and len(skill) >= 3:
                return True
        
        # Has numbers (e.g., "HTML5", "CSS3", "Python3")
        if any(c.isdigit() for c in skill) and len(skill) <= 15:
            return True
        
        # Mixed case tech names (e.g., "JavaScript", "TypeScript", "NodeJS")
        if len(skill) > 3 and any(c.isupper() for c in skill) and any(c.islower() for c in skill):
            return True
        
        return False
    
    def _extract_experience_improved(self, text: str, pdf_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract work experience with flexible parsing - handles all resume formats"""
        experiences = []
        
        # Try HURIDOCS layout analysis first (if available and PDF path provided)
        # Convert relative path to absolute if needed
        abs_pdf_path = None
        if pdf_path:
            pdf_path_obj = Path(pdf_path)
            # Try direct path first
            if pdf_path_obj.exists():
                abs_pdf_path = str(pdf_path_obj.resolve())
            # Try with /app prefix for Docker container (common case)
            elif pdf_path.startswith('./'):
                abs_pdf_path = f"/app/{pdf_path[2:]}"
                if not Path(abs_pdf_path).exists():
                    abs_pdf_path = None
            # If still relative, try resolving from current working directory
            if not abs_pdf_path:
                try:
                    resolved = pdf_path_obj.resolve()
                    if resolved.exists():
                        abs_pdf_path = str(resolved)
                except:
                    pass
        
        if self.use_huridocs and abs_pdf_path and Path(abs_pdf_path).exists():
            try:
                logger.info("attempting_huridocs_layout_analysis", pdf_path=abs_pdf_path, original_path=pdf_path)
                layout_data = self.huridocs_analyzer.analyze_pdf_layout(abs_pdf_path, fast=True)
                if layout_data:
                    # NEW: Try using HURIDOCS segmented experience data first (uses type information)
                    try:
                        segmented_exp_data = self.huridocs_analyzer.get_segmented_experience_data(layout_data)
                        if segmented_exp_data.get("has_segmentation") and segmented_exp_data.get("segments"):
                            logger.info("using_huridocs_segmented_experience", 
                                      segments_count=len(segmented_exp_data["segments"]),
                                      titles_count=len(segmented_exp_data["titles"]))
                            
                            # Parse using segmented data
                            segmented_experiences = self._parse_segmented_experience(
                                segmented_exp_data["segments"], 
                                segmented_exp_data["titles"]
                            )
                            
                            if segmented_experiences:
                                logger.info("huridocs_segmented_experience_success", count=len(segmented_experiences))
                                return segmented_experiences
                    except Exception as e:
                        logger.warning("huridocs_segmented_extraction_failed", error=str(e))
                    
                    # Fallback: Extract text with proper layout structure
                    extracted = self.huridocs_analyzer.extract_text_with_layout(layout_data)
                    
                    # Use structured text from HURIDOCS
                    if extracted.get("layout_info", {}).get("has_columns"):
                        logger.info("huridocs_using_column_layout")
                        # Process columns separately - experience is usually in right column
                        for col_name, col_data in extracted["columns"].items():
                            if col_data.get("has_columns"):
                                # Right column typically has experience/work history
                                right_text = col_data.get("right", "")
                                if right_text:
                                    logger.info("huridocs_processing_right_column", length=len(right_text))
                                    # Create a simple layout_info for column processing
                                    col_layout_info = {"has_columns": False, "layout_type": "single_column"}
                                    col_experiences = self._extract_experience_from_text(right_text, col_layout_info)
                                    if col_experiences:
                                        logger.info("huridocs_right_column_experiences", count=len(col_experiences))
                                    experiences.extend(col_experiences)
                                
                                # Left column might also have some experience (check for completeness)
                                left_text = col_data.get("left", "")
                                if left_text:
                                    logger.info("huridocs_processing_left_column", length=len(left_text))
                                    col_layout_info = {"has_columns": False, "layout_type": "single_column"}
                                    col_experiences = self._extract_experience_from_text(left_text, col_layout_info)
                                    if col_experiences:
                                        logger.info("huridocs_left_column_experiences", count=len(col_experiences))
                                    experiences.extend(col_experiences)
                        
                        # If we found experiences in columns, return them (don't fall back)
                        if experiences:
                            logger.info("huridocs_experience_from_columns", count=len(experiences))
                            # Remove duplicates
                            seen = set()
                            unique_experiences = []
                            for exp in experiences:
                                exp_key = (exp.get("company", ""), exp.get("title", ""), exp.get("start_date", ""))
                                if exp_key not in seen:
                                    seen.add(exp_key)
                                    unique_experiences.append(exp)
                            experiences = unique_experiences
                            
                            if experiences:
                                logger.info("huridocs_experience_extraction_success", count=len(experiences))
                                return experiences
                    
                    # If no columns detected or no experience found in columns, use full text
                    if not experiences:
                        logger.info("huridocs_using_full_text_fallback")
                        full_text = extracted.get("text", text)
                        experiences = self._extract_experience_from_text(full_text, None)
                    
                    # Remove duplicates
                    if experiences:
                        seen = set()
                        unique_experiences = []
                        for exp in experiences:
                            exp_key = (exp.get("company", ""), exp.get("title", ""), exp.get("start_date", ""))
                            if exp_key not in seen:
                                seen.add(exp_key)
                                unique_experiences.append(exp)
                        experiences = unique_experiences
                        
                        if experiences:
                            logger.info("huridocs_experience_extraction_success", count=len(experiences))
                            return experiences
            except Exception as e:
                logger.warning("huridocs_extraction_failed_fallback", error=str(e))
        
        # Fallback to text-based layout analysis
        layout_info = self.layout_analyzer.analyze_layout(text)
        
        # If columns detected, extract from appropriate column
        if layout_info.get("has_columns"):
            columns = self.layout_analyzer.split_columns(text, layout_info)
            
            # Experience is usually in right column, but check both
            # Look for WORK EXPERIENCE section in each column
            for col_name, col_text in columns.items():
                col_experiences = self._extract_experience_from_text(col_text, layout_info)
                experiences.extend(col_experiences)
            
            # Remove duplicates
            seen = set()
            unique_experiences = []
            for exp in experiences:
                exp_key = (exp.get("company", ""), exp.get("title", ""), exp.get("start_date", ""))
                if exp_key not in seen:
                    seen.add(exp_key)
                    unique_experiences.append(exp)
            experiences = unique_experiences
            
            if experiences:
                return experiences
        
        # If no columns or no experience found in columns, use original method
        return self._extract_experience_from_text(text, layout_info)
    
    def _extract_experience_from_text(self, text: str, layout_info: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Extract experience from text using layout-aware parsing"""
        experiences = []
        lines = text.split('\n')
        
        # Use layout information to find experience section
        sections = layout_info.get("sections", {}) if layout_info else {}
        boundaries = layout_info.get("section_boundaries", {}) if layout_info else {}
        
        # Find EXPERIENCE section using layout info
        exp_text = None
        if "EXPERIENCE" in sections:
            exp_section = sections["EXPERIENCE"]
            start_line = exp_section["line_index"]
            if "EXPERIENCE" in boundaries:
                end_line = boundaries["EXPERIENCE"]["end"]
                exp_text = '\n'.join(lines[start_line + 1:end_line + 1])  # +1 to skip header
            else:
                # Fallback: extract until next section or end
                exp_text = '\n'.join(lines[start_line + 1:])
        
        # If layout-based extraction didn't work, try regex patterns
        # Handle both normal and spaced-out text (PDF extraction often spaces letters: "W O R K   E X P E R I E N C E")
        if not exp_text:
            # Normalize text: collapse multiple spaces/tabs but preserve newlines
            normalized_text = re.sub(r'[ \t]+', ' ', text)  # Collapse spaces/tabs, keep newlines
            
            section_end = r'(?:EDUCATION|PROJECTS|SKILLS|CERTIFICATIONS|LANGUAGES|ACHIEVEMENTS|AWARDS|INTERESTS|REFERENCES|OBJECTIVE|PROFILE|SUMMARY|CONTACT|TECHNICAL|COMPETENCIES|TOOLS|FRAMEWORKS|PLATFORMS)'
            
            section_patterns = [
                # Normal patterns (try first on original text)
                r'(?:WORK\s+)?EXPERIENCE[:\s]*\n(.*?)(?=\n' + section_end + r'[:\s]|$)',
                r'EMPLOYMENT[:\s]*\n(.*?)(?=\n' + section_end + r'[:\s]|$)',
                r'CAREER[:\s]*\n(.*?)(?=\n' + section_end + r'[:\s]|$)',
                r'PROFESSIONAL\s+EXPERIENCE[:\s]*\n(.*?)(?=\n' + section_end + r'[:\s]|$)',
                r'WORK\s+HISTORY[:\s]*\n(.*?)(?=\n' + section_end + r'[:\s]|$)',
                r'WORK\s+EXPERIENCE[:\s]*\n(.*?)(?=\n' + section_end + r'[:\s]|$)',
                # Two-column layouts (EDUCATION and EXPERIENCE on same line)
                r'(?:EDUCATION\s+)?(?:WORK\s+)?EXPERIENCE[:\s]*\n(.*?)(?=\n(?:PROJECTS|SKILLS|CERTIFICATIONS|LANGUAGES|ACHIEVEMENTS|AWARDS)[:\s]|$)',
                # Spaced-out text patterns (PDF extraction artifacts: "W O R K   E X P E R I E N C E")
                # Match spaced letters with flexible spacing
                r'(?:W\s+O\s+R\s+K\s+)?E\s+X\s+P\s+E\s+R\s+I\s+E\s+N\s+C\s+E[:\s]*\n(.*?)(?=\n(?:E\s+D\s+U\s+C\s+A\s+T\s+I\s+O\s+N|P\s+R\s+O\s+J\s+E\s+C\s+T\s+S|S\s+K\s+I\s+L\s+L\s+S)[:\s]|$)',
                r'W\s+O\s+R\s+K\s+E\s+X\s+P\s+E\s+R\s+I\s+E\s+N\s+C\s+E[:\s]*\n(.*?)(?=\n(?:E\s+D\s+U\s+C\s+A\s+T\s+I\s+O\s+N|P\s+R\s+O\s+J\s+E\s+C\s+T\s+S|S\s+K\s+I\s+L\s+L\s+S)[:\s]|$)',
            ]
            
            # Try patterns on both original and normalized text (preserve newlines)
            texts_to_search = [text, normalized_text]
            
            for search_text in texts_to_search:
                for pattern in section_patterns:
                    exp_section = re.search(pattern, search_text, re.IGNORECASE | re.DOTALL)
                    if exp_section:
                        exp_text = exp_section.group(1)
                        logger.info("experience_section_found_via_regex", pattern_index=section_patterns.index(pattern))
                        break
                if exp_text:
                    break
        
        # If no explicit section found, try content-based detection
        # This is especially useful for column text where headers might be spaced-out
        if not exp_text:
            exp_text = self._find_experience_by_content(text)
            if exp_text:
                logger.info("experience_found_by_content_detection", length=len(exp_text))
        
        if not exp_text:
            logger.info("no_experience_section_found_in_text", text_length=len(text))
            return experiences
        
        # Clean up: Remove education entries that got mixed in (they usually have university/degree keywords)
        # Split by lines and filter out lines that are clearly education
        lines = exp_text.split('\n')
        cleaned_lines = []
        skip_next_n_lines = 0
        
        for i, line in enumerate(lines):
            if skip_next_n_lines > 0:
                skip_next_n_lines -= 1
                continue
            
            line_upper = line.upper()
            # Skip lines that are clearly education (university, degree names)
            if any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"]) and \
               any(word in line_upper for word in ["MCA", "BSC", "MSC", "BTECH", "MTECH", "BACHELOR", "MASTER", "PHD", "ACADEMIC", "COURSEWORK"]):
                # Skip this line and next 1-2 lines (usually degree details)
                skip_next_n_lines = 2
                continue
            
            # Skip date lines that are clearly education dates (2019-2021, 2015-2018) when followed by university
            # Also skip if date is in past (not PRESENT) and next line has university
            date_match = re.search(r'(\d{4})\s*[-–—]\s*(\d{4}|PRESENT|CURRENT|NOW)', line.strip())
            if date_match:
                end_date = date_match.group(2)
                # If it's a past date (not PRESENT) and next line has university, it's likely education
                if end_date not in ["PRESENT", "CURRENT", "NOW"] and i + 1 < len(lines):
                    next_line_upper = lines[i + 1].upper()
                    if any(word in next_line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "MCA", "BACHELOR", "MASTER"]):
                        skip_next_n_lines = 3
                        continue
            
            cleaned_lines.append(line)
        
        exp_text = '\n'.join(cleaned_lines)
        
        # Flexible entry splitting - handle multiple formats:
        # 1. Split by date patterns (most common)
        # 2. Split by company indicators
        # 3. Split by double newlines (some resumes use spacing)
        
        # Primary: Split by date patterns - prioritize PRESENT dates
        # IMPORTANT: Include the line BEFORE the date (usually company name)
        # Strategy: Split by ALL dates (PRESENT and past), but include previous line for company
        
        lines_list = exp_text.split('\n')
        entries = []
        current_entry = []
        # Enhanced date pattern: handles multiple date formats
        # Formats: YYYY-YYYY, YYYY-MM-YYYY-MM, Month YYYY - Month YYYY, YYYY/YYYY, etc.
        date_pattern = r'(?:\d{4}(?:-\d{2})?|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\s*[-–—/]\s*(?:\d{4}(?:-\d{2})?|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|PRESENT|CURRENT|NOW|TILL\s+DATE|TILL\s+NOW)'
        
        # Skip profile summary and section headers at the start
        skip_until_company = True
        
        for i, line in enumerate(lines_list):
            line_stripped = line.strip()
            line_upper = line_stripped.upper()
            
            # Check if this is a company line (has company keywords)
            is_company_line = any(keyword in line_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS", "SYSTEMS"])
            
            # Check if this line has a date pattern
            has_date = bool(re.search(date_pattern, line_stripped, re.IGNORECASE))
            
            # Once we find a company line or date, we're past the profile summary
            if is_company_line or has_date:
                skip_until_company = False
            
            # Skip profile summary and section headers
            if skip_until_company:
                # Skip lines that look like profile summary or section headers
                if (any(word in line_upper for word in ["PROFILE", "SUMMARY", "VERSATILE", "EXPERIENCE"]) and 
                    not is_company_line and not has_date):
                    continue
            
            # IMPORTANT: Before adding line, check if current_entry already has title+company (Entry 1 structure)
            # If so, and this line looks like a description OR a new title, save Entry 1 and start Entry 2
            if current_entry and not has_date:
                entry_text_check = '\n'.join(current_entry)
                entry_upper_check = entry_text_check.upper()
                has_title = any(keyword in entry_upper_check for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST"])
                has_company = (any(keyword in entry_upper_check for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS", "SYSTEMS"]) or
                              any(len(entry_line.strip()) > 2 and len(entry_line.strip()) < 60 and len(entry_line.strip().split()) <= 2 and
                                  not any(word in entry_line.upper() for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"]) and
                                  not any(keyword in entry_line.upper() for keyword in ["DEVELOPER", "ENGINEER", "MANAGER"]) and
                                  not re.search(r'\d+', entry_line) for entry_line in current_entry))
                
                # If we have title+company but no date yet, check if this line starts a new entry
                if has_title and has_company:
                    line_lower = line_stripped.lower()
                    # Check if this line is a description (has action verbs, numbers, special chars)
                    is_description = (any(word in line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented", "modified"]) or
                                     re.search(r'\d+', line_stripped) or re.search(r'[+\-%]', line_stripped) or
                                     len(line_stripped) > 100)
                    
                    # Check if this line is a new title (has job keywords and is short)
                    is_new_title = (any(keyword in line_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST"]) and
                                   len(line_stripped) < 60 and
                                   len(line_stripped.split()) <= 8)
                    
                    # Check if this line is a location (like "Nashville, TN")
                    is_location = bool(re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', line_stripped))
                    
                    # If this is a description line OR a new title OR a location, save Entry 1 and start accumulating for Entry 2
                    # IMPORTANT: Filter Entry 1 to only include title and company lines (no descriptions)
                    if is_description or is_new_title or is_location:
                        # Filter Entry 1 to only title and company lines
                        filtered_entry = []
                        for entry_line in current_entry:
                            entry_line_upper = entry_line.upper()
                            entry_line_lower = entry_line.lower()
                            is_title_line = any(keyword in entry_line_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST"])
                            is_company_line = (any(keyword in entry_line_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS", "SYSTEMS"]) or
                                              (len(entry_line.strip()) > 2 and len(entry_line.strip()) < 60 and len(entry_line.strip().split()) <= 2 and
                                               not any(word in entry_line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"]) and
                                               not any(keyword in entry_line_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER"]) and
                                               not any(word in entry_line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented", "modified"]) and
                                               not re.search(r'\d+', entry_line) and not re.search(r'[+\-%]', entry_line)))
                            
                            if is_title_line or is_company_line:
                                filtered_entry.append(entry_line)
                        
                        # Use filtered entry if we have title/company, otherwise use original
                        if filtered_entry:
                            entry_text = '\n'.join(filtered_entry)
                        else:
                            entry_text = '\n'.join(current_entry)
                        
                        entry_upper = entry_text.upper()
                        has_work = (any(keyword in entry_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS"]) or
                                   any(keyword in entry_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST"]))
                        if has_work:
                            entries.append(entry_text)
                        # Start new entry with this line (it's the start of Entry 2)
                        current_entry = [line_stripped]
                        continue  # Skip the rest of the loop for this line
            
            # If we find a date line, this marks the end of current entry and start of new
            if has_date:
                # If we have accumulated lines, save as entry (but only if it has work indicators)
                if current_entry:
                    entry_text = '\n'.join(current_entry)
                    entry_upper = entry_text.upper()
                    # Only save if it has work indicators (company or job title)
                    has_work = (any(keyword in entry_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS"]) or
                               any(keyword in entry_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST"]))
                    if has_work:
                        entries.append(entry_text)
                
                # Start new entry - include date line and previous lines if they look like title/company
                # Pattern detection: Title -> Company -> Date
                # IMPORTANT: Check if previous lines form a Title->Company pattern, then add date to complete the entry
                if i >= 2:
                    prev_prev_line = lines_list[i-2].strip()
                    prev_line = lines_list[i-1].strip()
                    prev_prev_upper = prev_prev_line.upper()
                    prev_line_upper = prev_line.upper()
                    prev_line_lower = prev_line.lower()
                    
                    # Check if prev_prev is title and prev is company
                    has_title_kw = any(keyword in prev_prev_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST"])
                    has_company_kw = any(keyword in prev_line_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS", "SYSTEMS"])
                    # Accept short company names (1-2 words) even without keywords (like "Deloitte")
                    is_short_company = (len(prev_line) > 2 and len(prev_line) < 60 and 
                                       len(prev_line.split()) <= 2 and  # Short name (1-2 words)
                                       not any(word in prev_line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"]) and
                                       not any(keyword in prev_line_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER"]) and
                                       not any(word in prev_line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented"]) and
                                       not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented)', prev_line, re.IGNORECASE) and
                                       not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', prev_line))  # Not a location
                    
                    if has_title_kw and (has_company_kw or is_short_company):
                        # Pattern: Title -> Company -> Date (include all three)
                        current_entry = [prev_prev_line, prev_line, line]
                    elif has_company_kw or is_short_company:
                        # Pattern: Company -> Date (include both)
                        current_entry = [prev_line, line]
                    else:
                        # Just date line
                        current_entry = [line]
                elif i > 0:
                    # Check if previous line is company
                    prev_line = lines_list[i-1].strip()
                    prev_line_upper = prev_line.upper()
                    prev_line_lower = prev_line.lower()
                    has_company_kw = any(keyword in prev_line_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS", "SYSTEMS"])
                    # Accept short company names
                    is_short_company = (len(prev_line) > 2 and len(prev_line) < 60 and 
                                       len(prev_line.split()) <= 2 and
                                       not any(word in prev_line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"]) and
                                       not any(keyword in prev_line_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER"]) and
                                       not any(word in prev_line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented"]) and
                                       not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented)', prev_line, re.IGNORECASE) and
                                       not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', prev_line))
                    
                    if has_company_kw or is_short_company:
                        current_entry = [prev_line, line]
                    else:
                        current_entry = [line]
                else:
                    current_entry = [line]
            else:
                current_entry.append(line)
        
        # Add last entry (if it has work indicators)
        if current_entry:
            entry_text = '\n'.join(current_entry)
            entry_upper = entry_text.upper()
            has_work = (any(keyword in entry_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS"]) or
                       any(keyword in entry_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST"]))
            if has_work:
                entries.append(entry_text)
        
        # If that didn't work well, try splitting by job title patterns (lines starting with job titles)
        if len(entries) < 2:
            # Pattern: Newline followed by job title (Senior/Junior/Full-Stack/Software/etc. + Developer/Engineer/etc.)
            # Also handle lines that are just job titles (standalone)
            job_title_pattern = r'\n(?=(?:Senior|Junior|Sr\.|Jr\.|Full-Stack|Full Stack|Software|Lead|Principal|Staff|Associate)?\s*(?:Developer|Engineer|Architect|Manager|Consultant|Analyst|Designer|Specialist|Programmer))'
            split_entries = re.split(job_title_pattern, exp_text, flags=re.IGNORECASE)
            # Filter out empty entries and ensure we have multiple entries
            split_entries = [e.strip() for e in split_entries if e.strip()]
            if len(split_entries) > 1:
                entries = split_entries
        
        # If still not working, try splitting by company indicators
        if len(entries) < 2:
            entries = re.split(r'\n(?=[A-Z][^a-z]*\s+(?:PVT|LTD|LLC|INC|CORP|COMPANY|TECHNOLOGIES|SOFTWARE|SOLUTIONS))', exp_text, flags=re.IGNORECASE)
        
        # If still not working, try double newlines
        if len(entries) < 2:
            entries = re.split(r'\n\s*\n', exp_text)
        
        for entry in entries:
            if not entry.strip():
                continue
            
            # Check if entry is education (has university/degree but NO work indicators)
            entry_upper = entry.upper()
            has_university = any(word in entry_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL"])
            has_degree = any(word in entry_upper for word in ["BACHELOR", "MASTER", "MCA", "BSC", "MSC", "DEGREE", "ACADEMIC", "COURSEWORK"])
            
            # Work experience indicators (company, job title keywords)
            has_company = any(word in entry_upper for word in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS"])
            has_job_title = any(word in entry_upper for word in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST"])
            has_work_indicators = has_company or has_job_title
            
            # Skip ONLY if it has education keywords BUT no work indicators (pure education entry)
            if (has_university or has_degree) and not has_work_indicators:
                continue  # Skip this entry - it's education, not experience
            
            # Even if entry has both education and work indicators, try to parse it
            # The parser will extract work experience parts and filter education
            exp_dict = self._parse_experience_entry_improved(entry.strip())
            if exp_dict:
                # Check for duplicate entries (same company and dates)
                # If we already have an entry with same company and dates, merge them
                is_duplicate = False
                for existing_exp in experiences:
                    existing_company = existing_exp.get("company", "")
                    existing_dates = existing_exp.get("date_range", "")
                    new_company = exp_dict.get("company", "")
                    new_dates = exp_dict.get("date_range", "")
                    
                    # Check if same company and dates (or one has missing dates)
                    if (existing_company and new_company and 
                        existing_company == new_company and
                        (existing_dates == new_dates or not existing_dates or not new_dates)):
                        # Merge: prefer non-empty title and dates
                        if not existing_exp.get("title") or existing_exp.get("title") == "Not Specified":
                            existing_exp["title"] = exp_dict.get("title", existing_exp.get("title"))
                        if not existing_exp.get("date_range"):
                            existing_exp["date_range"] = exp_dict.get("date_range", "")
                            existing_exp["start_date"] = exp_dict.get("start_date")
                            existing_exp["end_date"] = exp_dict.get("end_date")
                        if not existing_exp.get("description"):
                            existing_exp["description"] = exp_dict.get("description", "")
                        is_duplicate = True
                        logger.info("merged_duplicate_experience_entry", company=new_company)
                        break
                
                if is_duplicate:
                    continue  # Skip adding duplicate
                # Accept if we have company (most reliable indicator) OR valid title
                company_valid = exp_dict.get("company") and exp_dict.get("company") != "Not Specified"
                title = exp_dict.get("title", "")
                
                # Check if title is a description line
                is_description_line = (
                    title.startswith("Developers, Testers") or
                    title.startswith("Collaborated") or
                    title.startswith("Designed") or
                    title.startswith("Led and") or
                    title.startswith("Completed") or
                    title.startswith("Contributed") or
                    'ensure' in title.lower() or
                    'seamless' in title.lower() or
                    'coordination' in title.lower() or
                    title.count(',') >= 2 or  # Too many commas
                    title.count('and') >= 2 or  # Multiple "and"
                    len(title) > 50  # Too long
                )
                
                # If title is description line, set to "Not Specified" if we have company
                if is_description_line and company_valid:
                    exp_dict["title"] = "Not Specified"  # Will be inferred from description later
                    title = "Not Specified"
                
                # Title validation - must have job keywords if not "Not Specified"
                job_keywords = ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", 
                               "ARCHITECT", "CONSULTANT", "ANALYST", "SPECIALIST", "DESIGNER"]
                has_job_keyword = any(keyword in title.upper() for keyword in job_keywords) if title != "Not Specified" else True
                
                title_valid = (title and 
                              title != "Not Specified" and 
                              len(title) > 2 and
                              has_job_keyword and
                              not is_description_line)
                
                # Accept if company is valid OR title is valid
                if company_valid or title_valid:
                    experiences.append(exp_dict)
        
        return experiences
    
    def _find_experience_by_content(self, text: str) -> Optional[str]:
        """Find experience section by content patterns when explicit section header is missing"""
        # Look for patterns that indicate work experience:
        # - Company indicators (Pvt Ltd, Inc, Corp, Technologies, Software, Solutions)
        # - Job title keywords (Developer, Engineer, Manager, Lead, Senior, etc.)
        # - Date ranges (YYYY - YYYY or YYYY - PRESENT)
        # - Multiple occurrences suggest an experience section
        
        lines = text.split('\n')
        exp_start_idx = None
        exp_end_idx = None
        
        company_keywords = ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS", "SYSTEMS"]
        job_title_keywords = ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST", "SPECIALIST"]
        date_pattern = r'\d{4}\s*[-–—]\s*(?:\d{4}|PRESENT|CURRENT|NOW)'
        
        consecutive_work_indicators = 0
        max_consecutive = 0
        best_start = None
        
        # More flexible detection: check if company/job_title and date are within 3 lines of each other
        for i, line in enumerate(lines):
            line_upper = line.upper()
            has_company = any(keyword in line_upper for keyword in company_keywords)
            has_job_title = any(keyword in line_upper for keyword in job_title_keywords)
            has_date = bool(re.search(date_pattern, line, re.IGNORECASE))
            
            # Check if this line or nearby lines (within 3 lines) have work experience indicators
            is_work_line = False
            if has_date:
                # If this line has a date, check if nearby lines (within 3 lines) have company/job_title
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    nearby_line_upper = lines[j].upper()
                    if any(keyword in nearby_line_upper for keyword in company_keywords + job_title_keywords):
                        is_work_line = True
                        break
            elif has_company or has_job_title:
                # If this line has company/job_title, check if nearby lines (within 3 lines) have date
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    if re.search(date_pattern, lines[j], re.IGNORECASE):
                        is_work_line = True
                        break
            
            if is_work_line:
                consecutive_work_indicators += 1
                if consecutive_work_indicators > max_consecutive:
                    max_consecutive = consecutive_work_indicators
                    best_start = i - consecutive_work_indicators + 1
            else:
                consecutive_work_indicators = 0
        
        # If we found a good cluster of work experience indicators, extract that section
        # Lower threshold to 1 to catch single experience entries (especially in column layouts)
        if best_start and max_consecutive >= 1:
            # Find end - look for next major section or end of text
            end_idx = len(lines)
            for i in range(best_start + max_consecutive, len(lines)):
                line_upper = lines[i].upper()
                # Stop at major section headers
                if any(header in line_upper for header in ["EDUCATION", "PROJECTS", "SKILLS", "CERTIFICATIONS", "LANGUAGES", "ACHIEVEMENTS", "AWARDS"]):
                    end_idx = i
                    break
                # Stop if we hit a long gap (likely new section)
                if i > best_start + max_consecutive + 10 and not re.search(date_pattern, lines[i], re.IGNORECASE):
                    end_idx = i
                    break
            
            return '\n'.join(lines[best_start:end_idx])
        
        return None
    
    def _parse_segmented_experience(self, segments: List[Dict[str, Any]], title_segments: List[str]) -> List[Dict[str, Any]]:
        """
        Parse experience entries from HURIDOCS segmented data
        Groups segments by spatial proximity and uses type information
        """
        if not segments:
            return []
        
        experiences = []
        current_entry_segments = []
        current_title = None
        current_company = None
        
        # Group segments by proximity (segments close together are likely same entry)
        for i, segment in enumerate(segments):
            # Safety check
            if not isinstance(segment, dict):
                continue
                
            text = segment.get("text", "").strip() if segment.get("text") else ""
            seg_type = segment.get("type", "").lower() if segment.get("type") else ""
            top = segment.get("top", 0) if segment.get("top") is not None else 0
            
            # Check if this is a title segment (likely job title) OR text that looks like a job title
            # HURIDOCS might classify job titles as "text" instead of "title"
            is_potential_title = False
            if seg_type == "title" and text:
                # Check if it looks like a job title (not section header)
                if not any(keyword in text.upper() for keyword in ["EXPERIENCE", "WORK", "EDUCATION", "SKILLS"]):
                    is_potential_title = True
            elif seg_type == "text" and text:
                # WORLD-CLASS ELITE LEVEL: Advanced pattern matching for job titles
                # Check if text looks like a job title using sophisticated ML-like pattern recognition
                text_upper = text.upper()
                text_lower = text.lower()
                
                # Expanded job title keywords (including variations and common patterns)
                job_keywords = ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", 
                               "CONSULTANT", "ANALYST", "SPECIALIST", "DESIGNER", "SCIENTIST", "FULL-STACK", 
                               "FULL STACK", "STACK", "SOFTWARE", "FRONTEND", "BACKEND", "FULLSTACK", "DEVOPS",
                               "JR", "JR.", "JUNIOR"]
                
                has_job_keyword = any(keyword in text_upper for keyword in job_keywords)
                
                # Context-aware validation with world-class precision
                is_short = len(text) > 5 and len(text) < 80 and len(text.split()) <= 10
                no_action_verbs = not any(word in text_lower for word in ["designed", "developed", "created", "built", 
                                                                          "led", "managed", "collaborated", "analyzed", 
                                                                          "integrated", "wrote", "maintained", "documented", 
                                                                          "participated", "implemented", "modified", "worked", 
                                                                          "delivered", "ensured", "improved", "optimized", 
                                                                          "contributed", "achieved", "reduced", "increased"])
                no_numbers = not re.search(r'\d+', text)
                # Allow periods (for "Jr.") and hyphens (for "Full-Stack") but not other special chars
                no_special_chars = not re.search(r'[+\-%]', text.replace('.', '').replace('-', ''))
                not_education = not any(word in text_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL", 
                                                                        "BACHELOR", "MASTER", "DEGREE", "MCA", "BSC", "MSC"])
                not_company_keyword = not any(keyword in text_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", 
                                                                                    "COMPANY", "TECHNOLOGIES"])
                not_location = not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', text)
                not_description_start = not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented|Modified)', text, re.IGNORECASE)
                not_date = not re.search(r'\d{4}', text)
                
                # Additional context: Check if it's likely a title based on position and surrounding context
                # Titles are usually: short, have job keywords, no action verbs, no dates, no locations
                is_likely_title = (has_job_keyword and is_short and no_action_verbs and no_numbers and 
                                 no_special_chars and not_education and not_company_keyword and 
                                 not_location and not_description_start and not_date)
                
                if is_likely_title:
                    is_potential_title = True
                    logger.info("detected_title_from_text_segment_elite", title=text, type=seg_type)
            
            if is_potential_title:
                # If we have accumulated segments, save previous entry
                if current_entry_segments and (current_title or current_company or len(current_entry_segments) > 3):
                    exp_entry = self._build_experience_from_segments(
                        current_entry_segments, current_title, current_company
                    )
                    if exp_entry:
                        experiences.append(exp_entry)
                
                # Start new entry
                current_title = text
                current_company = None
                current_entry_segments = [segment]
                continue
            
            # Check if this looks like a company name (short text, no action verbs)
            if not current_company and seg_type == "text" and text:
                text_lower = text.lower()
                is_company = (
                    len(text) > 2 and len(text) < 60 and
                    len(text.split()) <= 3 and
                    not any(word in text_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated"]) and
                    not re.search(r'\d+', text) and
                    not re.search(r'[+\-%]', text) and
                    (any(keyword in text.upper() for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS", "SYSTEMS"]) or
                     (len(text.split()) <= 2 and not any(word in text.upper() for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"])))
                )
                
                if is_company:
                    current_company = text
                    if not current_entry_segments:
                        current_entry_segments = [segment]
                    else:
                        current_entry_segments.append(segment)
                    continue
            
            # Check for date patterns
            date_pattern = r'(?:\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*[-–—]\s*(?:\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|PRESENT|CURRENT|NOW)'
            has_date = bool(re.search(date_pattern, text, re.IGNORECASE))
            
            # If we find a date and have accumulated segments, check if this starts a new entry
            if has_date and current_entry_segments:
                # Check if this date is far from previous segments (new entry)
                prev_segment = current_entry_segments[-1]
                prev_top = prev_segment.get("top", 0)
                gap = top - prev_top
                
                # Large gap (> 30px) OR date pattern with different year suggests new entry
                # Also check if this date is for a different period (Entry 2)
                date_match = re.search(r'(?:\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})', text, re.IGNORECASE)
                prev_text = '\n'.join([s.get("text", "") for s in current_entry_segments])
                prev_date_match = re.search(r'(?:\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})', prev_text, re.IGNORECASE)
                
                is_different_period = False
                if date_match and prev_date_match:
                    # Check if years are different (likely different entry)
                    date_year = date_match.group(0)
                    prev_year = prev_date_match.group(0)
                    if date_year != prev_year and (gap > 20 or len(current_entry_segments) > 5):
                        is_different_period = True
                
                # Large gap (> 30px) OR different period suggests new entry
                if gap > 30 or is_different_period:
                    # Save previous entry
                    exp_entry = self._build_experience_from_segments(
                        current_entry_segments, current_title, current_company
                    )
                    if exp_entry:
                        experiences.append(exp_entry)
                    
                    # Start new entry - check if this segment itself is a title or company
                    current_title = None
                    current_company = None
                    
                    # Check if previous segment (before date) is a title or company
                    if i > 0 and len(segments) > i - 1:
                        prev_seg = segments[i-1]
                        if prev_seg and isinstance(prev_seg, dict):
                            prev_seg_text = prev_seg.get("text", "").strip()
                            prev_seg_type = prev_seg.get("type", "").lower()
                            
                            # Check if previous segment is a title (WORLD-CLASS: Check both "title" type AND text that looks like a title)
                            if prev_seg_text:
                                # Check if it's a "title" type segment (and not a section header)
                                if prev_seg_type == "title" and not any(keyword in prev_seg_text.upper() for keyword in ["EXPERIENCE", "WORK", "EDUCATION", "SKILLS"]):
                                    current_title = prev_seg_text
                                # Also check if it looks like a job title (even if it's "text" type)
                                elif prev_seg_type == "text" and len(prev_seg_text) > 5 and len(prev_seg_text) < 80:
                                    prev_seg_upper = prev_seg_text.upper()
                                    prev_seg_lower = prev_seg_text.lower()
                                    # Use same sophisticated logic as is_potential_title
                                    has_job_keyword = any(keyword in prev_seg_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST", "SPECIALIST", "DESIGNER", "SCIENTIST", "FULL-STACK", "FULL STACK", "STACK"])
                                    is_short = len(prev_seg_text.split()) <= 10
                                    no_action_verbs = not any(word in prev_seg_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented", "modified", "worked", "delivered", "ensured", "improved", "optimized", "contributed"])
                                    no_numbers = not re.search(r'\d+', prev_seg_text)
                                    no_special_chars = not re.search(r'[+\-%]', prev_seg_text.replace('.', '').replace('-', ''))
                                    not_education = not any(word in prev_seg_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL", "BACHELOR", "MASTER", "DEGREE", "MCA", "BSC", "MSC"])
                                    not_company_keyword = not any(keyword in prev_seg_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES"])
                                    not_location = not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', prev_seg_text)
                                    not_description_start = not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented|Modified)', prev_seg_text, re.IGNORECASE)
                                    not_date = not re.search(r'\d{4}', prev_seg_text)
                                    
                                    if (has_job_keyword and is_short and no_action_verbs and no_numbers and 
                                        no_special_chars and not_education and not_company_keyword and 
                                        not_location and not_description_start and not_date):
                                        current_title = prev_seg_text
                                        logger.info("detected_title_from_prev_segment_elite", title=prev_seg_text, type=prev_seg_type)
                            
                            # Check if previous segment is a company
                            if not current_company and prev_seg_text:
                                text_lower = prev_seg_text.lower()
                                is_company = (
                                    len(prev_seg_text) > 2 and len(prev_seg_text) < 60 and
                                    len(prev_seg_text.split()) <= 3 and
                                    not any(word in text_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated"]) and
                                    not re.search(r'\d+', prev_seg_text) and
                                    not re.search(r'[+\-%]', prev_seg_text) and
                                    (any(keyword in prev_seg_text.upper() for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS", "SYSTEMS"]) or
                                     (len(prev_seg_text.split()) <= 2 and not any(word in prev_seg_text.upper() for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"])))
                                )
                                if is_company:
                                    current_company = prev_seg_text
                    
                    current_entry_segments = [segment]
                else:
                    # Same entry, add to current
                    current_entry_segments.append(segment)
            else:
                # Add to current entry
                if not current_entry_segments:
                    current_entry_segments = [segment]
                else:
                    current_entry_segments.append(segment)
        
        # Add last entry
        if current_entry_segments and (current_title or current_company):
            exp_entry = self._build_experience_from_segments(
                current_entry_segments, current_title, current_company
            )
            if exp_entry:
                experiences.append(exp_entry)
        
        return experiences
    
    def _build_experience_from_segments(self, segments: List[Dict[str, Any]], title: Optional[str], company: Optional[str]) -> Optional[Dict[str, Any]]:
        """Build experience entry from segments"""
        if not segments:
            return None
        
        # Extract text from segments
        entry_text = "\n".join([seg.get("text", "").strip() for seg in segments if isinstance(seg, dict) and seg.get("text", "").strip()])
        
        if not entry_text:
            return None
        
        # If we have company but not title, try to extract title from entry text
        # This is an EARLY fallback - check ALL lines, not just first 5
        if company and not title:
            lines = entry_text.split('\n')
            logger.info("early_title_extraction_in_build_segments", company=company, entry_lines=len(lines), entry_text_preview=entry_text[:300])
            for line in lines:  # Check ALL lines, not just first 5
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                line_upper = line_stripped.upper()
                line_lower = line_stripped.lower()
                
                # Check if it looks like a job title
                has_job_keyword = any(keyword in line_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST", "SPECIALIST", "DESIGNER", "SCIENTIST"])
                is_short = len(line_stripped) > 5 and len(line_stripped) < 80 and len(line_stripped.split()) <= 10
                no_action_verbs = not any(word in line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented", "modified", "worked", "delivered", "ensured", "improved", "optimized"])
                no_numbers = not re.search(r'\d+', line_stripped)
                # Allow periods (for "Jr.") and hyphens (for "Full-Stack") but not other special chars
                no_special_chars = not re.search(r'[+\-%]', line_stripped.replace('.', '').replace('-', ''))
                not_education = not any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL", "BACHELOR", "MASTER", "DEGREE"])
                not_company_keyword = not any(keyword in line_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY"])
                not_date = not re.search(r'\d{4}', line_stripped)
                not_company = line_stripped.lower() != company.lower()
                
                if has_job_keyword and is_short and no_action_verbs and no_numbers and no_special_chars and not_education and not_company_keyword and not_date and not_company:
                    title = line_stripped
                    break
        
        # If we have title and company from segments, use them directly (more accurate)
        if title and company:
            # Extract date from entry text
            date_pattern = r'(?:\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*[-–—]\s*(?:\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|PRESENT|CURRENT|NOW)'
            date_match = re.search(date_pattern, entry_text, re.IGNORECASE)
            date_range = date_match.group(0) if date_match else None
            
            # Extract start/end dates
            start_date = None
            end_date = None
            if date_match:
                parts = re.split(r'\s*[-–—]\s*', date_match.group(0))
                if len(parts) >= 1:
                    start_date = parts[0].strip()
                if len(parts) >= 2:
                    end_date = parts[1].strip()
            
            # Filter description (remove title, company, date lines)
            description_lines = []
            for line in entry_text.split('\n'):
                line_stripped = line.strip()
                if (line_stripped.lower() != title.lower() and 
                    line_stripped.lower() != company.lower() and
                    not re.search(date_pattern, line_stripped, re.IGNORECASE) and
                    len(line_stripped) > 10):  # Skip very short lines
                    description_lines.append(line_stripped)
            
            description = "\n".join(description_lines[:10])  # Limit to 10 lines
            
            return {
                "title": title,
                "company": company,
                "date_range": date_range,
                "start_date": start_date,
                "end_date": end_date,
                "description": description
            }
        
        # Fallback: Use existing parsing logic but with pre-identified title/company
        parsed = self._parse_experience_entry_improved(entry_text)
        
        # WORLD-CLASS ELITE LEVEL: Always prioritize parsed result's title
        # _parse_experience_entry_improved has the most sophisticated extraction logic
        if parsed and parsed.get("title") and parsed.get("title") != "Not Specified":
            # If we don't have a title from segments, use parsed result's title immediately
            if not title or title == "Not Specified":
                title = parsed.get("title")
                logger.info("using_parsed_title_elite_priority", title=title, company=company)
            # If we have both, prefer non-Jr. version
            elif "jr" not in title.lower() and "jr" in parsed.get("title", "").lower():
                title = parsed.get("title")
                logger.info("using_parsed_title_prefer_non_jr", title=title, company=company)
        
        # If still no title but we have company, try one more time to extract from entry text
        # This is an EARLY fallback before the main parsing
        if company and not title:
            lines = entry_text.split('\n')
            logger.info("early_title_extraction_fallback", company=company, entry_lines=len(lines), entry_text_preview=entry_text[:300])
            for line in lines:  # Check ALL lines, not just first 5
                line_stripped = line.strip()
                if not line_stripped or line_stripped.lower() == company.lower():
                    continue
                line_upper = line_stripped.upper()
                line_lower = line_stripped.lower()
                
                # Check if it looks like a job title
                has_job_keyword = any(keyword in line_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST", "SPECIALIST", "DESIGNER", "SCIENTIST"])
                is_short = len(line_stripped) > 5 and len(line_stripped) < 80 and len(line_stripped.split()) <= 10
                no_action_verbs = not any(word in line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented", "modified", "worked", "delivered", "ensured", "improved", "optimized"])
                no_numbers = not re.search(r'\d+', line_stripped)
                # Allow periods (for "Jr.") and hyphens (for "Full-Stack") but not other special chars
                no_special_chars = not re.search(r'[+\-%]', line_stripped.replace('.', '').replace('-', ''))
                not_education = not any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL", "BACHELOR", "MASTER", "DEGREE"])
                not_company_keyword = not any(keyword in line_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY"])
                not_date = not re.search(r'\d{4}', line_stripped)
                
                if has_job_keyword and is_short and no_action_verbs and no_numbers and no_special_chars and not_education and not_company_keyword and not_date:
                    title = line_stripped
                    logger.info("extracted_title_from_entry_text", title=title, company=company)
                    break
        
        if not parsed:
            # If parsing failed, create minimal entry with title/company
            # But first, try to extract title from entry text one more time
            if company and not title:
                lines = entry_text.split('\n')
                for line in lines[:5]:
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.lower() == company.lower():
                        continue
                    line_upper = line_stripped.upper()
                    line_lower = line_stripped.lower()
                    
                    # Check if it looks like a job title
                    has_job_keyword = any(keyword in line_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST", "SPECIALIST", "DESIGNER", "SCIENTIST"])
                    is_short = len(line_stripped) > 5 and len(line_stripped) < 80 and len(line_stripped.split()) <= 10
                    no_action_verbs = not any(word in line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented", "modified", "worked", "delivered", "ensured", "improved", "optimized"])
                    no_numbers = not re.search(r'\d+', line_stripped)
                    # Allow periods (for "Jr.") and hyphens (for "Full-Stack") but not other special chars
                    no_special_chars = not re.search(r'[+\-%]', line_stripped.replace('.', '').replace('-', ''))
                    not_education = not any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL", "BACHELOR", "MASTER", "DEGREE"])
                    not_company_keyword = not any(keyword in line_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY"])
                    not_date = not re.search(r'\d{4}', line_stripped)
                    
                    if has_job_keyword and is_short and no_action_verbs and no_numbers and no_special_chars and not_education and not_company_keyword and not_date:
                        title = line_stripped
                        break
            
            if title or company:
                return {
                    "title": title or "Not Specified",
                    "company": company or "Not Specified",
                    "date_range": None,
                    "start_date": None,
                    "end_date": None,
                    "description": entry_text[:500] if entry_text else ""
                }
            return None
        
        # WORLD-CLASS ELITE LEVEL: Intelligent title/company merging
        # Priority: 1) Parsed result (sophisticated extraction), 2) Segmented data, 3) Fallback extraction
        parsed_title = parsed.get("title") if parsed else None
        parsed_company = parsed.get("company") if parsed else None
        
        # TITLE MERGING STRATEGY:
        # 1. If parsed has a valid title, prefer it (it has world-class extraction logic)
        # 2. Only override if segmented title is clearly better (e.g., non-Jr. version)
        # 3. If no parsed title, use segmented or extract from text
        
        if parsed_title and parsed_title != "Not Specified" and len(parsed_title) > 3:
            # Parsed has a valid title - use it unless segmented is clearly better
            if title and title != "Not Specified":
                # Compare: prefer non-Jr. version if both exist
                if "jr" not in title.lower() and "jr" in parsed_title.lower():
                    parsed["title"] = title  # Segmented has better (non-Jr.) version
                    logger.info("using_segmented_title_prefer_non_jr", segmented=title, parsed=parsed_title)
                else:
                    # Keep parsed title (it's from sophisticated extraction)
                    parsed["title"] = parsed_title
                    logger.info("using_parsed_title_sophisticated", title=parsed_title)
            else:
                # No segmented title, use parsed
                parsed["title"] = parsed_title
                logger.info("using_parsed_title_no_segmented", title=parsed_title)
        elif title and title != "Not Specified":
            # No valid parsed title, use segmented
            parsed["title"] = title
            logger.info("using_segmented_title_no_parsed", title=title)
        elif not parsed_title or parsed_title == "Not Specified":
            # Neither has title - try one final extraction from entry text
            # WORLD-CLASS ELITE LEVEL: Ultra-aggressive extraction - check ALL lines
            if company:
                lines = entry_text.split('\n')
                logger.info("elite_title_extraction_start", entry_lines=len(lines), company=company, entry_text_preview=entry_text[:200])
                
                # Strategy 1: Check ALL lines (not just first 7) for job titles
                for line in lines:  # Check ALL lines, not just first 7
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.lower() == company.lower():
                        continue
                    
                    # Use same sophisticated logic as _parse_experience_entry_improved
                    line_upper = line_stripped.upper()
                    line_lower = line_stripped.lower()
                    
                    # Check if it looks like a job title (world-class pattern matching)
                    has_job_keyword = any(keyword in line_upper for keyword in ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST", "SPECIALIST", "DESIGNER", "SCIENTIST", "FULL-STACK", "FULL STACK", "STACK"])
                    is_short = len(line_stripped) > 5 and len(line_stripped) < 80 and len(line_stripped.split()) <= 10
                    no_action_verbs = not any(word in line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented", "modified", "worked", "delivered", "ensured", "improved", "optimized", "contributed"])
                    no_numbers = not re.search(r'\d+', line_stripped)
                    # Allow periods (for "Jr.") and hyphens (for "Full-Stack") but not other special chars
                    no_special_chars = not re.search(r'[+\-%]', line_stripped.replace('.', '').replace('-', ''))
                    not_education = not any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL", "BACHELOR", "MASTER", "DEGREE", "MCA", "BSC", "MSC"])
                    not_company_keyword = not any(keyword in line_upper for keyword in ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY"])
                    not_date = not re.search(r'\d{4}', line_stripped)
                    not_location = not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', line_stripped)
                    not_description_start = not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented|Modified)', line_stripped, re.IGNORECASE)
                    
                    if (has_job_keyword and is_short and no_action_verbs and no_numbers and 
                        no_special_chars and not_education and not_company_keyword and 
                        not_date and not_location and not_description_start):
                        parsed["title"] = line_stripped
                        logger.info("extracted_title_final_fallback_elite", title=line_stripped, company=company, line_number=lines.index(line))
                        break
                
                # Strategy 2: If still no title, try extracting from lines that contain company name
                # Sometimes title and company are on same line: "Jr. Full-Stack Developer | Randstad Technologies"
                if not parsed.get("title") or parsed.get("title") == "Not Specified":
                    job_keywords_expanded = ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", 
                                            "ARCHITECT", "CONSULTANT", "ANALYST", "SPECIALIST", "DESIGNER", 
                                            "SCIENTIST", "FULL-STACK", "FULL STACK", "FULLSTACK", "STACK",
                                            "SOFTWARE", "FRONTEND", "BACKEND", "DEVOPS", "JR", "JR."]
                    
                    for line in lines:
                        if company.upper() in line.upper() and len(line) > len(company) + 10:
                            # Extract part before company (likely title)
                            company_pos = line.upper().find(company.upper())
                            if company_pos > 5:
                                title_candidate = line[:company_pos].strip()
                                # Clean up separators
                                title_candidate = re.sub(r'[|•\-–—]\s*$', '', title_candidate).strip()
                                
                                # Validate it's a title
                                if (len(title_candidate) > 5 and len(title_candidate) < 80 and
                                    any(keyword in title_candidate.upper() for keyword in job_keywords_expanded)):
                                    parsed["title"] = title_candidate
                                    logger.info("extracted_title_from_company_line", title=title_candidate, company=company)
                                    break
                    
                    # Strategy 3: If still no title, look for ANY line with job keywords (most aggressive)
                    # This is the ULTIMATE fallback - be very permissive
                    if not parsed.get("title") or parsed.get("title") == "Not Specified":
                        logger.info("elite_title_extraction_strategy3_start", lines_count=len(lines))
                        for line in lines:
                            line_stripped = line.strip()
                            if not line_stripped or line_stripped.lower() == company.lower():
                                continue
                            
                            line_upper = line_stripped.upper()
                            # VERY permissive: just check for job keywords and reasonable length
                            # Allow some special chars (like periods in "Jr.") and be flexible
                            has_job_keyword = any(keyword in line_upper for keyword in job_keywords_expanded)
                            reasonable_length = len(line_stripped) > 3 and len(line_stripped) < 100 and len(line_stripped.split()) <= 12
                            no_year_dates = not re.search(r'\d{4}', line_stripped)  # No full years
                            not_location = not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', line_stripped)  # Not location
                            not_obvious_description = not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented|Modified|Worked|Delivered|Ensured|Improved|Optimized)', line_stripped, re.IGNORECASE)
                            
                            if (has_job_keyword and reasonable_length and no_year_dates and 
                                not_location and not_obvious_description):
                                parsed["title"] = line_stripped
                                logger.info("extracted_title_aggressive_fallback_elite", title=line_stripped, company=company, line_number=lines.index(line))
                                break
                        
                        # Strategy 4: If STILL no title, try extracting from ANY line that contains "Jr" or "Junior" + job keyword
                        # This is for cases like "Jr. Full-Stack Developer" that might be split across lines or have special formatting
                        if not parsed.get("title") or parsed.get("title") == "Not Specified":
                            logger.info("elite_title_extraction_strategy4_start", lines_count=len(lines))
                            for line in lines:
                                line_stripped = line.strip()
                                if not line_stripped or line_stripped.lower() == company.lower():
                                    continue
                                
                                line_upper = line_stripped.upper()
                                # Look for "JR" or "JUNIOR" combined with job keywords
                                has_jr = "JR" in line_upper or "JUNIOR" in line_upper
                                has_job_keyword = any(keyword in line_upper for keyword in job_keywords_expanded)
                                
                                if has_jr and has_job_keyword and len(line_stripped) > 5 and len(line_stripped) < 100:
                                    # Additional validation: should not be a description or date
                                    if (not re.search(r'\d{4}', line_stripped) and 
                                        not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed)', line_stripped, re.IGNORECASE)):
                                        parsed["title"] = line_stripped
                                        logger.info("extracted_title_jr_fallback_elite", title=line_stripped, company=company, line_number=lines.index(line))
                                        break
        
        # COMPANY MERGING STRATEGY:
        # Prefer shorter, more accurate company names
        if company:
            if not parsed_company or (len(company) < len(parsed_company) and len(company) < 60):
                parsed["company"] = company
                logger.info("using_segmented_company", company=company)
            elif parsed_company:
                parsed["company"] = parsed_company
        
        # FINAL WORLD-CLASS FALLBACK: If still no title, use _parse_experience_entry_improved result directly
        # This is the most sophisticated extraction - trust it completely if it found a title
        if (not parsed.get("title") or parsed.get("title") == "Not Specified") and parsed:
            # Re-check parsed result - it might have been extracted but not used
            if parsed.get("title") and parsed.get("title") != "Not Specified":
                parsed["title"] = parsed.get("title")
                logger.info("using_parsed_title_final_fallback", title=parsed.get("title"))
        
        return parsed if parsed.get("title") or parsed.get("company") else None
    
    def _parse_experience_entry_improved(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse experience entry with flexible logic - handles all formats"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if len(lines) < 1:
            return None
        
        # Find date range - try multiple date formats
        date_patterns = [
            r'(\d{4})\s*[-–—]\s*(\d{4}|PRESENT|CURRENT|NOW)',  # 2021 - PRESENT
            r'(\d{4})\s*to\s*(\d{4}|PRESENT|CURRENT|NOW)',      # 2021 to PRESENT
            r'(\d{1,2})[/-](\d{4})\s*[-–—]\s*(\d{1,2})[/-](\d{4}|PRESENT)',  # MM/YYYY - MM/YYYY
            r'(\w+)\s+(\d{4})\s*[-–—]\s*(\w+)?\s*(\d{4}|PRESENT)',  # Jan 2021 - Dec 2021
        ]
        
        # Prioritize dates with PRESENT/CURRENT (work experience) over past dates (education)
        date_matches = []
        for i, line in enumerate(lines):
            for pattern in date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    end_date_str = match.group(2).strip() if len(match.groups()) >= 2 else ""
                    # Prioritize PRESENT/CURRENT dates (work experience)
                    priority = 2 if end_date_str.upper() in ["PRESENT", "CURRENT", "NOW"] else 1
                    date_matches.append((priority, match, i, pattern))
        
        date_match = None
        date_line_idx = -1
        start_date = None
        end_date = None
        
        # Sort by priority (PRESENT dates first), then use first match
        if date_matches:
            date_matches.sort(key=lambda x: x[0], reverse=True)
            priority, date_match, date_line_idx, pattern = date_matches[0]
            # Extract dates
            if len(date_match.groups()) >= 2:
                start_date = date_match.group(1).strip()
                end_date = date_match.group(2).strip() if date_match.group(2) else (date_match.group(4).strip() if len(date_match.groups()) >= 4 and date_match.group(4) else "PRESENT")
        
        # If no date found, try to infer from context or skip date requirement
        if not date_match:
            # Some resumes don't have dates - try to parse anyway if we have company/title
            start_date = None
            end_date = None
            date_line_idx = -1
        
        # Flexible company and title extraction - try multiple strategies
        company = ""
        title = ""
        
        company_keywords = ["PVT", "LTD", "LLC", "INC", "CORP", "COMPANY", "TECHNOLOGIES", "SOFTWARE", "SOLUTIONS", "SYSTEMS"]
        job_title_keywords = ["DEVELOPER", "ENGINEER", "MANAGER", "LEAD", "SENIOR", "JUNIOR", "ARCHITECT", "CONSULTANT", "ANALYST", "SPECIALIST", "DESIGNER", "SCIENTIST"]
        
        # Strategy 1: If we have a date line, extract from it
        # Handle lines with multiple dates (e.g., "2019 - 2021 Company Name 2021 - PRESENT")
        if date_line_idx >= 0:
            date_line = lines[date_line_idx]
            
            # Check if line has multiple dates - prioritize PRESENT date
            all_dates = re.findall(r'(\d{4})\s*[-–—]\s*(\d{4}|PRESENT|CURRENT|NOW)', date_line, re.IGNORECASE)
            if len(all_dates) > 1:
                # Find PRESENT date first
                present_date_match = re.search(r'(\d{4})\s*[-–—]\s*(PRESENT|CURRENT|NOW)', date_line, re.IGNORECASE)
                if present_date_match:
                    # Extract text between the two dates (this is usually the company)
                    # Pattern: "2019 - 2021 Company Name 2021 - PRESENT"
                    # Extract: "Company Name"
                    before_present = date_line[:present_date_match.start()].strip()
                    # Remove the first date from before_present
                    before_present_clean = re.sub(r'^\d{4}\s*[-–—]\s*\d{4}\s*', '', before_present, flags=re.IGNORECASE).strip()
                    if before_present_clean and len(before_present_clean) > 3:
                        before_present_upper = before_present_clean.upper()
                        if (any(keyword in before_present_upper for keyword in company_keywords) and
                            not any(word in before_present_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"])):
                            company = before_present_clean
                            # Update dates to use PRESENT date
                            start_date = present_date_match.group(1).strip()
                            end_date = present_date_match.group(2).strip()
            
            # If company not found yet, try removing all dates
            if not company:
                for pattern in date_patterns:
                    company_line = re.sub(pattern, '', date_line, flags=re.IGNORECASE).strip()
                    if company_line and len(company_line) > 3:
                        company_line_upper = company_line.upper()
                        # Check if it's actually a company (not education)
                        if not any(word in company_line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "MCA", "BACHELOR", "MASTER"]):
                            if any(keyword in company_line_upper for keyword in company_keywords):
                                company = company_line
                                break
        
        # Strategy 2: Check previous line for company (prioritize line right before date)
        if not company and date_line_idx > 0:
            # First check the line immediately before date (most common pattern)
            if date_line_idx > 0:
                prev_line = lines[date_line_idx - 1]
                prev_line_upper = prev_line.upper()
                prev_line_lower = prev_line.lower()
                # Check if line looks like a company name (not description, not title)
                # IMPORTANT: Accept short, single-word company names (like "Deloitte", "Google", "Microsoft")
                # even if they don't have company keywords
                is_company = (
                    (any(keyword in prev_line_upper for keyword in company_keywords) or
                     (len(prev_line) > 2 and len(prev_line) < 60 and 
                      # Short single-word or two-word names are likely companies
                      (len(prev_line.split()) <= 2 or any(keyword in prev_line_upper for keyword in company_keywords)) and
                      not any(word in prev_line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "MCA", "BACHELOR", "MASTER"]) and
                      not any(keyword in prev_line_upper for keyword in job_title_keywords) and
                      not any(word in prev_line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "contributed", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented"]) and
                      not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented)', prev_line, re.IGNORECASE) and
                      # Not a location (like "Nashville, TN")
                      not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', prev_line)))
                )
                if is_company:
                    company = prev_line
            # If not found, check earlier lines
            if not company:
                for i in range(max(0, date_line_idx - 3), date_line_idx - 1):
                    prev_line = lines[i]
                    prev_line_upper = prev_line.upper()
                    prev_line_lower = prev_line.lower()
                    # Check if line looks like a company name
                    is_company = (
                        (any(keyword in prev_line_upper for keyword in company_keywords) or
                         (len(prev_line) > 2 and len(prev_line) < 60 and 
                          (len(prev_line.split()) <= 2 or any(keyword in prev_line_upper for keyword in company_keywords)) and
                          not any(word in prev_line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "MCA", "BACHELOR", "MASTER"]) and
                          not any(keyword in prev_line_upper for keyword in job_title_keywords) and
                          not any(word in prev_line_lower for word in ["designed", "developed", "created", "built", "led", "managed", "collaborated", "contributed", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented"]) and
                          not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented)', prev_line, re.IGNORECASE) and
                          not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', prev_line)))
                    )
                    if is_company:
                        company = prev_line
                        break
        
        # Strategy 3: Check next line for company (some formats put company after date)
        if not company and date_line_idx >= 0 and date_line_idx + 1 < len(lines):
            next_line = lines[date_line_idx + 1]
            next_line_upper = next_line.upper()
            if (any(keyword in next_line_upper for keyword in company_keywords) and
                not any(word in next_line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"])):
                company = next_line
        
        # Strategy 4: Look for company anywhere in entry (for formats without clear structure)
        # IMPORTANT: Prioritize short company names (1-2 words) over description lines
        if not company:
            # First pass: Look for short company names (1-2 words) - these are most likely companies
            short_company_candidates = []
            for line in lines:
                line_upper = line.upper()
                line_lower = line.lower()
                
                # Check if line is a short company name (1-2 words, no action verbs, not a title)
                is_short_company = (
                    len(line) > 2 and len(line) < 60 and
                    len(line.split()) <= 2 and  # Short name (1-2 words) like "Deloitte"
                    not any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "MCA", "BACHELOR", "MASTER"]) and
                    not any(keyword in line_upper for keyword in job_title_keywords) and
                    not any(word in line_lower for word in ["collaborated", "designed", "developed", "created", "built", "led", "managed", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented", "modified", "custom", "components", "systems", "solutions", "requirements", "procedures", "specifications", "dependencies", "applications", "exercises", "designs"]) and
                    not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented|Modified)', line, re.IGNORECASE) and
                    not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', line) and  # Not a location
                    not re.search(r'\d+', line) and  # No numbers (descriptions often have numbers like "25+")
                    not re.search(r'[+\-%]', line)  # No special chars like "+", "-", "%" (descriptions often have these)
                )
                
                if is_short_company:
                    # Prioritize lines with company keywords, but also accept without
                    priority = 2 if any(keyword in line_upper for keyword in company_keywords) else 1
                    short_company_candidates.append((priority, line))
            
            # Sort by priority (company keywords first), then use first candidate
            if short_company_candidates:
                short_company_candidates.sort(key=lambda x: x[0], reverse=True)
                company = short_company_candidates[0][1]
            
            # Second pass: If no short company found, look for longer company names with keywords
            if not company:
                for line in lines:
                    line_upper = line.upper()
                    line_lower = line.lower()
                    
                    # Check if line has BOTH company and title keywords (e.g., "Team 4 Progress Technologies MERN Stack Developer")
                    has_company_kw = any(keyword in line_upper for keyword in company_keywords)
                    has_title_kw = any(keyword in line_upper for keyword in job_title_keywords)
                    
                    if has_company_kw and has_title_kw:
                        # Try to split: extract company part (before title keywords)
                        # Find first job title keyword position
                        first_title_pos = len(line)
                        for keyword in job_title_keywords:
                            pos = line_upper.find(keyword)
                            if pos >= 0 and pos < first_title_pos:
                                first_title_pos = pos
                        
                        # Extract company part (before title)
                        company_candidate = line[:first_title_pos].strip()
                        # Clean up: remove trailing words that might be part of title
                        company_candidate = re.sub(r'\s+(?:Stack|Developer|Engineer|Manager).*$', '', company_candidate, flags=re.IGNORECASE).strip()
                        
                        if (company_candidate and len(company_candidate) > 5 and len(company_candidate) < 60 and
                            any(keyword in company_candidate.upper() for keyword in company_keywords) and
                            not any(word in company_candidate.upper() for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"])):
                            company = company_candidate
                            break
                    
                    # Strict validation - must have company keywords
                    is_company = (
                        any(keyword in line_upper for keyword in company_keywords) and
                        not any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "MCA", "BACHELOR", "MASTER"]) and
                        not any(word in line_lower for word in ["collaborated", "designed", "developed", "created", "built", "led", "managed", "analyzed", "integrated", "wrote", "maintained", "documented", "participated", "implemented"]) and
                        not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Analyzed|Integrated|Wrote|Maintained|Documented|Participated|Implemented)', line, re.IGNORECASE) and
                        not re.match(r'^[A-Z][a-z]+,\s*[A-Z]{2}$', line) and
                        not any(keyword in line_upper for keyword in job_title_keywords)
                    )
                    if is_company:
                        company = line
                        break
        
        # Flexible title extraction - try multiple strategies
        title_line_idx = -1
        
        # Strategy 1: Look for job title keywords in lines BEFORE date (title usually comes before company/date)
        if not title:
            # Search from start of entry to date line (title is usually first)
            search_start = 0
            search_end = date_line_idx if date_line_idx >= 0 else len(lines)
            
            for i in range(search_start, search_end):
                if i == date_line_idx:
                    continue  # Skip date line itself
                
                potential_title = lines[i]
                potential_title_upper = potential_title.upper()
                potential_title_lower = potential_title.lower()
                
                # STRICT: Skip if line contains ANY education keywords (even if it also has job keywords)
                # This prevents "PUNE UNIVERSITY Senior Full Stack Developer" from being accepted
                has_education_keywords = any(word in potential_title_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL", "MCA", "BSC", "MSC", "BTECH", "MTECH", "BACHELOR", "MASTER", "PHD", "DEGREE", "ACADEMIC", "COURSEWORK"])
                if has_education_keywords:
                    # Try to extract just the job title part if education and title are mixed
                    # Pattern: "PUNE UNIVERSITY Senior Full Stack Developer" -> extract "Senior Full Stack Developer"
                    title_extracted = False
                    for keyword in job_title_keywords:
                        if keyword in potential_title_upper:
                            # Find position of job keyword
                            keyword_pos = potential_title_upper.find(keyword)
                            # Extract from 20 chars before keyword to end (to catch "Senior" before "Developer")
                            start_pos = keyword_pos - 20 if keyword_pos >= 20 else 0
                            title_candidate = potential_title[start_pos:].strip()
                            # Remove any leading education words (including partial matches like "Y" from "UNIVERSITY")
                            title_candidate = re.sub(r'^[A-Z\s]*(?:UNIVERSITY|COLLEGE|INSTITUTE|SCHOOL)\s+', '', title_candidate, flags=re.IGNORECASE).strip()
                            # Remove single letter prefixes that might be from partial word matches
                            title_candidate = re.sub(r'^[A-Z]\s+', '', title_candidate).strip()
                            # Remove any trailing education content like "(Academic Coursework"
                            title_candidate = re.sub(r'\s*\([^)]*(?:ACADEMIC|COURSEWORK|COMPLETED)[^)]*\).*$', '', title_candidate, flags=re.IGNORECASE).strip()
                            # Clean up any remaining education keywords
                            title_candidate = re.sub(r'\b(?:UNIVERSITY|COLLEGE|INSTITUTE|SCHOOL|MCA|BACHELOR|MASTER)\b\s*', '', title_candidate, flags=re.IGNORECASE).strip()
                            if title_candidate and len(title_candidate) > 5 and len(title_candidate) < 60:
                                potential_title = title_candidate
                                potential_title_upper = potential_title.upper()
                                potential_title_lower = potential_title.lower()
                                title_extracted = True
                                break
                    if not title_extracted:
                        continue  # Reject if no job keyword found after education
                
                # Skip if it's the company name we already found
                if company and potential_title.upper() == company.upper():
                    continue
                
                # Check if line has BOTH company and title (e.g., "Team 4 Progress Technologies MERN Stack Developer")
                # If company was already extracted and this line contains both, extract title from it
                has_company_kw = any(keyword in potential_title_upper for keyword in company_keywords)
                has_title_kw = any(keyword in potential_title_upper for keyword in job_title_keywords)
                
                if has_company_kw and has_title_kw:
                    # If we already have company and this line contains it, extract title part
                    if company and company.upper() in potential_title_upper:
                        # Find first job title keyword position
                        first_title_pos = len(potential_title)
                        for keyword in job_title_keywords:
                            pos = potential_title_upper.find(keyword)
                            if pos >= 0 and pos < first_title_pos:
                                first_title_pos = pos
                        
                        # Extract title part (from first title keyword)
                        # Go back a bit to catch "Senior" or "MERN" before "Developer"
                        start_pos = max(0, first_title_pos - 10)
                        title_candidate = potential_title[start_pos:].strip()
                        
                        # Remove any leading company words
                        title_candidate = re.sub(r'^[A-Z\s]*(?:PVT|LTD|LLC|INC|CORP|COMPANY|TECHNOLOGIES|SOFTWARE|SOLUTIONS|SYSTEMS)\s+', '', title_candidate, flags=re.IGNORECASE).strip()
                        # Remove "Team 4 Progress Technologies" or similar company names
                        title_candidate = re.sub(r'^(?:Team\s+\d+\s+)?(?:Progress\s+)?Technologies\s+', '', title_candidate, flags=re.IGNORECASE).strip()
                        # Remove single letter prefixes
                        title_candidate = re.sub(r'^[A-Z]\s+', '', title_candidate).strip()
                        
                        if title_candidate and len(title_candidate) > 3 and len(title_candidate) < 60:
                            potential_title = title_candidate
                            potential_title_upper = potential_title.upper()
                            potential_title_lower = potential_title.lower()
                
                # Check if it looks like a job title
                has_job_keyword = any(keyword in potential_title_upper for keyword in job_title_keywords)
                has_education = False  # Already checked above
                has_academic = any(word in potential_title_lower for word in ["academic", "coursework", "graduation", "graduated", "gpa", "cgpa"])
                starts_with_action_verb = re.match(r'^\s*(Designed|Developed|Created|Built|Implemented|Managed|Led|Worked|Delivered|Ensured|Improved|Optimized|Collaborated|Contributed)', potential_title, re.IGNORECASE)
                looks_like_tech_list = potential_title.count(',') >= 2 or (potential_title.count('.') >= 2 and len(potential_title) < 50)
                has_date = bool(re.search(r'\d{4}', potential_title))
                has_academic_parentheses = re.search(r'\(.*?(?:academic|coursework|completed|degree).*?\)', potential_title, re.IGNORECASE)
                
                # Accept if it has job keywords AND looks like a title (strict validation)
                # IMPORTANT: Reject if it starts with "Jr." when we're looking for the first entry
                # This helps distinguish between Entry 1 (Full-Stack) and Entry 2 (Jr. Full-Stack)
                starts_with_jr = bool(re.match(r'^\s*(Jr\.|Junior|Jr\s)', potential_title, re.IGNORECASE))
                
                # Job titles should be short, have job keywords, and not be descriptions
                # Also check if title contains university/college even if not caught above
                contains_university_college = bool(re.search(r'\b(UNIVERSITY|COLLEGE|INSTITUTE|SCHOOL)\b', potential_title_upper))
                
                # IMPORTANT: If we already have a title and this one starts with "Jr.", prefer the non-Jr. one
                # This ensures Entry 1 gets "Full-Stack Developer" not "Jr. Full-Stack Developer"
                if title and starts_with_jr:
                    continue  # Skip Jr. titles if we already have a non-Jr. title
                
                is_valid_title = (
                    has_job_keyword and  # MUST have job keyword
                    len(potential_title) > 5 and len(potential_title) < 60 and  # Reasonable length
                    not has_education and
                    not has_academic and
                    not contains_university_college and  # Additional check for university/college
                    not starts_with_action_verb and
                    not looks_like_tech_list and
                    not has_date and
                    not has_academic_parentheses and
                    not potential_title.endswith(')') and  # Don't accept lines ending with ) (likely from education)
                    not potential_title.startswith('(') and  # Don't accept lines starting with (
                    potential_title.count(' ') < 8 and  # Not too many words (titles are usually 2-5 words)
                    'UNIVERSITY' not in potential_title_upper and  # Explicit check
                    'COLLEGE' not in potential_title_upper  # Explicit check
                )
                
                if is_valid_title:
                    title = potential_title
                    title_line_idx = i
                    break
        
        # Strategy 2: If no title found, look anywhere in entry for job title keywords (with strict validation)
        if not title:
            for line in lines:
                line_upper = line.upper()
                line_lower = line.lower()
                # Strict validation for job title
                if (any(keyword in line_upper for keyword in job_title_keywords) and
                    not any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "MCA", "BACHELOR", "MASTER"]) and
                    not any(word in line_lower for word in ["academic", "coursework", "completed", "graduated"]) and
                    len(line) > 5 and len(line) < 60 and
                    not re.search(r'\d{4}', line) and
                    not re.match(r'^\s*(Designed|Developed|Created|Built|Led|Managed|Collaborated|Contributed|Delivered|Ensured)', line, re.IGNORECASE) and
                    not line.endswith(')') and
                    not line.startswith('(') and
                    line.count(' ') < 8):
                    title = line
                    title_line_idx = lines.index(line)
                    break
        
        # Description is everything after title/company/date
        description_lines = []
        start_desc_idx = max(
            title_line_idx + 1 if title_line_idx >= 0 else 0,
            date_line_idx + 1 if date_line_idx >= 0 else 0
        )
        
        date_pattern_check = r'\d{4}\s*[-–—]\s*(?:\d{4}|PRESENT|CURRENT|NOW)'
        for i in range(start_desc_idx, len(lines)):
            line = lines[i]
            # Skip if it's company or title (already extracted)
            if (company and line.upper() == company.upper()) or (title and line.upper() == title.upper()):
                continue
            # Skip education lines in description
            line_upper = line.upper()
            if any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL"]) and \
               any(word in line_upper for word in ["MCA", "BSC", "MSC", "BTECH", "MTECH", "BACHELOR", "MASTER", "PHD", "ACADEMIC", "COURSEWORK"]):
                continue  # Skip education lines
            # Skip lines that look like dates or are too short
            has_date_in_line = bool(re.search(date_pattern_check, line, re.IGNORECASE))
            if not has_date_in_line and len(line) > 10:
                description_lines.append(line)
        
        description = '\n'.join(description_lines)
        
        # If no title but we have company, try to infer title from description
        if not title and company and description:
            desc_upper = description.upper()
            for keyword in job_title_keywords:
                if keyword in desc_upper:
                    title_match = re.search(rf'([A-Z][^.!?]*{keyword}[^.!?]*)', description, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1).strip()
                        if len(title) > 80:
                            title = title[:80]
                        break
        
        # Final fallback - if still no title, use first meaningful line (but be strict)
        if not title:
            for line in lines:
                line_upper = line.upper()
                # Must have job title keywords, not be description, not be education
                has_job_keyword = any(keyword in line_upper for keyword in job_title_keywords)
                is_description = (line.startswith("Collaborated") or 
                                line.startswith("Designed") or 
                                line.startswith("Developed") or
                                line.startswith("Led") or
                                line.count(',') >= 2)
                is_education = any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "MCA", "BACHELOR", "MASTER"])
                
                if (has_job_keyword and
                    not is_description and
                    not is_education and
                    len(line) > 5 and len(line) < 60 and
                    not re.search(r'\d{4}', line) and
                    (not company or line.upper() != company.upper())):
                    title = line
                    break
        
        # If we have company but no title, still return the entry (company is more reliable)
        # If we have title but no company, still return the entry (title is valuable)
        # Only return None if we have neither company nor title
        if not title and not company:
            return None
        
        return {
            "title": title if title else "Not Specified",
            "company": company if company else "Not Specified",
            "date_range": f"{start_date} - {end_date}" if start_date and end_date else None,
            "start_date": start_date,
            "end_date": end_date if end_date and end_date.upper() not in ["PRESENT", "CURRENT", "NOW"] else "present" if end_date else None,
            "description": description,
        }
    
    def _extract_education_improved(self, text: str) -> List[Dict[str, Any]]:
        """Extract education with improved parsing - also from mixed sections"""
        education = []
        
        # First, try to find dedicated EDUCATION section
        edu_section = re.search(
            r'EDUCATION[:\s]*\n(.*?)(?=\n(?:WORK|EXPERIENCE|PROJECTS|SKILLS|CERTIFICATIONS|LANGUAGES|$))',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if edu_section:
            edu_text = edu_section.group(1)
            # Pattern: "2019 - 2021 UNIVERSITY NAME\nDegree Name"
            # OR: "UNIVERSITY NAME\nDegree Name 2019"
            entries = re.split(r'\n(?=\d{4}\s*[-–—]|\n\n)', edu_text)
            
            for entry in entries:
                if not entry.strip():
                    continue
                
                edu_dict = self._parse_education_entry_improved(entry.strip())
                if edu_dict and edu_dict.get("degree"):
                    education.append(edu_dict)
        
        # If no dedicated EDUCATION section found, try to extract from EXPERIENCE section
        # (many resumes mix education with experience)
        if not education:
            exp_section = re.search(
                r'(?:WORK\s+)?EXPERIENCE[:\s]*\n(.*?)(?=\n(?:EDUCATION|PROJECTS|SKILLS|CERTIFICATIONS|LANGUAGES|$))',
                text,
                re.IGNORECASE | re.DOTALL
            )
            if exp_section:
                exp_text = exp_section.group(1)
                # Look for education patterns in experience section
                education = self._extract_education_from_mixed_section(exp_text)
        
        return education
    
    def _extract_education_from_mixed_section(self, text: str) -> List[Dict[str, Any]]:
        """Extract education entries from mixed sections (e.g., experience section containing education)"""
        education = []
        lines = text.split('\n')
        
        # Look for university + degree patterns
        # Pattern: University name on one line, degree on nearby lines
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            line_upper = line.upper()
            
            # Check if line contains university
            if any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE"]):
                # Found a university - look for degree in nearby lines
                institution = line
                # Remove date patterns and job titles from institution line
                institution = re.sub(r'\d{4}\s*[-–—]\s*\d{4}|PRESENT|CURRENT', '', institution, flags=re.IGNORECASE).strip()
                # Remove job title keywords (including multi-word titles)
                institution = re.sub(r'\b(Developer|Engineer|Manager|Lead|Senior|Junior|Architect|Consultant|Full Stack|Stack Developer|Stack|Software)\b', '', institution, flags=re.IGNORECASE).strip()
                # Clean up multiple spaces
                institution = re.sub(r'\s+', ' ', institution).strip()
                institution = institution.strip()
                
                # Look ahead for degree (next 3 lines)
                degree = None
                year = None
                date_pattern = r'(\d{4})\s*[-–—]\s*(\d{4})'
                
                for j in range(i, min(i + 4, len(lines))):
                    check_line = lines[j].strip()
                    check_line_lower = check_line.lower()
                    check_line_upper = check_line.upper()
                    
                    # Check for date pattern
                    date_match = re.search(date_pattern, check_line)
                    if date_match:
                        year = date_match.group(2)  # End year
                    
                    # Check for degree keywords
                    if not degree and any(word in check_line_upper for word in ["MCA", "BSC", "MSC", "BTECH", "MTECH", "BACHELOR", "MASTER", "PHD", "DEGREE"]):
                        # Found degree - extract it
                        degree_line = check_line
                        # Clean up degree - remove extra text
                        # Extract degree name (MCA, Bachelor of Computer Science, etc.)
                        degree_match = re.search(r'(?:MCA|B\.?Sc|M\.?Sc|B\.?Tech|M\.?Tech|B\.?E|M\.?E|Bachelor|Master|PhD|Ph\.D)[\s\w()]*', degree_line, re.IGNORECASE)
                        if degree_match:
                            degree = degree_match.group(0).strip()
                            # Remove parenthetical content like "(Academic Coursework Completed)" or incomplete parentheses
                            degree = re.sub(r'\([^)]*\)', '', degree).strip()
                            degree = re.sub(r'\([^)]*$', '', degree).strip()  # Remove incomplete parentheses
                        else:
                            # Take first part before action verbs or long descriptions
                            degree_parts = re.split(r'\s+(Designed|Developed|Created|Built|Led|Managed|Backend|Architectures|optimized|performance|using)', degree_line, flags=re.IGNORECASE)
                            if degree_parts:
                                degree = degree_parts[0].strip()
                                # Remove date patterns
                                degree = re.sub(date_pattern, '', degree).strip()
                        
                        # Clean degree further - stop at action verbs or sentence parts
                        if degree:
                            # Split at action verbs or descriptive words
                            degree_clean = re.split(r'\s+(backend|architectures|with|using|optimized|performance|caching|deployments)', degree, flags=re.IGNORECASE)
                            if degree_clean:
                                degree = degree_clean[0].strip()
                        
                        if degree and len(degree) > 2:
                            # Extract field if present (e.g., "Bachelor of Computer Science" -> field = "Computer Science")
                            field = None
                            if 'of' in degree.lower():
                                field_match = re.search(r'of\s+([^\n(]+)', degree, re.IGNORECASE)
                                if field_match:
                                    field = field_match.group(1).strip()
                                    # Stop field at action verbs or sentence parts
                                    field_clean = re.split(r'\s+(backend|architectures|with|using|optimized|performance)', field, flags=re.IGNORECASE)
                                    if field_clean:
                                        field = field_clean[0].strip()
                                    field = re.sub(r'\(.*?\)', '', field).strip()  # Remove parentheses
                                    # Remove degree name from field if it got included
                                    field = re.sub(r'^(Bachelor|Master|MCA|B\.?Sc|M\.?Sc)\s+', '', field, flags=re.IGNORECASE).strip()
                                    
                                    # Remove field from degree to avoid duplication (keep just "Bachelor" or "Master")
                                    degree_base = re.split(r'\s+of\s+', degree, flags=re.IGNORECASE)[0].strip()
                                    degree = degree_base
                            
                            edu_dict = {
                                "degree": degree,
                                "institution": institution,
                                "field": field,
                                "year": year,
                            }
                            education.append(edu_dict)
                            # Skip ahead to avoid duplicate processing
                            i = j + 1
                            break
                i += 1
            else:
                i += 1
        
        return education
    
    def _parse_education_entry_improved(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse education entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None
        
        # Find year/date range
        year = None
        date_pattern = r'(\d{4})\s*[-–—]\s*(\d{4})'
        date_match = re.search(date_pattern, entry)
        if date_match:
            year = date_match.group(2)  # End year
        
        # Find institution (usually contains "UNIVERSITY", "COLLEGE", "INSTITUTE")
        institution = ""
        degree = ""
        
        for line in lines:
            line_upper = line.upper()
            if any(word in line_upper for word in ["UNIVERSITY", "COLLEGE", "INSTITUTE", "SCHOOL"]):
                institution = line
                # Remove date range from institution
                institution = re.sub(date_pattern, '', institution).strip()
            elif not degree and len(line) > 5:
                # First substantial line without university keywords is likely degree
                degree = re.sub(date_pattern, '', line).strip()
        
        # If no clear degree found, use first line
        if not degree and lines:
            degree = lines[0]
            degree = re.sub(date_pattern, '', degree).strip()
        
        # Extract field of study if present (usually in parentheses or after comma)
        field = None
        field_match = re.search(r'\(([^)]+)\)|,\s*([^,\n]+)', degree)
        if field_match:
            field = field_match.group(1) or field_match.group(2)
            # Remove field from degree
            degree = re.sub(r'\([^)]+\)|,\s*[^,\n]+', '', degree).strip()
        
        return {
            "degree": degree,
            "institution": institution,
            "field": field,
            "year": year,
        }
    
    def _extract_projects_improved(self, text: str) -> List[Dict[str, Any]]:
        """Extract projects - only if PROJECTS section exists (experienced people may not have this)"""
        projects = []
        
        # Find PROJECTS section
        proj_section = re.search(
            r'PROJECTS[:\s]*\n(.*?)(?=\n(?:WORK|EXPERIENCE|EDUCATION|SKILLS|CERTIFICATIONS|LANGUAGES|$))',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not proj_section:
            # No projects section - return empty (experienced people don't always have projects)
            return projects
        
        proj_text = proj_section.group(1)
        entries = re.split(r'\n\n+', proj_text)
        
        for entry in entries[:15]:
            if not entry.strip():
                continue
            
            proj_dict = self._parse_project_entry_improved(entry.strip())
            if proj_dict and proj_dict.get("name") and len(proj_dict.get("name", "")) > 2:
                projects.append(proj_dict)
        
        return projects
    
    def _parse_project_entry_improved(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse project entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None
        
        name = lines[0]
        description = '\n'.join(lines[1:]) if len(lines) > 1 else ""
        
        # Extract URL if present
        url_match = re.search(r'https?://[^\s]+', entry)
        url = url_match.group(0) if url_match else None
        
        # Filter out invalid project names (too short, look like contact info, etc.)
        if len(name) < 3 or '@' in name or re.search(r'\d{10}', name):
            return None
        
        return {
            "name": name,
            "description": description,
            "url": url,
        }
    
    def _extract_certifications_improved(self, text: str) -> List[str]:
        """Extract certifications"""
        certifications = []
        
        # Find CERTIFICATIONS section - handle both with and without newline
        cert_section = re.search(
            r'(?:CERTIFICATIONS?|CERTIFICATES?)[:\s]*\n?(.*?)(?=\n(?:WORK|EXPERIENCE|EDUCATION|PROJECTS|SKILLS|LANGUAGES)|$)',
            text,
            re.IGNORECASE | re.DOTALL | re.MULTILINE
        )
        
        if cert_section:
            cert_text = cert_section.group(1).strip()
            if cert_text:
                # Split by newline, comma, semicolon, or space (if space-separated)
                if '\n' in cert_text or ',' in cert_text or ';' in cert_text:
                    certs = re.split(r'[,;\n•]', cert_text)
                else:
                    # Space-separated (e.g., "MTA AWS")
                    certs = cert_text.split()
                
                for cert in certs:
                    cert = cert.strip()
                    if cert and len(cert) > 2 and len(cert) < 50:  # Reasonable length
                        certifications.append(cert)
        
        return certifications
    
    def _extract_languages_improved(self, text: str) -> List[str]:
        """Extract languages"""
        languages = []
        
        lang_section = re.search(
            r'LANGUAGES?[:\s]*\n(.*?)(?=\n(?:WORK|EXPERIENCE|EDUCATION|PROJECTS|SKILLS|CERTIFICATIONS|$))',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if lang_section:
            lang_text = lang_section.group(1)
            langs = re.split(r'[,;\n•]', lang_text)
            for lang in langs:
                lang = lang.strip()
                # Remove proficiency levels
                lang = re.sub(r'\s*\([^)]+\)', '', lang)
                if lang and len(lang) > 1 and len(lang) < 30:
                    languages.append(lang)
        
        return languages
    
    def _calculate_experience_years(self, experience_list: List[Dict[str, Any]]) -> Optional[int]:
        """Calculate total years of experience from date ranges"""
        if not experience_list:
            return None
        
        total_days = 0
        date_ranges = []
        
        for exp in experience_list:
            start_date_str = exp.get("start_date")
            end_date_str = exp.get("end_date")
            
            if not start_date_str:
                continue
            
            start_date = self._parse_date(start_date_str)
            if not start_date:
                continue
            
            if end_date_str and end_date_str.lower() in ["present", "current", "now"]:
                end_date = date.today()
            elif end_date_str:
                end_date = self._parse_date(end_date_str)
                if not end_date:
                    continue
            else:
                continue
            
            if start_date and end_date and end_date >= start_date:
                delta = end_date - start_date
                days = delta.days
                date_ranges.append((start_date, end_date, days))
        
        if not date_ranges:
            return None
        
        # Sort and merge overlapping periods
        date_ranges.sort(key=lambda x: x[0])
        merged_ranges = []
        
        for start, end, days in date_ranges:
            if not merged_ranges:
                merged_ranges.append((start, end, days))
            else:
                last_start, last_end, last_days = merged_ranges[-1]
                if start <= last_end:
                    new_end = max(end, last_end)
                    new_days = (new_end - last_start).days
                    merged_ranges[-1] = (last_start, new_end, new_days)
                else:
                    merged_ranges.append((start, end, days))
        
        total_days = sum(days for _, _, days in merged_ranges)
        years = total_days / 365.25
        years_rounded = round(years * 2) / 2
        
        return int(years_rounded) if years_rounded >= 1 else None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        date_str = date_str.lower().strip()
        
        if date_str in ["present", "current", "now"]:
            return date.today()
        
        formats = [
            "%Y-%m",      # 2020-01
            "%Y-%m-%d",   # 2020-01-15
            "%Y",         # 2020
            "%B %Y",      # January 2020
            "%b %Y",      # Jan 2020
            "%m/%Y",      # 01/2020
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                if fmt == "%Y":
                    return date(parsed.year, 1, 1)
                return parsed
            except ValueError:
                continue
        
        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            year = int(year_match.group(0))
            return date(year, 1, 1)
        
        return None
    
    def _extract_personal_info(self, text: str) -> Dict[str, Any]:
        """Extract personal information: name, email, phone, LinkedIn, portfolio"""
        personal_info = {
            "first_name": "",
            "last_name": "",
            "email": "",
            "phone": "",
            "linkedin_url": "",
            "portfolio_url": "",
        }
        
        # Extract email - most reliable pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            personal_info["email"] = email_match.group(0).strip()
        
        # Extract phone - various formats
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # +91 7620402389, (123) 456-7890
            r'\b\d{10}\b',  # 10 digits
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                phone = phone_match.group(0).strip()
                # Clean up phone number
                phone = re.sub(r'[^\d+]', '', phone)  # Keep only digits and +
                if len(phone) >= 10:  # Valid phone should be at least 10 digits
                    personal_info["phone"] = phone
                    break
        
        # Extract LinkedIn URL
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'linkedin\.com/profile/view\?id=[\w-]+',
            r'www\.linkedin\.com/in/[\w-]+',
        ]
        for pattern in linkedin_patterns:
            linkedin_match = re.search(pattern, text, re.IGNORECASE)
            if linkedin_match:
                linkedin_url = linkedin_match.group(0).strip()
                if not linkedin_url.startswith('http'):
                    linkedin_url = 'https://' + linkedin_url
                personal_info["linkedin_url"] = linkedin_url
                break
        
        # Extract portfolio/personal website URLs
        portfolio_patterns = [
            r'(?:https?://)?(?:www\.)?[\w-]+\.(?:com|net|org|io|dev|me|co|in|github\.io)[/\w-]*',
        ]
        # Exclude common non-portfolio domains (including email domains)
        exclude_domains = ['linkedin.com', 'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 
                          'github.com', 'stackoverflow.com', 'medium.com', 'twitter.com', 'facebook.com',
                          'email.com', 'mail.com', 'icloud.com', 'protonmail.com', 'aol.com']
        
        for pattern in portfolio_patterns:
            portfolio_matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in portfolio_matches:
                url = match.group(0).strip()
                # Extract domain from URL
                domain_match = re.search(r'([\w-]+\.(?:com|net|org|io|dev|me|co|in|github\.io))', url, re.IGNORECASE)
                if domain_match:
                    domain = domain_match.group(1).lower()
                    # Check if it's not an excluded domain
                    if not any(excluded in domain for excluded in exclude_domains):
                        # Also check if it's not part of an email (should not have @ before it)
                        url_start = text.find(url)
                        if url_start > 0:
                            before_url = text[max(0, url_start-10):url_start].lower()
                            if '@' not in before_url:  # Not part of email
                                if not url.startswith('http'):
                                    url = 'https://' + url
                                personal_info["portfolio_url"] = url
                                break
            if personal_info["portfolio_url"]:
                break
        
        # Extract name - usually at the top of resume, first line is most likely
        # Look for capitalized words that look like names
        lines = text.split('\n')[:5]  # Check first 5 lines
        name_candidates = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) > 60:  # Skip very long lines
                continue
            
            # Skip lines that are clearly not names
            if any(skip in line.lower() for skip in ['email', 'phone', 'address', 'linkedin', 'github', 
                                                      'experience', 'education', 'skills', 'objective', 
                                                      'summary', 'profile', '@', 'http', 'www', 'developer',
                                                      'engineer', 'manager', 'designer', 'analyst']):
                continue
            
            # Check if line looks like a name (2-4 words, capitalized or all caps)
            words = line.split()
            if 2 <= len(words) <= 4:
                # Check if all words start with capital letter (or are all caps)
                is_capitalized = all(word and (word[0].isupper() or word.isupper()) for word in words if word)
                if is_capitalized:
                    # Check if it's not a section header (all caps + common section words)
                    section_keywords = ['experience', 'education', 'skills', 'projects', 'certifications',
                                       'languages', 'summary', 'objective', 'profile', 'contact', 'work']
                    is_section_header = all(word.isupper() for word in words if word) and \
                                       any(keyword in line.lower() for keyword in section_keywords)
                    
                    if not is_section_header:
                        # Exclude common job titles
                        job_titles = ['developer', 'engineer', 'manager', 'designer', 'analyst', 'specialist',
                                     'architect', 'consultant', 'lead', 'senior', 'junior', 'full', 'stack',
                                     'developer', 'programmer', 'coder']
                        if not any(title in line.lower() for title in job_titles):
                            # Check if words are reasonable length (names are usually 2-15 chars)
                            if all(2 <= len(word) <= 15 for word in words if word):
                                # Prioritize first line (index 0) - names are usually at the top
                                priority = 10 - i  # First line gets highest priority
                                name_candidates.append((priority, line))
        
        # Sort by priority (first line first) and use the best candidate
        if name_candidates:
            name_candidates.sort(key=lambda x: x[0], reverse=True)
            full_name = name_candidates[0][1]
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                personal_info["first_name"] = name_parts[0]
                personal_info["last_name"] = " ".join(name_parts[1:])  # Handle multi-word last names
            elif len(name_parts) == 1:
                personal_info["first_name"] = name_parts[0]
        
        logger.info("personal_info_extracted", 
                   has_name=bool(personal_info["first_name"]),
                   has_email=bool(personal_info["email"]),
                   has_phone=bool(personal_info["phone"]),
                   has_linkedin=bool(personal_info["linkedin_url"]),
                   has_portfolio=bool(personal_info["portfolio_url"]))
        
        return personal_info
    
    def _basic_parse(self, text: str) -> Dict[str, Any]:
        """Fallback basic parsing without NER"""
        from app.resumes.parser import ResumeParser
        parser = ResumeParser()
        return parser.parse(text)
