"""
Smart Resume Validator - Validates if uploaded document is actually a resume
Uses content analysis and pattern matching to detect resume-like documents
"""
import re
from typing import Dict, Tuple, List
import structlog

logger = structlog.get_logger()


class ResumeValidator:
    """Validate if a document is actually a resume/CV"""
    
    # Resume indicators (weighted)
    RESUME_INDICATORS = {
        # Contact information (high weight)
        'email_pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone_pattern': r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        
        # Professional keywords (medium weight)
        'job_titles': [
            'developer', 'engineer', 'manager', 'analyst', 'consultant', 'architect',
            'designer', 'specialist', 'coordinator', 'director', 'lead', 'senior',
            'junior', 'intern', 'executive', 'officer', 'administrator'
        ],
        
        # Experience indicators (high weight)
        'experience_keywords': [
            'experience', 'work history', 'employment', 'career', 'position',
            'role', 'responsibilities', 'achievements', 'projects'
        ],
        
        # Education indicators (high weight)
        'education_keywords': [
            'education', 'degree', 'university', 'college', 'institute',
            'bachelor', 'master', 'phd', 'diploma', 'certification', 'graduation'
        ],
        
        # Skills indicators (medium weight)
        'skills_keywords': [
            'skills', 'technologies', 'tools', 'programming', 'languages',
            'frameworks', 'platforms', 'software'
        ],
        
        # Date patterns (medium weight) - resume dates
        'date_pattern': r'\b(19|20)\d{2}\s*[-–—]\s*(?:19|20)?\d{2}|PRESENT|CURRENT\b',
        
        # Company indicators (medium weight)
        'company_indicators': ['pvt', 'ltd', 'inc', 'llc', 'corp', 'technologies', 'solutions', 'services'],
    }
    
    # Non-resume indicators (negative weight)
    NON_RESUME_INDICATORS = [
        # Document types
        'invoice', 'receipt', 'bill', 'contract', 'agreement', 'letter',
        'memo', 'report', 'proposal', 'presentation',
        
        # Academic paper indicators
        'abstract', 'references', 'bibliography', 'methodology', 'hypothesis',
        'experiment', 'results and discussion',
        
        # Business document indicators
        'terms and conditions', 'privacy policy', 'terms of service',
    ]
    
    MIN_RESUME_SCORE = 30  # Minimum score to be considered a resume
    MIN_TEXT_LENGTH = 200  # Minimum text length to be a valid resume
    
    def validate(self, text: str) -> Tuple[bool, Dict[str, any]]:
        """
        Validate if text represents a resume
        
        Returns:
            Tuple[is_valid, details_dict]
        """
        if not text or len(text.strip()) < self.MIN_TEXT_LENGTH:
            return False, {
                'reason': 'text_too_short',
                'score': 0,
                'details': 'Document text is too short to be a resume'
            }
        
        text_lower = text.lower()
        text_upper = text.upper()
        
        score = 0
        details = {
            'has_email': False,
            'has_phone': False,
            'has_dates': False,
            'job_title_count': 0,
            'experience_keywords_count': 0,
            'education_keywords_count': 0,
            'skills_keywords_count': 0,
            'company_indicators_count': 0,
            'non_resume_indicators_count': 0,
        }
        
        # Check email (high weight: +15)
        email_match = re.search(self.RESUME_INDICATORS['email_pattern'], text)
        if email_match:
            score += 15
            details['has_email'] = True
            details['email_found'] = email_match.group(0)
        
        # Check phone (high weight: +10)
        phone_match = re.search(self.RESUME_INDICATORS['phone_pattern'], text)
        if phone_match:
            score += 10
            details['has_phone'] = True
        
        # Check date patterns (medium weight: +10)
        date_matches = len(re.findall(self.RESUME_INDICATORS['date_pattern'], text_upper))
        if date_matches >= 2:  # At least 2 date ranges
            score += 10
            details['has_dates'] = True
            details['date_count'] = date_matches
        
        # Check job titles (medium weight: +2 each, max +10)
        job_title_count = sum(1 for title in self.RESUME_INDICATORS['job_titles'] if title in text_lower)
        job_title_score = min(job_title_count * 2, 10)
        score += job_title_score
        details['job_title_count'] = job_title_count
        
        # Check experience keywords (high weight: +3 each, max +15)
        exp_keywords_count = sum(1 for kw in self.RESUME_INDICATORS['experience_keywords'] if kw in text_lower)
        exp_score = min(exp_keywords_count * 3, 15)
        score += exp_score
        details['experience_keywords_count'] = exp_keywords_count
        
        # Check education keywords (high weight: +3 each, max +15)
        edu_keywords_count = sum(1 for kw in self.RESUME_INDICATORS['education_keywords'] if kw in text_lower)
        edu_score = min(edu_keywords_count * 3, 15)
        score += edu_score
        details['education_keywords_count'] = edu_keywords_count
        
        # Check skills keywords (medium weight: +2 each, max +10)
        skills_keywords_count = sum(1 for kw in self.RESUME_INDICATORS['skills_keywords'] if kw in text_lower)
        skills_score = min(skills_keywords_count * 2, 10)
        score += skills_score
        details['skills_keywords_count'] = skills_keywords_count
        
        # Check company indicators (medium weight: +1 each, max +5)
        company_count = sum(1 for indicator in self.RESUME_INDICATORS['company_indicators'] if indicator in text_lower)
        company_score = min(company_count, 5)
        score += company_score
        details['company_indicators_count'] = company_count
        
        # Negative indicators (penalty: -5 each)
        non_resume_count = sum(1 for indicator in self.NON_RESUME_INDICATORS if indicator in text_lower)
        penalty = min(non_resume_count * 5, 30)  # Max penalty of 30
        score -= penalty
        details['non_resume_indicators_count'] = non_resume_count
        details['penalty_applied'] = penalty
        
        # Bonus: If has both email AND phone (+5)
        if details['has_email'] and details['has_phone']:
            score += 5
        
        # Bonus: If has experience AND education keywords (+5)
        if exp_keywords_count > 0 and edu_keywords_count > 0:
            score += 5
        
        details['score'] = score
        details['is_valid'] = score >= self.MIN_RESUME_SCORE
        
        if not details['is_valid']:
            reasons = []
            if not details['has_email'] and not details['has_phone']:
                reasons.append('missing_contact_info')
            if details['experience_keywords_count'] == 0:
                reasons.append('no_experience_indicators')
            if details['education_keywords_count'] == 0:
                reasons.append('no_education_indicators')
            if details['non_resume_indicators_count'] > 0:
                reasons.append('contains_non_resume_content')
            details['reasons'] = reasons
            details['reason'] = 'low_resume_score'
        else:
            details['reason'] = 'valid_resume'
        
        logger.info("resume_validation_complete", 
                   is_valid=details['is_valid'], 
                   score=score,
                   has_contact=details['has_email'] or details['has_phone'])
        
        return details['is_valid'], details






