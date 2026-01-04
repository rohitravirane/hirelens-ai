"""
Scoring engine for candidate-job matching
"""
from typing import Dict, List, Any, Optional, Set, Tuple
import structlog
import re
from difflib import SequenceMatcher

from app.ai_engine.service import ai_engine

logger = structlog.get_logger()


class ScoringEngine:
    """Multi-dimensional scoring engine"""
    
    # Scoring weights (configurable)
    WEIGHTS = {
        "skill_match": 0.40,  # Highest weight
        "experience": 0.25,
        "project_similarity": 0.20,
        "domain_familiarity": 0.15,
    }
    
    # Common skill aliases and variations
    SKILL_ALIASES = {
        "js": ["javascript", "ecmascript"],
        "javascript": ["js", "ecmascript"],
        "react": ["reactjs", "react.js", "reactjs"],
        "reactjs": ["react", "react.js"],
        "react.js": ["react", "reactjs"],
        "node": ["nodejs", "node.js"],
        "nodejs": ["node", "node.js"],
        "node.js": ["node", "nodejs"],
        "vue": ["vuejs", "vue.js"],
        "vuejs": ["vue", "vue.js"],
        "vue.js": ["vue", "vuejs"],
        "angular": ["angularjs", "angular.js"],
        "angularjs": ["angular", "angular.js"],
        "angular.js": ["angular", "angularjs"],
        "typescript": ["ts"],
        "ts": ["typescript"],
        "html": ["html5"],
        "html5": ["html"],
        "css": ["css3"],
        "css3": ["css"],
        "python": ["py"],
        "py": ["python"],
        "java": ["spring", "spring framework", "spring boot", "hibernate", "j2ee", "jee"],
        "spring": ["java", "spring framework", "spring boot"],
        "spring framework": ["java", "spring", "spring boot"],
        "spring boot": ["java", "spring", "spring framework"],
        "hibernate": ["java"],
        "j2ee": ["java"],
        "jee": ["java"],
        "machine learning": ["ml", "machinelearning"],
        "ml": ["machine learning", "machinelearning"],
        "artificial intelligence": ["ai"],
        "ai": ["artificial intelligence"],
        "aws": ["amazon web services"],
        "amazon web services": ["aws"],
        "gcp": ["google cloud platform", "google cloud"],
        "google cloud platform": ["gcp", "google cloud"],
        "google cloud": ["gcp", "google cloud platform"],
        "azure": ["microsoft azure"],
        "microsoft azure": ["azure"],
        "kubernetes": ["k8s"],
        "k8s": ["kubernetes"],
        "docker": ["docker container"],
        "postgresql": ["postgres", "pg"],
        "postgres": ["postgresql", "pg"],
        "pg": ["postgresql", "postgres"],
        "mongodb": ["mongo"],
        "mongo": ["mongodb"],
        "redis": ["redis cache"],
        "git": ["git version control"],
        "rest": ["rest api", "restful api", "rest apis"],
        "rest api": ["rest", "restful api", "rest apis"],
        "rest apis": ["rest", "rest api", "restful api"],
        "restful api": ["rest", "rest api", "rest apis"],
        "graphql": ["graph ql"],
        "graph ql": ["graphql"],
        "sql": ["mysql", "postgresql", "postgres", "sql server", "mssql", "oracle"],
        "mysql": ["sql"],
        "mssql": ["sql", "sql server"],
        "sql server": ["sql", "mssql"],
        "oracle": ["sql"],
        "scrum": ["scrum/agile", "agile", "scrum agile"],
        "agile": ["scrum", "scrum/agile", "scrum agile"],
        "scrum/agile": ["scrum", "agile"],
        "scrum agile": ["scrum", "agile"],
        "net": [".net", "dotnet", "dot net"],
        ".net": ["net", "dotnet", "dot net"],
        "dotnet": ["net", ".net", "dot net"],
        "dot net": ["net", ".net", "dotnet"],
        "next.js": ["nextjs", "next js"],
        "nextjs": ["next.js", "next js"],
        "next js": ["next.js", "nextjs"],
    }
    
    def calculate_match_score(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Calculate comprehensive match score
        Returns scores for all dimensions plus overall score
        """
        scores = {
            "skill_match_score": self._calculate_skill_match(candidate_data, job_data),
            "experience_score": self._calculate_experience_score(candidate_data, job_data),
            "project_similarity_score": self._calculate_project_similarity(candidate_data, job_data),
            "domain_familiarity_score": self._calculate_domain_familiarity(candidate_data, job_data),
        }
        
        # Calculate weighted overall score
        overall_score = (
            scores["skill_match_score"] * self.WEIGHTS["skill_match"] +
            scores["experience_score"] * self.WEIGHTS["experience"] +
            scores["project_similarity_score"] * self.WEIGHTS["project_similarity"] +
            scores["domain_familiarity_score"] * self.WEIGHTS["domain_familiarity"]
        )
        
        scores["overall_score"] = round(overall_score, 2)
        
        # Determine confidence level
        if overall_score >= 80:
            scores["confidence_level"] = "high"
        elif overall_score >= 60:
            scores["confidence_level"] = "medium"
        else:
            scores["confidence_level"] = "low"
        
        return scores
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize a skill name for matching"""
        if not skill:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = skill.lower().strip()
        
        # Remove special characters except spaces and hyphens
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        
        # Replace multiple spaces/hyphens with single space
        normalized = re.sub(r'[\s-]+', ' ', normalized)
        
        # Handle common plural/singular forms for better matching
        # Remove trailing 's' for common tech terms (but be careful)
        # Only do this for known tech terms to avoid false positives
        tech_plurals = {
            'apis': 'api',
            'frameworks': 'framework',
            'tools': 'tool',
            'languages': 'language',
        }
        words = normalized.split()
        if len(words) == 2 and words[-1] in tech_plurals:
            # e.g., "rest apis" -> "rest api"
            normalized = f"{words[0]} {tech_plurals[words[-1]]}"
        elif normalized.endswith('s') and len(normalized) > 4:
            # For single-word skills ending in 's', try both forms
            # We'll handle this in matching logic, not here
            pass
        
        # Remove leading/trailing spaces
        normalized = normalized.strip()
        
        return normalized
    
    def _get_skill_variations(self, skill: str) -> Set[str]:
        """Get all variations and aliases of a skill"""
        normalized = self._normalize_skill(skill)
        variations = {normalized}
        
        # Add aliases
        if normalized in self.SKILL_ALIASES:
            for alias in self.SKILL_ALIASES[normalized]:
                variations.add(self._normalize_skill(alias))
        
        # Also check reverse lookup (if alias is the skill, add main skill)
        for main_skill, aliases in self.SKILL_ALIASES.items():
            if normalized in [self._normalize_skill(a) for a in aliases]:
                variations.add(self._normalize_skill(main_skill))
                variations.update([self._normalize_skill(a) for a in aliases])
        
        return variations
    
    def _skills_match(self, skill1: str, skill2: str, threshold: float = 0.85) -> bool:
        """
        Check if two skills match using smart matching
        Returns True if skills match (exact, alias, or fuzzy)
        """
        # Normalize both skills
        norm1 = self._normalize_skill(skill1)
        norm2 = self._normalize_skill(skill2)
        
        # Exact match after normalization
        if norm1 == norm2:
            return True
        
        # Check if they're aliases (this is the most reliable method)
        variations1 = self._get_skill_variations(skill1)
        variations2 = self._get_skill_variations(skill2)
        
        if variations1.intersection(variations2):
            return True
        
        # Fuzzy matching for similar skills (but be careful with short names)
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        if similarity >= threshold:
            # Additional check: don't match if one is clearly a substring of a longer different word
            # e.g., "java" should NOT match "javascript" even if similarity is high
            if len(norm1) >= 4 and len(norm2) >= 4:  # Both must be at least 4 chars for fuzzy match
                return True
        
        # Handle plural/singular variations
        # e.g., "rest apis" vs "rest api"
        norm1_singular = norm1.rstrip('s') if norm1.endswith('s') and len(norm1) > 3 else norm1
        norm2_singular = norm2.rstrip('s') if norm2.endswith('s') and len(norm2) > 3 else norm2
        if norm1_singular == norm2 or norm2_singular == norm1 or norm1_singular == norm2_singular:
            # But avoid false positives like "j" matching "js"
            if min(len(norm1_singular), len(norm2_singular)) >= 3:
                return True
        
        # Check if one skill contains the other (for compound skills)
        # But be very strict to avoid false positives like "java" in "javascript"
        if norm1 in norm2 or norm2 in norm1:
            shorter = min(len(norm1), len(norm2))
            longer = max(len(norm1), len(norm2))
            # Only match if:
            # 1. Shorter is at least 4 chars (avoid "js" matching "javascript")
            # 2. The longer one is not much longer (avoid "java" matching "javascript")
            if shorter >= 4 and (longer - shorter) <= 3:
                # Additional check: don't match if it's a known false positive
                false_positives = [
                    ("java", "javascript"),
                    ("js", "javascript"),
                    ("net", "internet"),
                    ("go", "golang"),
                ]
                for fp1, fp2 in false_positives:
                    if (norm1 == fp1 and norm2 == fp2) or (norm1 == fp2 and norm2 == fp1):
                        return False
                return True
        
        return False
    
    def _find_matching_skills(
        self,
        candidate_skills: List[str],
        required_skills: List[str]
    ) -> Tuple[Set[str], Set[str]]:
        """
        Find matching skills between candidate and required skills using smart matching
        Returns: (matched_required_skills, matched_candidate_skills)
        """
        matched_required = set()
        matched_candidate = set()
        
        # Handle None or empty cases
        if not candidate_skills or not required_skills:
            return matched_required, matched_candidate
        
        # Ensure we're working with lists of strings
        candidate_skills = [str(s) for s in candidate_skills if s]
        required_skills = [str(s) for s in required_skills if s]
        
        for req_skill in required_skills:
            if not req_skill:  # Skip empty strings
                continue
            for cand_skill in candidate_skills:
                if not cand_skill:  # Skip empty strings
                    continue
                if self._skills_match(req_skill, cand_skill):
                    matched_required.add(req_skill)
                    matched_candidate.add(cand_skill)
                    break  # Each required skill matches at most one candidate skill
        
        return matched_required, matched_candidate
    
    def _calculate_skill_match(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> float:
        """Calculate skill match score (0-100) using smart matching"""
        candidate_skills_list = candidate_data.get("skills", []) or []
        required_skills_list = job_data.get("required_skills", []) or []
        nice_to_have_skills_list = job_data.get("nice_to_have_skills", []) or []
        
        if not required_skills_list:
            # If no required skills specified, give base score
            return 50.0
        
        # Find matching required skills using smart matching
        matched_required, _ = self._find_matching_skills(
            candidate_skills_list,
            required_skills_list
        )
        
        # Calculate required skills score (70% weight)
        required_score = (len(matched_required) / len(required_skills_list)) * 70 if required_skills_list else 0
        
        # Find matching nice-to-have skills
        matched_nice, _ = self._find_matching_skills(
            candidate_skills_list,
            nice_to_have_skills_list
        )
        
        # Calculate nice-to-have skills score (30% weight)
        nice_score = (len(matched_nice) / len(nice_to_have_skills_list)) * 30 if nice_to_have_skills_list else 0
        
        total_score = required_score + nice_score
        
        # Bonus for having extra relevant skills
        candidate_skill_count = len(set(self._normalize_skill(s) for s in candidate_skills_list))
        required_skill_count = len(required_skills_list)
        if candidate_skill_count > required_skill_count:
            bonus = min(10, (candidate_skill_count - required_skill_count) * 2)
            total_score = min(100, total_score + bonus)
        
        return round(total_score, 2)
    
    def _calculate_experience_score(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> float:
        """Calculate experience relevance score (0-100)"""
        candidate_years = candidate_data.get("experience_years", 0) or 0
        required_years = job_data.get("experience_years_required", 0) or 0
        
        if required_years == 0:
            return 70.0  # Neutral score if no requirement
        
        if candidate_years >= required_years:
            # Has required or more experience
            excess = candidate_years - required_years
            if excess == 0:
                return 100.0
            elif excess <= 2:
                return 95.0
            elif excess <= 5:
                return 90.0
            else:
                return 85.0  # Overqualified
        else:
            # Less than required
            deficit = required_years - candidate_years
            if deficit <= 1:
                return 80.0
            elif deficit <= 2:
                return 60.0
            elif deficit <= 3:
                return 40.0
            else:
                return 20.0
    
    def _calculate_project_similarity(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> float:
        """Calculate project similarity score (0-100)"""
        candidate_projects = candidate_data.get("projects", [])
        if not candidate_projects:
            return 30.0  # Low score if no projects
        
        # Extract keywords from job description
        job_text = job_data.get("raw_text", "").lower()
        job_keywords = set(job_data.get("required_skills", []) + job_data.get("nice_to_have_skills", []))
        
        # Check project descriptions for relevance
        relevant_projects = 0
        for project in candidate_projects[:5]:  # Check top 5 projects
            project_text = str(project.get("description", "") + " " + project.get("name", "")).lower()
            
            # Count keyword matches
            matches = sum(1 for keyword in job_keywords if keyword.lower() in project_text)
            if matches >= 2:
                relevant_projects += 1
        
        if not candidate_projects:
            return 30.0
        
        score = (relevant_projects / min(len(candidate_projects), 5)) * 100
        return round(score, 2)
    
    def _calculate_domain_familiarity(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> float:
        """Calculate domain familiarity score (0-100)"""
        # Use semantic similarity of experience descriptions
        candidate_experience = candidate_data.get("experience", [])
        job_text = job_data.get("raw_text", "")
        
        if not candidate_experience or not job_text:
            return 50.0
        
        # Generate embeddings and calculate similarity
        try:
            # Combine candidate experience into text
            candidate_text = " ".join([
                exp.get("description", "") + " " + exp.get("title", "")
                for exp in candidate_experience[:3]
            ])
            
            # Generate embeddings
            candidate_embedding = ai_engine.generate_embedding(candidate_text[:1000])
            job_embedding = ai_engine.generate_embedding(job_text[:1000])
            
            # Calculate similarity
            similarity = ai_engine.calculate_semantic_similarity(candidate_embedding, job_embedding)
            
            # Convert to 0-100 score
            score = (similarity + 1) * 50  # Cosine similarity is -1 to 1, convert to 0-100
            return round(score, 2)
        except Exception as e:
            logger.error("domain_familiarity_calculation_failed", error=str(e))
            return 50.0  # Neutral score on error
    
    def calculate_percentile_rank(
        self,
        score: float,
        all_scores: List[float],
    ) -> float:
        """Calculate percentile rank of a score"""
        if not all_scores:
            return 0.0
        
        sorted_scores = sorted(all_scores, reverse=True)
        rank = sum(1 for s in sorted_scores if s < score)
        percentile = (rank / len(sorted_scores)) * 100
        return round(percentile, 2)


# Global instance
scoring_engine = ScoringEngine()

