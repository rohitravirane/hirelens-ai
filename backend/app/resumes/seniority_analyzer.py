"""
World-Class Elite Seniority Detection System
Comprehensive resume analysis with red flag detection
"""
from typing import Dict, List, Any, Optional
import json
import requests
import structlog
import re
from datetime import datetime

logger = structlog.get_logger()

# Ollama configuration
OLLAMA_ENDPOINT = "http://host.docker.internal:11434"
OLLAMA_MODEL = "qwen2.5:7b-instruct-q4_K_M"


class EliteSeniorityAnalyzer:
    """
    World-Class Seniority Detection System
    
    Features:
    - Comprehensive resume analysis (entire resume, not just title)
    - Smart seniority detection (never returns "unknown")
    - Red flag detection (brutally honest assessment)
    - Evidence-based reasoning
    - Elite-level accuracy
    """
    
    def __init__(self):
        self.ollama_endpoint = OLLAMA_ENDPOINT
        self.model = OLLAMA_MODEL
        self.available = self._check_ollama_availability()
        
        if self.available:
            logger.info("elite_seniority_analyzer_initialized", model=self.model)
        else:
            logger.warning("elite_seniority_analyzer_unavailable", endpoint=self.ollama_endpoint)
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning("ollama_not_available_for_seniority", error=str(e))
            return False
    
    def _build_elite_seniority_prompt(
        self,
        resume_data: Dict[str, Any],
        raw_text: str
    ) -> str:
        """
        Build world-class comprehensive prompt for seniority analysis
        """
        # Extract all relevant information
        experience_years = resume_data.get("experience_years", 0)
        experience_list = resume_data.get("experience", [])
        projects = resume_data.get("projects", [])
        education = resume_data.get("education", [])
        skills = resume_data.get("skills", [])
        
        # Format experience for analysis
        experience_text = ""
        if experience_list:
            for exp in experience_list[:10]:  # Last 10 positions
                title = exp.get("title", "Unknown")
                company = exp.get("company", "Unknown")
                duration = exp.get("duration", "")
                description = exp.get("description", "")
                experience_text += f"\n- {title} at {company} ({duration})\n  {description}\n"
        
        # Format projects
        projects_text = ""
        if projects:
            for proj in projects[:10]:
                name = proj.get("name", "Unknown")
                description = proj.get("description", "")
                tech = proj.get("technologies", [])
                projects_text += f"\n- {name}: {description}\n  Tech: {', '.join(tech) if tech else 'N/A'}\n"
        
        prompt = f"""You are an elite HR expert with 30+ years of experience in technical recruitment. Your task is to perform a BRUTALLY HONEST, COMPREHENSIVE analysis of a candidate's seniority level based on their ENTIRE resume.

# TASK: Elite Seniority Level Detection

## CANDIDATE RESUME DATA:

**Total Experience:** {experience_years} years

**Work Experience:**
{experience_text if experience_text else 'No experience listed'}

**Projects:**
{projects_text if projects_text else 'No projects listed'}

**Skills:** {', '.join(skills) if skills else 'Not specified'}

**Education:** {json.dumps(education, indent=2) if education else 'Not provided'}

**Full Resume Text (for context):**
{raw_text[:3000] if raw_text else 'Not available'}

## YOUR TASK:

Analyze the ENTIRE resume comprehensively and determine the candidate's seniority level. Be BRUTALLY HONEST and identify ANY red flags.

### SENIORITY LEVELS:
1. **intern** - No professional experience, student/intern
2. **junior** - 0-2 years, entry-level, needs supervision
3. **mid** - 2-5 years, independent contributor, some mentoring
4. **senior** - 5-10 years, technical leader, mentors others, architecture decisions
5. **lead** - 8-12 years, team lead, cross-functional impact, strategic thinking
6. **principal** - 10+ years, technical authority, system design, multiple teams
7. **staff** - 12+ years, organization-wide impact, thought leadership
8. **executive** - C-level, VP, Director roles

### ANALYSIS CRITERIA (Analyze ALL of these):

1. **YEARS OF EXPERIENCE**
   - Total years in industry
   - Relevant experience vs total
   - Career progression timeline

2. **ROLE TITLES & PROGRESSION**
   - Current/latest title
   - Title progression over time
   - Leadership indicators (Lead, Principal, Staff, Manager, Director)
   - Team size managed (if any)

3. **RESPONSIBILITIES & IMPACT**
   - Technical depth (architecture, design, system design)
   - Leadership activities (mentoring, code reviews, technical decisions)
   - Business impact (scale, revenue, users affected)
   - Cross-functional collaboration

4. **TECHNICAL DEPTH**
   - Complexity of projects
   - Technologies mastered (not just used)
   - Problem-solving sophistication
   - Innovation and optimization work

5. **RED FLAGS (Be BRUTAL - identify these honestly):**
   - **Job Hopping**: Too many jobs in short time (<1 year average)
   - **Title Inflation**: Senior title but junior responsibilities
   - **Experience Mismatch**: Years don't match claimed seniority
   - **Gap Issues**: Long unexplained gaps (>6 months)
   - **Skill Inconsistency**: Skills don't match experience level
   - **Overstatement**: Claims don't match evidence in resume
   - **Career Regression**: Moving to lower-level roles
   - **No Progression**: Same level for 5+ years without growth
   - **Weak Evidence**: Vague descriptions, no metrics, no impact
   - **Education Mismatch**: Education doesn't support claimed level

6. **POSITIVE SIGNALS:**
   - Clear career progression
   - Increasing responsibility over time
   - Leadership and mentoring evidence
   - Technical depth and complexity
   - Measurable impact and achievements
   - Continuous learning and growth

## OUTPUT FORMAT (JSON ONLY):

Provide your analysis in this EXACT JSON structure:

{{
  "seniority_level": "<intern|junior|mid|senior|lead|principal|staff|executive>",
  "confidence": <0.0-1.0 float>,
  "evidence": [
    "Evidence point 1 with specific details",
    "Evidence point 2 with specific details",
    "Evidence point 3 with specific details"
  ],
  "red_flags": [
    {{
      "severity": "<critical|major|minor>",
      "type": "<job_hopping|title_inflation|experience_mismatch|gap_issues|skill_inconsistency|overstatement|career_regression|no_progression|weak_evidence|education_mismatch>",
      "description": "Brutally honest description of the red flag",
      "impact": "How this affects the candidate's seniority assessment"
    }}
  ],
  "positive_signals": [
    "Positive signal 1 with evidence",
    "Positive signal 2 with evidence"
  ],
  "detailed_analysis": {{
    "years_analysis": {{
      "total_years": <float>,
      "relevant_years": <float>,
      "assessment": "Analysis of years of experience"
    }},
    "title_analysis": {{
      "current_title": "<title>",
      "progression": "Analysis of title progression",
      "leadership_indicators": ["indicator1", "indicator2"]
    }},
    "responsibility_analysis": {{
      "technical_depth": "<low|medium|high|expert>",
      "leadership_activities": ["activity1", "activity2"],
      "business_impact": "Assessment of business impact"
    }},
    "technical_depth_analysis": {{
      "complexity_level": "<low|medium|high|expert>",
      "mastery_indicators": ["indicator1", "indicator2"],
      "innovation_work": "Evidence of innovation"
    }}
  }},
  "reasoning": "2-3 sentence explanation of why this seniority level was determined, considering all factors including red flags"
}}

## CRITICAL REQUIREMENTS:

1. **NEVER return "unknown"** - Always determine a level based on evidence
2. **Be BRUTAL about red flags** - Don't sugarcoat issues
3. **Be COMPREHENSIVE** - Analyze entire resume, not just title
4. **Be EVIDENCE-BASED** - Base assessment on actual resume content
5. **Be CONSISTENT** - Use same criteria for all candidates
6. **Be HONEST** - If someone is junior, say junior. If senior, say senior.

## SCORING GUIDELINES:

- **intern**: Student, no professional experience
- **junior**: 0-2 years, needs guidance, basic tasks
- **mid**: 2-5 years, independent, some mentoring
- **senior**: 5-10 years, technical leader, mentors, architecture
- **lead**: 8-12 years, team lead, cross-functional, strategic
- **principal**: 10+ years, technical authority, system design
- **staff**: 12+ years, org-wide impact, thought leadership
- **executive**: C-level, VP, Director

Now provide your BRUTAL, HONEST analysis in the JSON format above. Analyze the ENTIRE resume comprehensively."""

        return prompt
    
    def analyze_seniority(
        self,
        resume_data: Dict[str, Any],
        raw_text: str
    ) -> Dict[str, Any]:
        """
        Analyze seniority level with comprehensive resume analysis
        
        Returns:
            Dict with seniority level, confidence, evidence, red flags, etc.
        """
        if not self.available:
            logger.warning("ollama_not_available_falling_back_to_rule_based")
            return self._fallback_seniority_analysis(resume_data, raw_text)
        
        try:
            prompt = self._build_elite_seniority_prompt(resume_data, raw_text)
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Low temperature for consistency
                        "top_p": 0.9,
                        "max_tokens": 3000,
                    }
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Extract JSON from response
                json_text = self._extract_json_from_response(response_text)
                
                if json_text:
                    analysis = json.loads(json_text)
                    
                    # Validate and ensure we never return "unknown"
                    if analysis.get("seniority_level", "").lower() == "unknown":
                        analysis = self._infer_seniority_from_evidence(resume_data, analysis)
                    
                    logger.info("elite_seniority_analysis_generated", 
                              seniority=analysis.get("seniority_level"),
                              confidence=analysis.get("confidence"))
                    return analysis
                else:
                    logger.error("failed_to_parse_seniority_response", response_preview=response_text[:200])
                    return self._fallback_seniority_analysis(resume_data, raw_text)
            else:
                logger.error("ollama_api_error_for_seniority", status_code=response.status_code)
                return self._fallback_seniority_analysis(resume_data, raw_text)
                
        except Exception as e:
            logger.error("elite_seniority_analysis_failed", error=str(e))
            return self._fallback_seniority_analysis(resume_data, raw_text)
    
    def _extract_json_from_response(self, response_text: str) -> Optional[str]:
        """Extract JSON from LLM response"""
        # Remove markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                return response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                return response_text[start:end].strip()
        
        # Try to find JSON object directly
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            return response_text[start:end].strip()
        
        return None
    
    def _infer_seniority_from_evidence(
        self,
        resume_data: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Infer seniority from evidence if LLM returned unknown"""
        experience_years = resume_data.get("experience_years", 0)
        experience_list = resume_data.get("experience", [])
        
        # Analyze titles
        titles = []
        if experience_list:
            for exp in experience_list:
                title = exp.get("title", "").lower()
                titles.append(title)
        
        # Determine based on years and titles
        if experience_years == 0:
            level = "intern"
        elif experience_years < 2:
            level = "junior"
        elif experience_years < 5:
            level = "mid"
        elif experience_years < 8:
            level = "senior"
        elif experience_years < 12:
            level = "lead"
        else:
            level = "principal"
        
        # Check for leadership titles
        leadership_keywords = ["lead", "principal", "staff", "manager", "director", "vp", "chief"]
        if any(kw in " ".join(titles) for kw in leadership_keywords):
            if experience_years >= 10:
                level = "principal"
            elif experience_years >= 8:
                level = "lead"
        
        analysis["seniority_level"] = level
        analysis["confidence"] = 0.7  # Lower confidence for inferred
        analysis["reasoning"] = f"Inferred {level} based on {experience_years} years of experience and role titles"
        
        return analysis
    
    def _fallback_seniority_analysis(
        self,
        resume_data: Dict[str, Any],
        raw_text: str
    ) -> Dict[str, Any]:
        """Fallback rule-based seniority analysis (never returns unknown)"""
        experience_years = resume_data.get("experience_years", 0)
        experience_list = resume_data.get("experience", [])
        
        # Analyze titles
        titles = []
        leadership_indicators = []
        if experience_list:
            for exp in experience_list:
                title = exp.get("title", "").lower()
                titles.append(title)
                
                # Check for leadership
                if any(kw in title for kw in ["lead", "principal", "staff", "manager", "director", "vp", "chief", "head"]):
                    leadership_indicators.append(title)
        
        # Determine level based on years
        if experience_years == 0:
            level = "intern"
            confidence = 0.9
        elif experience_years < 2:
            level = "junior"
            confidence = 0.85
        elif experience_years < 5:
            level = "mid"
            confidence = 0.8
        elif experience_years < 8:
            level = "senior"
            confidence = 0.75
        elif experience_years < 12:
            level = "lead"
            confidence = 0.7
        else:
            level = "principal"
            confidence = 0.65
        
        # Adjust based on leadership titles
        if leadership_indicators:
            if experience_years >= 10:
                level = "principal"
            elif experience_years >= 8:
                level = "lead"
            elif experience_years >= 5:
                level = "senior"
            confidence = min(confidence + 0.1, 0.95)
        
        # Check for red flags
        red_flags = []
        if experience_list and len(experience_list) > 0:
            # Job hopping check
            avg_duration = experience_years / len(experience_list) if len(experience_list) > 0 else 0
            if avg_duration < 1.0 and len(experience_list) >= 3:
                red_flags.append({
                    "severity": "major",
                    "type": "job_hopping",
                    "description": f"Average job duration is {avg_duration:.1f} years, indicating frequent job changes",
                    "impact": "May indicate instability or inability to commit"
                })
        
        return {
            "seniority_level": level,
            "confidence": confidence,
            "evidence": [
                f"{experience_years} years of professional experience",
                f"Current/latest roles: {', '.join(titles[:3])}" if titles else "No role titles found"
            ],
            "red_flags": red_flags,
            "positive_signals": leadership_indicators[:3] if leadership_indicators else [],
            "detailed_analysis": {
                "years_analysis": {
                    "total_years": experience_years,
                    "relevant_years": experience_years,
                    "assessment": f"{experience_years} years of experience indicates {level} level"
                },
                "title_analysis": {
                    "current_title": titles[0] if titles else "Unknown",
                    "progression": "Analyzed from experience list",
                    "leadership_indicators": leadership_indicators
                }
            },
            "reasoning": f"Determined {level} level based on {experience_years} years of experience and role analysis"
        }


# Global instance
elite_seniority_analyzer = EliteSeniorityAnalyzer()

