"""
Resume parsing service
"""
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, date
import pdfplumber
from docx import Document
import structlog

logger = structlog.get_logger()


class ResumeParser:
    """Parse resumes from PDF and DOCX files"""
    
    def __init__(self):
        self.skill_patterns = self._load_skill_patterns()
        self.experience_patterns = self._load_experience_patterns()
    
    def _load_skill_patterns(self) -> List[str]:
        """Load common skill keywords"""
        return [
            "python", "java", "javascript", "typescript", "react", "node.js",
            "sql", "postgresql", "mongodb", "aws", "docker", "kubernetes",
            "machine learning", "deep learning", "ai", "data science",
            "agile", "scrum", "git", "ci/cd", "microservices",
        ]
    
    def _load_experience_patterns(self) -> List[re.Pattern]:
        """Load regex patterns for experience extraction"""
        return [
            re.compile(r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience', re.IGNORECASE),
            re.compile(r'experience[:\s]+(\d+)\+?\s*(?:years?|yrs?)', re.IGNORECASE),
        ]
    
    def extract_text(self, file_path: str) -> str:
        """Extract raw text from resume file"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        try:
            if extension == ".pdf":
                return self._extract_from_pdf(file_path)
            elif extension in [".docx", ".doc"]:
                return self._extract_from_docx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {extension}")
        except Exception as e:
            logger.error("text_extraction_failed", file_path=file_path, error=str(e))
            raise
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n".join(text_parts)
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = Document(file_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            text_parts.append(paragraph.text)
        return "\n".join(text_parts)
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse resume text into structured data"""
        parsed = {
            "skills": self._extract_skills(text),
            "experience": self._extract_experience(text),
            "education": self._extract_education(text),
            "projects": self._extract_projects(text),
            "certifications": self._extract_certifications(text),
            "languages": self._extract_languages(text),
            "experience_years": self._extract_experience_years(text),
        }
        return parsed
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.skill_patterns:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Also look for skills section
        skills_section = re.search(
            r'(?:skills?|technical\s+skills?|technologies?)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if skills_section:
            skills_text = skills_section.group(1)
            # Extract comma or newline separated skills
            skills = re.split(r'[,;\n]', skills_text)
            for skill in skills:
                skill = skill.strip()
                if skill and len(skill) > 2:
                    found_skills.append(skill)
        
        # Remove duplicates and return
        return list(set(found_skills))
    
    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience"""
        experiences = []
        
        # Look for experience section
        experience_section = re.search(
            r'(?:experience|work\s+experience|employment|professional\s+experience)[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if experience_section:
            exp_text = experience_section.group(1)
            # Try to extract individual experiences
            exp_entries = re.split(r'\n\n+', exp_text)
            
            for entry in exp_entries[:10]:  # Limit to 10 entries
                exp_dict = self._parse_experience_entry(entry)
                if exp_dict:
                    experiences.append(exp_dict)
        
        return experiences
    
    def _parse_experience_entry(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single experience entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if len(lines) < 2:
            return None
        
        # First line usually contains title and company
        title_company = lines[0]
        title_match = re.match(r'^(.+?)(?:\s+at\s+|\s+-\s+|\s+@\s+)(.+)$', title_company, re.IGNORECASE)
        
        if title_match:
            title = title_match.group(1).strip()
            company = title_match.group(2).strip()
        else:
            title = title_company
            company = ""
        
        # Look for date range
        date_range = None
        date_match = re.search(r'(\d{4}|\w+\s+\d{4})\s*[-–—]\s*(\d{4}|\w+\s+\d{4}|present|current)', entry, re.IGNORECASE)
        if date_match:
            date_range = f"{date_match.group(1)} - {date_match.group(2)}"
        
        # Rest is description
        description = '\n'.join(lines[1:])
        
        return {
            "title": title,
            "company": company,
            "date_range": date_range,
            "description": description,
        }
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education information"""
        education = []
        
        education_section = re.search(
            r'(?:education|academic|qualifications?)[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if education_section:
            edu_text = education_section.group(1)
            edu_entries = re.split(r'\n\n+', edu_text)
            
            for entry in edu_entries[:5]:  # Limit to 5 entries
                edu_dict = self._parse_education_entry(entry)
                if edu_dict:
                    education.append(edu_dict)
        
        return education
    
    def _parse_education_entry(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single education entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None
        
        degree = lines[0]
        institution = lines[1] if len(lines) > 1 else ""
        year = None
        
        year_match = re.search(r'\d{4}', entry)
        if year_match:
            year = year_match.group(0)
        
        return {
            "degree": degree,
            "institution": institution,
            "year": year,
        }
    
    def _extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """Extract projects"""
        projects = []
        
        projects_section = re.search(
            r'(?:projects?|portfolio)[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if projects_section:
            proj_text = projects_section.group(1)
            proj_entries = re.split(r'\n\n+', proj_text)
            
            for entry in proj_entries[:10]:  # Limit to 10 projects
                proj_dict = self._parse_project_entry(entry)
                if proj_dict:
                    projects.append(proj_dict)
        
        return projects
    
    def _parse_project_entry(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single project entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None
        
        name = lines[0]
        description = '\n'.join(lines[1:]) if len(lines) > 1 else ""
        
        return {
            "name": name,
            "description": description,
        }
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certifications = []
        
        cert_section = re.search(
            r'(?:certifications?|certificates?)[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if cert_section:
            cert_text = cert_section.group(1)
            certs = re.split(r'[,;\n]', cert_text)
            for cert in certs:
                cert = cert.strip()
                if cert:
                    certifications.append(cert)
        
        return certifications
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract languages"""
        languages = []
        
        lang_section = re.search(
            r'(?:languages?)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if lang_section:
            lang_text = lang_section.group(1)
            langs = re.split(r'[,;\n]', lang_text)
            for lang in langs:
                lang = lang.strip()
                if lang:
                    languages.append(lang)
        
        return languages
    
    def _extract_experience_years(self, text: str) -> Optional[int]:
        """
        Extract total years of experience
        First tries explicit mentions, then calculates from experience entries
        """
        # Try explicit mentions first
        for pattern in self.experience_patterns:
            match = pattern.search(text)
            if match:
                try:
                    years = int(match.group(1))
                    return years
                except ValueError:
                    continue
        
        # If no explicit mention, calculate from experience entries
        experiences = self._extract_experience(text)
        if experiences:
            return self._calculate_years_from_experiences(experiences)
        
        return None
    
    def _calculate_years_from_experiences(self, experiences: List[Dict[str, Any]]) -> Optional[int]:
        """Calculate total years from experience date ranges"""
        
        total_days = 0
        date_ranges = []
        
        for exp in experiences:
            date_range = exp.get("date_range", "")
            if not date_range:
                continue
            
            # Parse date range (e.g., "2020-01 - 2022-12" or "Jan 2020 - Present")
            date_match = re.search(
                r'(\d{4}|\w+\s+\d{4})\s*[-–—]\s*(\d{4}|\w+\s+\d{4}|present|current)',
                date_range,
                re.IGNORECASE
            )
            
            if date_match:
                start_str = date_match.group(1).strip()
                end_str = date_match.group(2).strip().lower()
                
                # Parse start date
                start_date = self._parse_date_string(start_str)
                if not start_date:
                    continue
                
                # Parse end date
                if end_str in ["present", "current", "now"]:
                    end_date = date.today()
                else:
                    end_date = self._parse_date_string(end_str)
                    if not end_date:
                        continue
                
                if start_date and end_date and end_date >= start_date:
                    delta = end_date - start_date
                    date_ranges.append((start_date, end_date, delta.days))
        
        if not date_ranges:
            return None
        
        # Sort and merge overlapping periods
        date_ranges.sort(key=lambda x: x[0])
        merged = []
        
        for start, end, days in date_ranges:
            if not merged:
                merged.append((start, end, days))
            else:
                last_start, last_end, last_days = merged[-1]
                if start <= last_end:
                    new_end = max(end, last_end)
                    new_days = (new_end - last_start).days
                    merged[-1] = (last_start, new_end, new_days)
                else:
                    merged.append((start, end, days))
        
        total_days = sum(days for _, _, days in merged)
        years = total_days / 365.25
        return int(round(years))
    
    def _parse_date_string(self, date_str: str) -> Optional[date]:
        """Parse date string to date object"""
        
        formats = [
            "%Y-%m", "%Y-%m-%d", "%Y",
            "%B %Y", "%b %Y", "%m/%Y",
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

