"""
Elite-Level Resume Layout Analyzer
==================================
World-class layout understanding that handles:
- Single column layouts
- Two-column layouts  
- Multi-column layouts
- Missing sections
- Complex structures
- Various resume formats
"""

import re
import structlog
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import numpy as np
# Removed KMeans import - using simple threshold-based detection instead

logger = structlog.get_logger()


class EliteLayoutAnalyzer:
    """
    Elite-level layout analyzer that understands resume structure intelligently
    """
    
    def __init__(self):
        self.section_keywords = {
            'experience': ['work experience', 'employment', 'professional experience', 'career', 'employment history'],
            'education': ['education', 'academic', 'qualifications', 'degrees'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'technologies'],
            'projects': ['projects', 'portfolio', 'key projects'],
            'certifications': ['certifications', 'certificates', 'credentials', 'licenses'],
            'languages': ['languages', 'language proficiency'],
            'summary': ['summary', 'profile', 'objective', 'about', 'overview'],
            'contact': ['contact', 'personal information', 'details']
        }
        
    def analyze_comprehensive_layout(
        self, 
        text: str, 
        pdf_path: Optional[str] = None,
        huridocs_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive layout analysis - understands any resume structure
        
        Returns:
            {
                'layout_type': 'single_column' | 'two_column' | 'multi_column',
                'columns': {
                    'left': {...},
                    'right': {...}
                },
                'sections': {
                    'experience': {'column': 'left', 'start_line': 10, 'end_line': 50},
                    'skills': {'column': 'right', 'start_line': 5, 'end_line': 15}
                },
                'section_positions': {...},
                'confidence': 0.95
            }
        """
        try:
            # Limit text size to prevent performance issues
            max_text_length = 50000  # Limit to 50KB
            if len(text) > max_text_length:
                logger.warning("text_too_large_truncating", original_length=len(text), truncated_length=max_text_length)
                text = text[:max_text_length]
            
            # Step 1: Get spatial layout data (HURIDOCS or text-based)
            logger.info("elite_layout_step1_spatial_data")
            spatial_data = self._get_spatial_layout(text, pdf_path, huridocs_data)
            logger.info("elite_layout_step1_complete", has_spatial=spatial_data.get('has_spatial'), segments_count=len(spatial_data.get('segments', [])))
            
            # Step 2: Detect column structure
            logger.info("elite_layout_step2_column_detection")
            column_structure = self._detect_column_structure(text, spatial_data)
            logger.info("elite_layout_step2_complete", layout_type=column_structure.get('type'))
            
            # Step 3: Identify sections intelligently
            logger.info("elite_layout_step3_section_identification")
            sections = self._identify_sections_intelligently(text, column_structure, spatial_data)
            logger.info("elite_layout_step3_complete", count=len(sections))
            
            # Step 4: Map sections to columns
            section_mapping = self._map_sections_to_columns(sections, column_structure)
            
            # Step 5: Calculate confidence
            confidence = self._calculate_confidence(column_structure, sections, section_mapping)
            
            layout_info = {
                'layout_type': column_structure.get('type', 'single_column'),
                'columns': column_structure.get('columns', {}),
                'sections': sections,
                'section_mapping': section_mapping,
                'spatial_data': spatial_data,
                'confidence': confidence,
                'raw_text': text
            }
            
            logger.info("elite_layout_analysis_complete",
                       layout_type=layout_info['layout_type'],
                       sections_found=len(sections),
                       confidence=confidence)
            
            return layout_info
            
        except Exception as e:
            logger.error("elite_layout_analysis_error", error=str(e), exc_info=True)
            # Fallback to basic single-column layout
            return {
                'layout_type': 'single_column',
                'columns': {'full': {'text': text, 'start': 0, 'end': len(text)}},
                'sections': self._identify_sections_basic(text),
                'section_mapping': {},
                'confidence': 0.5,
                'raw_text': text
            }
    
    def _get_spatial_layout(
        self, 
        text: str, 
        pdf_path: Optional[str] = None,
        huridocs_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get spatial layout data from HURIDOCS or text analysis"""
        spatial_data = {
            'has_spatial': False,
            'segments': [],
            'page_width': 0,
            'page_height': 0
        }
        
        # Try HURIDOCS first (best spatial data)
        if huridocs_data:
            try:
                pages = huridocs_data.get('pages', [])
                if pages:
                    spatial_data['has_spatial'] = True
                    spatial_data['segments'] = pages
                    # Calculate page dimensions
                    if pages:
                        max_right = max(s.get('left', 0) + s.get('width', 0) for s in pages if isinstance(s, dict))
                        max_bottom = max(s.get('top', 0) + s.get('height', 0) for s in pages if isinstance(s, dict))
                        spatial_data['page_width'] = max_right
                        spatial_data['page_height'] = max_bottom
                    logger.info("using_huridocs_spatial_data", segments=len(pages))
            except Exception as e:
                logger.warning("huridocs_spatial_parse_error", error=str(e))
        
        # Fallback: Text-based spatial analysis
        if not spatial_data['has_spatial']:
            spatial_data = self._analyze_text_spatial_structure(text)
        
        return spatial_data
    
    def _analyze_text_spatial_structure(self, text: str) -> Dict[str, Any]:
        """Analyze text to infer spatial structure"""
        lines = text.split('\n')
        spatial_data = {
            'has_spatial': False,
            'segments': [],
            'line_positions': []
        }
        
        # Analyze line structure for column hints
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detect potential column separators (large gaps, vertical lines mentioned)
            # This is a heuristic approach
            segment = {
                'text': line,
                'line_index': i,
                'length': len(line),
                'has_section_header': self._is_section_header(line),
                'indentation_hint': len(line) - len(line.lstrip()) if line else 0
            }
            spatial_data['segments'].append(segment)
        
        return spatial_data
    
    def _detect_column_structure(
        self, 
        text: str, 
        spatial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Intelligently detect column structure"""
        logger.info("_detect_column_structure_start", has_spatial=spatial_data.get('has_spatial'))
        column_structure = {
            'type': 'single_column',
            'columns': {},
            'separator_x': None,
            'confidence': 0.0
        }
        
        # Method 1: Use HURIDOCS spatial data (most accurate)
        if spatial_data.get('has_spatial') and spatial_data.get('segments'):
            logger.info("trying_spatial_column_detection", segments_count=len(spatial_data.get('segments', [])))
            try:
                column_structure = self._detect_columns_from_spatial(spatial_data)
                logger.info("spatial_detection_complete", type=column_structure['type'])
                if column_structure['type'] != 'single_column':
                    logger.info("columns_detected_from_spatial", 
                               type=column_structure['type'],
                               confidence=column_structure['confidence'])
                    return column_structure
            except Exception as e:
                logger.error("spatial_column_detection_error", error=str(e), exc_info=True)
                column_structure = {'type': 'single_column', 'columns': {}, 'confidence': 0.0}
        
        # Method 2: Text-based column detection
        logger.info("trying_text_based_column_detection")
        try:
            column_structure = self._detect_columns_from_text(text, spatial_data)
            logger.info("text_detection_complete", type=column_structure['type'])
        except Exception as e:
            logger.error("text_column_detection_error", error=str(e), exc_info=True)
            column_structure = {'type': 'single_column', 'columns': {}, 'confidence': 0.0}
        
        return column_structure
    
    def _detect_columns_from_spatial(self, spatial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect columns using spatial position data"""
        logger.info("_detect_columns_from_spatial_start")
        try:
            segments = spatial_data.get('segments', [])
            if not segments:
                logger.info("no_segments_found")
                return {'type': 'single_column', 'columns': {}, 'confidence': 0.0}
            
            # Limit segments to prevent performance issues
            max_segments = 100
            if len(segments) > max_segments:
                logger.warning("too_many_segments_truncating", original_count=len(segments), truncated_count=max_segments)
                segments = segments[:max_segments]
            
            logger.info("extracting_left_positions", segments_count=len(segments))
            # Extract left positions
            left_positions = []
            for seg in segments:
                if isinstance(seg, dict) and 'left' in seg:
                    left = seg.get('left', 0)
                    if left > 0:
                        left_positions.append(left)
            
            logger.info("left_positions_extracted", count=len(left_positions))
            if not left_positions or len(left_positions) < 5:
                logger.info("insufficient_left_positions")
                return {'type': 'single_column', 'columns': {}, 'confidence': 0.0}
            
            page_width = spatial_data.get('page_width', 0)
            if not page_width:
                # Estimate from max left + average width
                max_left = max(left_positions)
                avg_width = 400  # Estimate
                page_width = max_left + avg_width
            
            logger.info("detecting_columns_simple_method", left_positions_count=len(left_positions))
            # Simple threshold-based column detection (faster than KMeans)
            # Find natural gap in left positions
            sorted_positions = sorted(left_positions)
            
            if len(sorted_positions) >= 10:
                # Find the largest gap between consecutive positions
                max_gap = 0
                gap_index = -1
                
                for i in range(len(sorted_positions) - 1):
                    gap = sorted_positions[i + 1] - sorted_positions[i]
                    if gap > max_gap:
                        max_gap = gap
                        gap_index = i
                
                # If gap is significant, it's likely a column separator
                if max_gap > 50 and max_gap > (page_width * 0.05):
                    separator_x = (sorted_positions[gap_index] + sorted_positions[gap_index + 1]) / 2
                    left_cluster_max = sorted_positions[gap_index]
                    right_cluster_min = sorted_positions[gap_index + 1]
                    
                    logger.info("column_separator_found", separator_x=separator_x, gap=max_gap)
                    
                    # Split segments into columns
                    left_segments = [s for s in segments 
                                   if isinstance(s, dict) and s.get('left', 0) < separator_x]
                    right_segments = [s for s in segments 
                                    if isinstance(s, dict) and s.get('left', 0) >= separator_x]
                    
                    # Reconstruct text for each column
                    left_text = self._reconstruct_text_from_segments(left_segments, 'top')
                    right_text = self._reconstruct_text_from_segments(right_segments, 'top')
                    
                    # Only consider it two-column if both have substantial content
                    if len(left_text) > 100 and len(right_text) > 100:
                        confidence = min(0.95, max_gap / page_width * 2)  # Higher gap = higher confidence
                        
                        logger.info("two_column_detected", left_length=len(left_text), right_length=len(right_text), confidence=confidence)
                        
                        return {
                            'type': 'two_column',
                            'columns': {
                                'left': {
                                    'text': left_text,
                                    'segments': left_segments,
                                    'start': 0,
                                    'end': len(left_text)
                                },
                                'right': {
                                    'text': right_text,
                                    'segments': right_segments,
                                    'start': 0,
                                    'end': len(right_text)
                                }
                            },
                            'separator_x': separator_x,
                            'confidence': confidence
                        }
        except Exception as e:
            logger.error("_detect_columns_from_spatial_error", error=str(e), exc_info=True)
            return {'type': 'single_column', 'columns': {}, 'confidence': 0.0}
        
        return {'type': 'single_column', 'columns': {}, 'confidence': 0.5}
    
    def _reconstruct_text_from_segments(self, segments: List[Dict], sort_key: str = 'top') -> str:
        """Reconstruct text from segments, sorted by position"""
        if not segments:
            return ""
        
        # Sort segments by position
        sorted_segments = sorted(
            segments,
            key=lambda s: (s.get('page_number', 0), s.get(sort_key, 0))
        )
        
        # Extract text
        texts = []
        for seg in sorted_segments:
            if isinstance(seg, dict):
                text = seg.get('text', '').strip()
                if text:
                    texts.append(text)
        
        return '\n'.join(texts)
    
    def _detect_columns_from_text(self, text: str, spatial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect columns from text structure (heuristic approach)"""
        lines = text.split('\n')
        
        # Look for patterns that suggest two columns:
        # 1. Lines with very different lengths alternating
        # 2. Section headers appearing on same line (e.g., "WORK EXPERIENCE EDUCATION")
        # 3. Large gaps in text (many spaces)
        
        # Check for section headers on same line (strong indicator of two columns)
        for line in lines[:20]:  # Check first 20 lines
            line_upper = line.upper()
            if ('EXPERIENCE' in line_upper and 'EDUCATION' in line_upper) or \
               ('WORK' in line_upper and 'EDUCATION' in line_upper) or \
               ('EXPERIENCE' in line_upper and 'SKILLS' in line_upper):
                logger.info("two_column_indicator_found", line=line[:50])
                # Try to split by large gap or separator
                return self._split_text_into_columns(text, line)
        
        return {'type': 'single_column', 'columns': {'full': {'text': text}}, 'confidence': 0.5}
    
    def _split_text_into_columns(self, text: str, header_line: str) -> Dict[str, Any]:
        """Split text into columns based on detected separator"""
        lines = text.split('\n')
        
        # Find the separator position (usually middle of page)
        # Look for lines with large gaps
        separator_pos = None
        for i, line in enumerate(lines):
            # Check for large gaps (multiple spaces)
            if len(line) > 50:
                # Find middle gap
                mid = len(line) // 2
                left_part = line[:mid].rstrip()
                right_part = line[mid:].lstrip()
                
                # If both parts have content and gap is significant
                if len(left_part) > 10 and len(right_part) > 10 and \
                   len(line) - len(left_part) - len(right_part) > 20:
                    separator_pos = mid
                    break
        
        if separator_pos:
            # Split lines
            left_lines = []
            right_lines = []
            
            for line in lines:
                if len(line) > separator_pos:
                    left_lines.append(line[:separator_pos].rstrip())
                    right_lines.append(line[separator_pos:].lstrip())
                else:
                    # Short line - decide based on position
                    if len(line) < separator_pos * 0.6:
                        left_lines.append(line)
                    else:
                        right_lines.append(line)
            
            left_text = '\n'.join([l for l in left_lines if l.strip()])
            right_text = '\n'.join([l for l in right_lines if l.strip()])
            
            if len(left_text) > 100 and len(right_text) > 100:
                return {
                    'type': 'two_column',
                    'columns': {
                        'left': {'text': left_text, 'start': 0, 'end': len(left_text)},
                        'right': {'text': right_text, 'start': 0, 'end': len(right_text)}
                    },
                    'separator_x': separator_pos,
                    'confidence': 0.7
                }
        
        return {'type': 'single_column', 'columns': {'full': {'text': text}}, 'confidence': 0.5}
    
    def _identify_sections_intelligently(
        self, 
        text: str, 
        column_structure: Dict[str, Any],
        spatial_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Intelligently identify all sections in the resume"""
        sections = {}
        
        # Get text from each column
        columns = column_structure.get('columns', {})
        
        if column_structure['type'] == 'two_column':
            # Search in both columns
            for col_name, col_data in columns.items():
                col_text = col_data.get('text', '')
                col_sections = self._find_sections_in_text(col_text, col_name)
                sections.update(col_sections)
        else:
            # Single column - search in full text
            full_text = columns.get('full', {}).get('text', text)
            sections = self._find_sections_in_text(full_text, 'full')
        
        logger.info("sections_identified", 
                   count=len(sections),
                   sections=list(sections.keys()))
        
        return sections
    
    def _find_sections_in_text(self, text: str, column_name: str) -> Dict[str, Dict[str, Any]]:
        """Find sections in text using multiple strategies"""
        sections = {}
        lines = text.split('\n')
        
        # Limit lines to prevent performance issues
        max_lines = 1000
        if len(lines) > max_lines:
            logger.warning("too_many_lines_truncating", original_lines=len(lines), truncated_lines=max_lines)
            lines = lines[:max_lines]
        
        # Strategy 1: Look for explicit section headers
        for i, line in enumerate(lines):
            line_upper = line.strip().upper()
            
            # Check against all section keywords
            for section_type, keywords in self.section_keywords.items():
                # Skip if already found
                if section_type in sections:
                    continue
                    
                for keyword in keywords:
                    if keyword.upper() in line_upper:
                        # Found section header
                        # Find section boundaries
                        start_line = i
                        end_line = self._find_section_end(lines, i, section_type)
                        
                        section_text = '\n'.join(lines[start_line:end_line])
                        
                        sections[section_type] = {
                            'column': column_name,
                            'start_line': start_line,
                            'end_line': end_line,
                            'text': section_text,
                            'header_line': line,
                            'confidence': 0.9
                        }
                        break
        
        # Strategy 2: Content-based detection (for missing headers)
        sections.update(self._detect_sections_by_content(text, column_name, sections))
        
        return sections
    
    def _find_section_end(self, lines: List[str], start_line: int, section_type: str) -> int:
        """Find where a section ends"""
        # Look for next section header
        next_section_keywords = []
        for st, keywords in self.section_keywords.items():
            if st != section_type:
                next_section_keywords.extend(keywords)
        
        for i in range(start_line + 1, len(lines)):
            line_upper = lines[i].strip().upper()
            # Check if this is a new section
            for keyword in next_section_keywords:
                if keyword.upper() in line_upper:
                    return i
        
        # If no next section found, section goes to end
        return len(lines)
    
    def _detect_sections_by_content(
        self, 
        text: str, 
        column_name: str,
        existing_sections: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Detect sections by analyzing content patterns"""
        detected = {}
        lines = text.split('\n')
        
        # Experience: Look for date patterns + company names
        if 'experience' not in existing_sections:
            exp_start, exp_end = self._find_experience_by_content(lines)
            if exp_start is not None:
                detected['experience'] = {
                    'column': column_name,
                    'start_line': exp_start,
                    'end_line': exp_end,
                    'text': '\n'.join(lines[exp_start:exp_end]),
                    'header_line': '',
                    'confidence': 0.7
                }
        
        # Skills: Look for technology keywords
        if 'skills' not in existing_sections:
            skills_start, skills_end = self._find_skills_by_content(lines)
            if skills_start is not None:
                detected['skills'] = {
                    'column': column_name,
                    'start_line': skills_start,
                    'end_line': skills_end,
                    'text': '\n'.join(lines[skills_start:skills_end]),
                    'header_line': '',
                    'confidence': 0.7
                }
        
        # Education: Look for degree patterns
        if 'education' not in existing_sections:
            edu_start, edu_end = self._find_education_by_content(lines)
            if edu_start is not None:
                detected['education'] = {
                    'column': column_name,
                    'start_line': edu_start,
                    'end_line': edu_end,
                    'text': '\n'.join(lines[edu_start:edu_end]),
                    'header_line': '',
                    'confidence': 0.7
                }
        
        return detected
    
    def _find_experience_by_content(self, lines: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """Find experience section by content patterns"""
        date_pattern = re.compile(r'\b(19|20)\d{2}\b|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s-]\d{4}|(current|present|now)')
        company_keywords = ['technologies', 'inc', 'ltd', 'corp', 'systems', 'solutions', 'consulting', 'group']
        
        start = None
        consecutive_matches = 0
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            has_date = bool(date_pattern.search(line))
            has_company = any(keyword in line_lower for keyword in company_keywords)
            has_job_title = any(word in line_lower for word in ['developer', 'engineer', 'manager', 'analyst', 'specialist', 'architect'])
            
            if has_date and (has_company or has_job_title):
                if start is None:
                    start = i
                consecutive_matches += 1
            elif start is not None:
                if consecutive_matches >= 1:  # Found at least one experience entry
                    return start, i
                start = None
                consecutive_matches = 0
        
        if start is not None and consecutive_matches >= 1:
            return start, len(lines)
        
        return None, None
    
    def _find_skills_by_content(self, lines: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """Find skills section by technology keywords"""
        tech_keywords = ['javascript', 'python', 'java', 'react', 'angular', 'node', 'html', 'css', '.net', 'spring', 'django', 'flask']
        
        start = None
        tech_count = 0
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            tech_found = sum(1 for keyword in tech_keywords if keyword in line_lower)
            
            if tech_found >= 2:  # At least 2 technologies in line
                if start is None:
                    start = i
                tech_count += tech_found
            elif start is not None:
                if tech_count >= 3:  # Found enough technologies
                    return start, i
                start = None
                tech_count = 0
        
        if start is not None and tech_count >= 3:
            return start, len(lines)
        
        return None, None
    
    def _find_education_by_content(self, lines: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """Find education section by degree patterns"""
        degree_patterns = [r'\b(B\.S\.|B\.A\.|M\.S\.|M\.A\.|Ph\.D\.|Bachelor|Master|Doctorate)', 
                          r'\b(University|College|Institute|School)']
        
        start = None
        
        for i, line in enumerate(lines):
            line_upper = line.upper()
            has_degree = any(re.search(pattern, line_upper, re.IGNORECASE) for pattern in degree_patterns)
            
            if has_degree:
                if start is None:
                    start = i
            elif start is not None:
                # Education section ended
                return start, i
        
        if start is not None:
            return start, len(lines)
        
        return None, None
    
    def _map_sections_to_columns(
        self, 
        sections: Dict[str, Dict[str, Any]],
        column_structure: Dict[str, Any]
    ) -> Dict[str, str]:
        """Map sections to their columns"""
        mapping = {}
        
        for section_name, section_data in sections.items():
            column = section_data.get('column', 'full')
            mapping[section_name] = column
        
        return mapping
    
    def _calculate_confidence(
        self,
        column_structure: Dict[str, Any],
        sections: Dict[str, Dict[str, Any]],
        section_mapping: Dict[str, str]
    ) -> float:
        """Calculate confidence score for layout analysis"""
        confidence = 0.5  # Base confidence
        
        # Column detection confidence
        if column_structure.get('confidence'):
            confidence += column_structure['confidence'] * 0.3
        
        # Section detection confidence
        if sections:
            avg_section_confidence = sum(s.get('confidence', 0.5) for s in sections.values()) / len(sections)
            confidence += avg_section_confidence * 0.4
        
        # Section distribution (sections in different columns = good)
        if column_structure['type'] == 'two_column':
            columns_used = set(section_mapping.values())
            if len(columns_used) > 1:
                confidence += 0.1
        
        return min(0.95, confidence)
    
    def _identify_sections_basic(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Basic section identification fallback"""
        sections = {}
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_upper = line.strip().upper()
            for section_type, keywords in self.section_keywords.items():
                for keyword in keywords:
                    if keyword.upper() in line_upper:
                        sections[section_type] = {
                            'column': 'full',
                            'start_line': i,
                            'end_line': len(lines),
                            'text': text,
                            'confidence': 0.6
                        }
                        break
        
        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """Check if line looks like a section header"""
        line_upper = line.strip().upper()
        
        # Check against section keywords
        for keywords in self.section_keywords.values():
            for keyword in keywords:
                if keyword.upper() in line_upper:
                    return True
        
        return False
    
    def get_text_for_section(
        self,
        section_name: str,
        layout_info: Dict[str, Any]
    ) -> Optional[str]:
        """Get text for a specific section from layout info"""
        sections = layout_info.get('sections', {})
        
        if section_name in sections:
            return sections[section_name].get('text', '')
        
        # Try to find in columns
        section_mapping = layout_info.get('section_mapping', {})
        column_name = section_mapping.get(section_name)
        
        if column_name:
            columns = layout_info.get('columns', {})
            if column_name in columns:
                col_text = columns[column_name].get('text', '')
                # Try to extract section from column text
                section_data = sections.get(section_name, {})
                start = section_data.get('start_line', 0)
                end = section_data.get('end_line', len(col_text))
                lines = col_text.split('\n')
                return '\n'.join(lines[start:end])
        
        return None

