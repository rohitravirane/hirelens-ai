"""
Smart Section Detector - Content-based section identification without headers
This is the intelligence that makes the system world-class - detecting sections
based on content patterns, not just headers
"""
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class SmartSectionDetector:
    """
    Intelligently detects resume sections without relying on headers
    Uses content patterns, layout clues, and semantic understanding
    """
    
    # Date patterns for experience/education
    DATE_PATTERN = r'\b(19|20)\d{2}\s*[-–—]\s*(?:19|20)?\d{2}|PRESENT|CURRENT|NOW\b'
    
    # Experience indicators
    EXPERIENCE_PATTERNS = {
        'job_titles': [
            r'\b(?:Senior|Junior|Lead|Principal|Staff|Associate|Entry\s+Level)\s+[A-Z][a-z]+\s+(?:Developer|Engineer|Manager|Analyst|Architect|Consultant|Specialist|Designer|Scientist|Coordinator|Director|Executive|Officer)\b',
            r'\b(?:Software|Full\s+Stack|Frontend|Backend|DevOps|Data|ML|AI|Cloud|Systems|Product|Project|Business|Technical|QA|Test)\s+[A-Z][a-z]+\b',
        ],
        'company_indicators': [
            r'\b(?:Pvt|Ltd|LLC|Inc|Corp|Corporation|Technologies|Solutions|Services|Systems|Group|Company|Co)\b',
            r'\b[A-Z][a-z]+\s+(?:Software|Tech|Technologies|Solutions|Systems|Group|Consulting)\b',
        ],
        'work_keywords': ['led', 'developed', 'designed', 'implemented', 'managed', 'created', 'built', 'delivered', 'improved', 'optimized', 'collaborated', 'worked', 'responsibilities', 'achievements'],
    }
    
    # Education indicators
    EDUCATION_PATTERNS = {
        'degree_keywords': ['bachelor', 'master', 'phd', 'ph.d', 'doctorate', 'mba', 'mca', 'bsc', 'msc', 'btech', 'mtech', 'degree', 'diploma', 'certificate'],
        'institution_keywords': ['university', 'college', 'institute', 'school', 'academy'],
        'education_keywords': ['graduated', 'graduation', 'coursework', 'gpa', 'cgpa', 'academic', 'studied', 'major', 'minor'],
    }
    
    # Skills indicators
    SKILLS_PATTERNS = {
        'technology_list': r'(?:Frontend|Backend|Database|DevOps|Tools|Technologies|Languages|Frameworks|Platforms|Software)[:\s]+',
        'tech_keywords': ['react', 'angular', 'vue', 'python', 'java', 'javascript', 'node', 'django', 'flask', 'sql', 'mongodb', 'postgresql', 'docker', 'kubernetes', 'aws', 'azure'],
        'separators': [',', ';', '|', '/'],
    }
    
    # Project indicators
    PROJECT_PATTERNS = {
        'project_keywords': ['project', 'portfolio', 'github', 'gitlab', 'demo', 'application', 'website', 'app', 'system'],
        'url_pattern': r'https?://[^\s]+',
        'github_pattern': r'github\.com/[\w-]+/[\w-]+',
    }
    
    def detect_sections(self, text: str) -> Dict[str, Tuple[int, int]]:
        """
        Detect section boundaries in resume text without headers
        
        Returns:
            Dict mapping section names to (start_index, end_index) tuples
        """
        lines = text.split('\n')
        sections = {}
        
        # Find potential section boundaries based on content patterns
        experience_start, experience_end = self._detect_experience_section(lines)
        education_start, education_end = self._detect_education_section(lines)
        skills_start, skills_end = self._detect_skills_section(lines)
        projects_start, projects_end = self._detect_projects_section(lines)
        
        if experience_start >= 0:
            sections['experience'] = (experience_start, experience_end)
        if education_start >= 0:
            sections['education'] = (education_start, education_end)
        if skills_start >= 0:
            sections['skills'] = (skills_start, skills_end)
        if projects_start >= 0:
            sections['projects'] = (projects_start, projects_end)
        
        logger.info("section_detection_complete",
                   experience_detected=experience_start >= 0,
                   education_detected=education_start >= 0,
                   skills_detected=skills_start >= 0,
                   projects_detected=projects_start >= 0)
        
        return sections
    
    def _detect_experience_section(self, lines: List[str]) -> Tuple[int, int]:
        """Detect work experience section using content patterns"""
        start_idx = -1
        end_idx = -1
        
        date_count = 0
        job_title_count = 0
        company_count = 0
        
        for i, line in enumerate(lines):
            line_upper = line.upper()
            line_lower = line.lower()
            
            # Check for date patterns (common in experience)
            if re.search(self.DATE_PATTERN, line_upper):
                date_count += 1
                if start_idx < 0:  # First date found
                    start_idx = i
            
            # Check for job title patterns
            for pattern in self.EXPERIENCE_PATTERNS['job_titles']:
                if re.search(pattern, line, re.IGNORECASE):
                    job_title_count += 1
                    if start_idx < 0:
                        start_idx = i
                    break
            
            # Check for company indicators
            for pattern in self.EXPERIENCE_PATTERNS['company_indicators']:
                if re.search(pattern, line, re.IGNORECASE):
                    company_count += 1
                    if start_idx < 0:
                        start_idx = i
                    break
            
            # Check for work keywords
            if any(keyword in line_lower for keyword in self.EXPERIENCE_PATTERNS['work_keywords']):
                if start_idx < 0:
                    start_idx = i
        
        # Experience section detected if we have multiple indicators
        if start_idx >= 0 and (date_count >= 2 or (job_title_count >= 1 and company_count >= 1)):
            # Find end - look for next major section or end of dense content
            end_idx = self._find_section_end(lines, start_idx, 'experience')
            return start_idx, end_idx
        
        return -1, -1
    
    def _detect_education_section(self, lines: List[str]) -> Tuple[int, int]:
        """Detect education section using content patterns"""
        start_idx = -1
        end_idx = -1
        
        degree_count = 0
        institution_count = 0
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            line_upper = line.upper()
            
            # Check for degree keywords
            if any(keyword in line_lower for keyword in self.EDUCATION_PATTERNS['degree_keywords']):
                degree_count += 1
                if start_idx < 0:
                    start_idx = i
            
            # Check for institution keywords
            if any(keyword in line_lower for keyword in self.EDUCATION_PATTERNS['institution_keywords']):
                institution_count += 1
                if start_idx < 0:
                    start_idx = i
            
            # Check for dates (education also has dates)
            if re.search(self.DATE_PATTERN, line_upper) and start_idx >= 0:
                # Continue in education section
                pass
        
        # Education detected if we have degree or institution keywords
        if start_idx >= 0 and (degree_count >= 1 or institution_count >= 1):
            end_idx = self._find_section_end(lines, start_idx, 'education')
            return start_idx, end_idx
        
        return -1, -1
    
    def _detect_skills_section(self, lines: List[str]) -> Tuple[int, int]:
        """Detect skills section using content patterns"""
        start_idx = -1
        
        for i, line in enumerate(lines):
            # Check for category patterns (Frontend:, Backend:, etc.)
            if re.search(self.SKILLS_PATTERNS['technology_list'], line, re.IGNORECASE):
                start_idx = i
                break
            
            # Check for technology density (many tech keywords in a line)
            line_lower = line.lower()
            tech_count = sum(1 for tech in self.SKILLS_PATTERNS['tech_keywords'] if tech in line_lower)
            if tech_count >= 3:  # Multiple technologies in one line
                start_idx = i
                break
        
        if start_idx >= 0:
            end_idx = self._find_section_end(lines, start_idx, 'skills')
            return start_idx, end_idx
        
        return -1, -1
    
    def _detect_projects_section(self, lines: List[str]) -> Tuple[int, int]:
        """Detect projects section using content patterns"""
        start_idx = -1
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check for project keywords
            if any(keyword in line_lower for keyword in self.PROJECT_PATTERNS['project_keywords']):
                # Also check for URLs (projects often have links)
                if re.search(self.PROJECT_PATTERNS['url_pattern'], line) or re.search(self.PROJECT_PATTERNS['github_pattern'], line_lower):
                    start_idx = i
                    break
        
        if start_idx >= 0:
            end_idx = self._find_section_end(lines, start_idx, 'projects')
            return start_idx, end_idx
        
        return -1, -1
    
    def _find_section_end(self, lines: List[str], start_idx: int, section_type: str) -> int:
        """Find where a section ends based on content density and next section indicators"""
        # Look ahead for next section indicators or content drop-off
        max_lookahead = min(50, len(lines) - start_idx)  # Look ahead max 50 lines
        
        for i in range(start_idx + 1, start_idx + max_lookahead):
            line = lines[i].strip()
            
            # Empty line followed by another empty line suggests section end
            if not line and i + 1 < len(lines) and not lines[i + 1].strip():
                return i
            
            # Check for next section headers (if any)
            line_upper = line.upper()
            if section_type == 'experience':
                # Education, Projects, Skills could come after experience
                if any(header in line_upper for header in ['EDUCATION', 'PROJECTS', 'SKILLS', 'CERTIFICATIONS']):
                    return i - 1
            elif section_type == 'education':
                # Projects, Skills, Contact could come after education
                if any(header in line_upper for header in ['PROJECTS', 'SKILLS', 'CERTIFICATIONS', 'CONTACT', 'PROFILE']):
                    return i - 1
            elif section_type == 'skills':
                # Contact, Profile, Projects could come after skills
                if any(header in line_upper for header in ['CONTACT', 'PROFILE', 'PROJECTS', 'REFERENCES']):
                    return i - 1
        
        # If no clear end found, use reasonable default
        return min(start_idx + max_lookahead, len(lines) - 1)



