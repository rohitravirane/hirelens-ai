"""
Job description parser and intelligence extractor
"""
import re
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger()


class JobDescriptionParser:
    """Parse and extract intelligence from job descriptions"""
    
    def __init__(self):
        self.skill_keywords = self._load_skill_keywords()
        self.seniority_keywords = {
            "junior": ["junior", "entry", "entry-level", "associate", "intern"],
            "mid": ["mid", "mid-level", "intermediate", "experienced"],
            "senior": ["senior", "sr", "lead", "principal", "staff"],
            "executive": ["executive", "director", "vp", "vice president", "chief"],
        }
    
    def _load_skill_keywords(self) -> List[str]:
        """Load comprehensive skill keywords"""
        return [
            # Programming Languages
            "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#",
            "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
            
            # Web Technologies
            "react", "angular", "vue", "next.js", "node.js", "express", "django",
            "flask", "fastapi", "spring", "laravel", "rails",
            
            # Databases
            "sql", "postgresql", "mysql", "mongodb", "redis", "cassandra",
            "elasticsearch", "dynamodb", "oracle",
            
            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
            "jenkins", "gitlab", "github actions", "ci/cd",
            
            # Data & AI
            "machine learning", "deep learning", "ai", "data science", "nlp",
            "computer vision", "tensorflow", "pytorch", "pandas", "numpy",
            
            # Other
            "agile", "scrum", "microservices", "rest api", "graphql", "grpc",
        ]
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse job description text into structured data"""
        parsed = {
            "required_skills": self._extract_required_skills(text),
            "nice_to_have_skills": self._extract_nice_to_have_skills(text),
            "experience_years_required": self._extract_experience_years(text),
            "seniority_level": self._extract_seniority_level(text),
            "education_requirements": self._extract_education_requirements(text),
            "location": self._extract_location(text),
            "remote_allowed": self._extract_remote_allowed(text),
            "employment_type": self._extract_employment_type(text),
        }
        return parsed
    
    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills"""
        text_lower = text.lower()
        found_skills = []
        
        # Look for "required skills" or "must have" sections
        required_section = re.search(
            r'(?:required\s+skills?|must\s+have|requirements?|qualifications?)[:\s]+(.*?)(?:\n\n|\n(?:nice|preferred|bonus)|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if required_section:
            skills_text = required_section.group(1)
            found_skills.extend(self._extract_skills_from_text(skills_text))
        
        # Also check for skills mentioned with "must", "required", "essential"
        for skill in self.skill_keywords:
            pattern = rf'\b(?:must|required|essential|need).*?\b{re.escape(skill)}\b'
            if re.search(pattern, text_lower):
                if skill not in found_skills:
                    found_skills.append(skill)
        
        return list(set(found_skills))
    
    def _extract_nice_to_have_skills(self, text: str) -> List[str]:
        """Extract nice-to-have skills"""
        text_lower = text.lower()
        found_skills = []
        
        # Look for "nice to have", "preferred", "bonus" sections
        nice_section = re.search(
            r'(?:nice\s+to\s+have|preferred|bonus|plus|advantage)[:\s]+(.*?)(?:\n\n|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        
        if nice_section:
            skills_text = nice_section.group(1)
            found_skills.extend(self._extract_skills_from_text(skills_text))
        
        # Check for skills mentioned with "preferred", "nice", "bonus"
        for skill in self.skill_keywords:
            pattern = rf'\b(?:preferred|nice|bonus|plus|advantage).*?\b{re.escape(skill)}\b'
            if re.search(pattern, text_lower):
                if skill not in found_skills:
                    found_skills.append(skill)
        
        return list(set(found_skills))
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from a text block"""
        skills = []
        text_lower = text.lower()
        
        for skill in self.skill_keywords:
            if skill.lower() in text_lower:
                skills.append(skill)
        
        # Also extract comma/bullet separated skills
        skill_items = re.split(r'[,;\n•\-\*]', text)
        for item in skill_items:
            item = item.strip()
            if item and len(item) > 2:
                # Check if it matches any known skill
                for skill in self.skill_keywords:
                    if skill.lower() in item.lower():
                        if skill not in skills:
                            skills.append(skill)
                        break
        
        return skills
    
    def _extract_experience_years(self, text: str) -> Optional[int]:
        """Extract required years of experience"""
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)',
            r'(?:experience|exp)[:\s]+(\d+)\+?\s*(?:years?|yrs?)',
            r'minimum\s+of\s+(\d+)\s*(?:years?|yrs?)',
            r'at\s+least\s+(\d+)\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional|software|development|engineering|devops|infrastructure)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:in|with)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:relevant|related)',
        ]
        
        # Try each pattern
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    years = int(match.group(1))
                    # Prefer higher numbers (more specific requirements)
                    if years >= 1 and years <= 20:  # Reasonable range
                        return years
                except ValueError:
                    continue
        
        return None
    
    def _extract_seniority_level(self, text: str) -> Optional[str]:
        """Extract seniority level"""
        text_lower = text.lower()
        
        # Check title first (most reliable)
        title_match = re.search(r'^(junior|senior|mid|lead|principal|staff|executive|director)', text_lower)
        if title_match:
            title_word = title_match.group(1)
            for level, keywords in self.seniority_keywords.items():
                if title_word in keywords:
                    return level
        
        # Check in description
        for level, keywords in self.seniority_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return level
        
        # Infer from experience years if available
        experience = self._extract_experience_years(text)
        if experience:
            if experience >= 7:
                return "senior"
            elif experience >= 4:
                return "mid"
            elif experience >= 1:
                return "junior"
        
        return None
    
    def _extract_education_requirements(self, text: str) -> List[str]:
        """Extract education requirements"""
        education = []
        
        patterns = [
            r'(?:bachelor|bs|b\.?s\.?|b\.?a\.?)\s+(?:degree|in)',
            r'(?:master|ms|m\.?s\.?|m\.?a\.?|mba)\s+(?:degree|in)',
            r'(?:ph\.?d|doctorate)',
            r'(?:high\s+school|diploma)',
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower):
                education.append(pattern)
        
        return education
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract job location"""
        # Look for location patterns
        location_patterns = [
            r'location[:\s]+([^\n]+)',
            r'based\s+in\s+([^\n,]+)',
            r'office\s+location[:\s]+([^\n]+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_remote_allowed(self, text: str) -> bool:
        """Check if remote work is allowed"""
        text_lower = text.lower()
        remote_keywords = ["remote", "work from home", "wfh", "distributed", "anywhere"]
        not_remote_keywords = ["on-site", "on site", "office", "onsite"]
        
        has_remote = any(keyword in text_lower for keyword in remote_keywords)
        has_not_remote = any(keyword in text_lower for keyword in not_remote_keywords)
        
        return has_remote and not has_not_remote
    
    def _extract_employment_type(self, text: str) -> Optional[str]:
        """Extract employment type"""
        text_lower = text.lower()
        
        if "full-time" in text_lower or "full time" in text_lower:
            return "full-time"
        elif "part-time" in text_lower or "part time" in text_lower:
            return "part-time"
        elif "contract" in text_lower:
            return "contract"
        elif "internship" in text_lower or "intern" in text_lower:
            return "internship"
        
        return None

