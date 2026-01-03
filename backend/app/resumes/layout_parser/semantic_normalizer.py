"""
Semantic normalization using local LLM (Ollama or Hugging Face)
Normalizes extracted data into structured JSON format
Supports: Ollama API (fast, pre-downloaded) or Hugging Face (slower, downloads on first use)
"""
from typing import Dict, List, Any, Optional
import json
import re
import structlog
import torch

logger = structlog.get_logger()

# Try to import Ollama support
try:
    import httpx
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Try to import Hugging Face support
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

# Global model instances (lazy loaded)
_tokenizer = None
_model = None
_device = None
_ollama_client = None
_ollama_model = None
_ollama_endpoint = None
_use_ollama = False


def _check_ollama_available(model_name: str = "qwen2.5:7b") -> bool:
    """Check if Ollama is available and model exists"""
    global _ollama_client, _ollama_model, _ollama_endpoint, _use_ollama
    
    if not OLLAMA_AVAILABLE:
        return False
    
    try:
        # Try multiple endpoints (Docker networking: host.docker.internal, WSL2: host gateway)
        ollama_endpoints = [
            "http://localhost:11434",  # Direct localhost
            "http://host.docker.internal:11434",  # Docker Desktop
            "http://172.17.0.1:11434",  # Docker bridge gateway
        ]
        
        client = None
        working_endpoint = None
        
        for endpoint in ollama_endpoints:
            try:
                test_client = httpx.Client(timeout=5.0)
                response = test_client.get(f"{endpoint}/api/tags")
                if response.status_code == 200:
                    client = test_client
                    working_endpoint = endpoint
                    break
            except Exception:
                continue
        
        if client is None:
            return False
        
        response = client.get(f"{working_endpoint}/api/tags")
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Check if Qwen model available (qwen2.5:7b, qwen2.5, qwen, etc.)
            qwen_models = [m for m in model_names if "qwen" in m.lower()]
            
            if qwen_models:
                # Prefer instruct models, then any Qwen model
                instruct_models = [m for m in qwen_models if "instruct" in m.lower()]
                if instruct_models:
                    _ollama_model = instruct_models[0]  # Use first instruct model
                else:
                    _ollama_model = qwen_models[0]  # Use first available Qwen model
                _ollama_client = client
                _ollama_endpoint = working_endpoint  # Store working endpoint
                _use_ollama = True
                logger.info("ollama_available_using_ollama", model=_ollama_model, endpoint=working_endpoint, available_models=qwen_models)
                return True
            else:
                logger.info("ollama_available_but_no_qwen_model", available_models=model_names)
                return False
        else:
            return False
    except Exception as e:
        logger.debug("ollama_not_available", error=str(e)[:100])
        return False


def _load_local_llm(model_name: str = "Qwen/Qwen2.5-7B-Instruct", device: Optional[str] = None):
    """Lazy load local LLM for semantic normalization
    Priority: Ollama (if available) > Hugging Face
    """
    global _tokenizer, _model, _device, _use_ollama
    
    # First, try Ollama (much faster, no download needed)
    if _check_ollama_available():
        logger.info("using_ollama_for_semantic_normalization", model=_ollama_model)
        return None, None, None  # Ollama doesn't need tokenizer/model objects
    
    # Fallback to Hugging Face
    if not HF_AVAILABLE:
        logger.warning("neither_ollama_nor_huggingface_available")
        return None, None, None
    
    if _tokenizer is None or _model is None:
        try:
            from app.core.config import settings
            
            # Determine device - Force GPU if available
            if device is None:
                if torch.cuda.is_available():
                    _device = "cuda"
                    logger.info("gpu_available_using_cuda")
                else:
                    _device = "cpu"
                    logger.warning("gpu_not_available_using_cpu")
            else:
                _device = device
                if _device == "cuda" and not torch.cuda.is_available():
                    logger.warning("cuda_requested_but_not_available_falling_back_to_cpu")
                    _device = "cpu"
            
            logger.info("loading_local_llm", model=model_name, device=_device)
            
            # Load tokenizer with proper configuration for Qwen2
            # Add timeout to prevent stuck downloads
            try:
                import os
                # Set timeout for Hugging Face downloads (30 seconds)
                os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "300"  # 5 minutes max
                
                _tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    use_fast=False,  # Use slow tokenizer for compatibility
                    local_files_only=False  # Allow download
                )
            except Exception as e:
                logger.warning("tokenizer_loading_failed_trying_fast", error=str(e))
                # Try with fast tokenizer
                _tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    use_fast=True
                )
            
            # Load model with quantization if CPU
            # Note: device_map='auto' may not work for all models, so we'll manually move to device
            if _device == "cpu":
                # Use 8-bit quantization for CPU
                try:
                    from transformers import BitsAndBytesConfig
                    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                    _model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        trust_remote_code=True,
                        torch_dtype=torch.float32,
                        quantization_config=quantization_config
                    )
                except Exception as e:
                    logger.warning("8bit_quantization_failed_using_fp32", error=str(e))
                    _model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        trust_remote_code=True,
                        torch_dtype=torch.float32
                    )
                    _model = _model.to(_device)
            else:
                # GPU: Use float16 for memory efficiency
                # Add timeout and resume_download for large models
                _model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                    low_cpu_mem_usage=True,
                    resume_download=True  # Resume if download interrupted
                )
                # Manually move to device (device_map='auto' may not work)
                _model = _model.to(_device)
            
            _model.eval()
            
            logger.info("local_llm_loaded", model=model_name, device=_device)
            
        except ImportError as e:
            logger.error("local_llm_import_failed", error=str(e))
            _tokenizer = None
            _model = None
        except Exception as e:
            logger.error("local_llm_loading_failed", error=str(e))
            _tokenizer = None
            _model = None
    
    return _tokenizer, _model, _device


class SemanticNormalizer:
    """
    Normalizes extracted resume data using local LLM
    Converts layout-extracted blocks into structured JSON
    """
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-7B-Instruct", device: Optional[str] = None):
        """
        Initialize semantic normalizer
        
        Args:
            model_name: Model name (Ollama model name or HuggingFace model name)
            device: Device to use ('cuda' or 'cpu') - only for Hugging Face
        """
        self.model_name = model_name
        self.tokenizer, self.model, self.device = _load_local_llm(model_name, device)
        # Available if Ollama is being used OR Hugging Face models loaded
        self.is_available = _use_ollama or (self.tokenizer is not None and self.model is not None)
        self.use_ollama = _use_ollama
    
    def normalize(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        header_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize extracted sections into structured JSON
        
        Args:
            sections: Dict of section name -> text blocks
            header_info: Header information (name, contact, etc.)
            
        Returns:
            Normalized structured data
        """
        if not self.is_available:
            logger.warning("local_llm_not_available_using_rule_based")
            return self._rule_based_normalize(sections, header_info)
        
        try:
            # Build prompt from sections
            prompt = self._build_normalization_prompt(sections, header_info)
            
            # Generate normalized output
            normalized = self._generate_normalized_output(prompt)
            
            logger.info("semantic_normalization_complete")
            return normalized
            
        except Exception as e:
            logger.error("semantic_normalization_failed", error=str(e))
            return self._rule_based_normalize(sections, header_info)
    
    def _build_normalization_prompt(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        header_info: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM normalization"""
        
        # Extract text from sections
        section_texts = {}
        for section_name, blocks in sections.items():
            section_text = "\n".join(
                self._extract_text_from_block(block)
                for block in blocks
            )
            section_texts[section_name] = section_text
        
        prompt = f"""You are an expert resume parser. Extract and normalize the following resume information into structured JSON.

Header Information:
{json.dumps(header_info, indent=2)}

Sections:
{json.dumps(section_texts, indent=2)}

Extract and normalize into this EXACT JSON structure:
{{
  "name": "Full name",
  "email": "Email if found",
  "phone": "Phone if found",
  "contact": {{
    "email": "...",
    "phone": "...",
    "location": "...",
    "linkedin": "...",
    "github": "...",
    "portfolio": "..."
  }},
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "start_date": "YYYY-MM or YYYY",
      "end_date": "YYYY-MM or YYYY or 'present'",
      "location": "Location if mentioned",
      "description": "Full description",
      "technologies": ["tech1", "tech2"],
      "metrics": ["metric1", "metric2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "Institution name",
      "field": "Field of study",
      "year": "YYYY",
      "gpa": "GPA if mentioned",
      "location": "Location if mentioned"
    }}
  ],
  "skills": {{
    "technical": ["skill1", "skill2"],
    "languages": ["lang1", "lang2"],
    "tools": ["tool1", "tool2"],
    "frameworks": ["framework1", "framework2"]
  }},
  "projects": [
    {{
      "name": "Project name",
      "description": "Description",
      "technologies": ["tech1", "tech2"],
      "url": "URL if mentioned"
    }}
  ],
  "certifications": ["cert1", "cert2"],
  "languages": ["language1", "language2"],
  "leadership_signals": ["signal1", "signal2"],
  "metrics_extracted": ["metric1", "metric2"]
}}

Return ONLY valid JSON, no markdown, no explanations."""
        
        return prompt
    
    def _generate_with_ollama(self, prompt: str) -> Dict[str, Any]:
        """Generate normalized output using Ollama API"""
        global _ollama_client, _ollama_model, _ollama_endpoint
        
        try:
            # Call Ollama API using working endpoint
            response = _ollama_client.post(
                f"{_ollama_endpoint}/api/generate",
                json={
                    "model": _ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 2048
                    }
                },
                timeout=120.0  # 2 minutes timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                
                # Extract JSON from response
                json_text = self._extract_json_from_response(generated_text)
                
                # Parse JSON
                normalized = json.loads(json_text)
                
                logger.info("ollama_generation_successful", model=_ollama_model)
                return normalized
            else:
                logger.error("ollama_api_error", status_code=response.status_code)
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error("ollama_generation_failed", error=str(e))
            raise
    
    def _generate_normalized_output(self, prompt: str) -> Dict[str, Any]:
        """Generate normalized output using LLM (Ollama or Hugging Face)"""
        # Use Ollama if available (much faster)
        if self.use_ollama:
            return self._generate_with_ollama(prompt)
        
        # Fallback to Hugging Face
        try:
            # Format prompt for model
            if "Qwen" in self.model_name or self.model_name is None:
                messages = [
                    {"role": "system", "content": "You are an expert resume parser. Always return valid JSON only."},
                    {"role": "user", "content": prompt}
                ]
                text = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            else:
                # Mistral format
                text = f"<s>[INST] {prompt} [/INST]"
            
            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=2048)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=2048,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract JSON from response
            json_text = self._extract_json_from_response(generated_text)
            
            # Parse JSON
            normalized = json.loads(json_text)
            
            return normalized
            
        except Exception as e:
            logger.error("llm_generation_failed", error=str(e))
            raise
    
    def _extract_json_from_response(self, text: str) -> str:
        """Extract JSON from LLM response"""
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # If no JSON found, return empty structure
        return '{}'
    
    def _extract_text_from_block(self, block: Dict[str, Any]) -> str:
        """Extract text from a text block"""
        if "tokens" in block:
            tokens = block["tokens"]
            if isinstance(tokens, list):
                if isinstance(tokens[0], dict):
                    return " ".join(t.get("token", "") for t in tokens)
                else:
                    return " ".join(str(t) for t in tokens)
        return block.get("text", "")
    
    def _rule_based_normalize(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        header_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback rule-based normalization with improved extraction"""
        logger.info("using_rule_based_normalization")
        
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
        
        # Extract from sections with improved parsing
        for section_name, blocks in sections.items():
            section_text = "\n".join(
                self._extract_text_from_block(block)
                for block in blocks
            )
            
            if not section_text.strip():
                continue
            
            if section_name == "experience":
                # Extract experience entries
                experience_entries = self._extract_experience(section_text)
                normalized["experience"].extend(experience_entries)
                logger.info("rule_based_experience_extracted", count=len(experience_entries))
                
            elif section_name == "education":
                # Extract education entries
                education_entries = self._extract_education(section_text)
                normalized["education"].extend(education_entries)
                logger.info("rule_based_education_extracted", count=len(education_entries))
                
            elif section_name == "skills":
                # Extract skills (comma, newline, or bullet separated)
                skills = self._extract_skills(section_text)
                normalized["skills"]["technical"] = skills
                logger.info("rule_based_skills_extracted", count=len(skills))
                
            elif section_name == "projects":
                # Extract projects
                projects = self._extract_projects(section_text)
                normalized["projects"].extend(projects)
                logger.info("rule_based_projects_extracted", count=len(projects))
                
            elif section_name == "certifications":
                # Extract certifications
                certs = self._extract_certifications(section_text)
                normalized["certifications"].extend(certs)
                logger.info("rule_based_certifications_extracted", count=len(certs))
                
            elif section_name == "languages":
                # Extract languages
                languages = self._extract_languages(section_text)
                normalized["languages"] = languages
                normalized["skills"]["languages"] = languages  # Also add to skills
                logger.info("rule_based_languages_extracted", count=len(languages))
        
        return normalized
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract languages from text"""
        languages = []
        
        # Common language names
        common_languages = [
            "English", "Hindi", "Marathi", "Spanish", "French", "German", "Chinese",
            "Japanese", "Korean", "Portuguese", "Italian", "Russian", "Arabic",
            "Bengali", "Telugu", "Tamil", "Gujarati", "Kannada", "Malayalam", "Punjabi"
        ]
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Pattern: "Language: Proficiency" or "Language - Proficiency"
            lang_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[:–-]\s*(.+)$', line)
            if lang_match:
                lang_name = lang_match.group(1).strip()
                # Verify it's a known language
                if any(common_lang.lower() in lang_name.lower() for common_lang in common_languages):
                    languages.append(lang_name)
            else:
                # Just language name
                for common_lang in common_languages:
                    if common_lang.lower() in line.lower() and len(line) < 30:
                        languages.append(common_lang)
                        break
        
        # Remove duplicates
        return list(dict.fromkeys(languages))  # Preserves order
    
    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract experience entries from text - IMPROVED with better company/title/date detection"""
        experience = []
        
        # Split by double newlines (each experience entry is usually separated by blank lines)
        entries = re.split(r'\n\s*\n+', text)
        
        for entry in entries:
            entry = entry.strip()
            if not entry or len(entry) < 10:
                continue
            
            # STRICT: Filter out education entries (contain "University", "College", "Bachelor", "Master", etc.)
            # Also filter if entry starts with education keywords
            education_keywords = r'\b(University|College|Institute|Bachelor|Master|MCA|BSc|MSc|BTech|MTech|Degree|Diploma|Academic|Coursework)\b'
            if re.search(education_keywords, entry, re.IGNORECASE):
                # Additional check: if it's clearly an education entry (has year range like "2019 - 2021" with education keywords)
                if re.search(r'\d{4}\s*[-–—]\s*\d{4}', entry) and re.search(education_keywords, entry, re.IGNORECASE):
                    continue  # Skip education entries
                # If entry contains "Pune University", "Mumbai University" etc. as main content, skip
                if re.search(r'\b(Pune|Mumbai|Delhi|Bangalore|Chennai|Hyderabad|Kolkata)\s+University\b', entry, re.IGNORECASE):
                    continue
            
            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if not lines:
                continue
            
            # Extract dates FIRST - look for patterns like "2021 - PRESENT", "2019 - 2020", etc.
            start_date = None
            end_date = None
            date_line_index = None
            
            # Improved date pattern: handles "YYYY - PRESENT", "YYYY - YYYY", "YYYY-MM - YYYY-MM"
            date_pattern = r'(\d{4}(?:-\d{2})?)\s*[-–—]\s*(\d{4}(?:-\d{2})?|PRESENT|CURRENT|NOW|present|current|now)'
            for i, line in enumerate(lines):
                date_match = re.search(date_pattern, line, re.IGNORECASE)
                if date_match:
                    start_date = date_match.group(1)
                    end_date_str = date_match.group(2).upper()
                    if end_date_str in ["PRESENT", "CURRENT", "NOW"]:
                        end_date = "present"
                    else:
                        end_date = end_date_str
                    date_line_index = i
                    break
            
            # Extract company name (usually comes BEFORE dates, contains "Pvt", "Ltd", "Technologies", etc.)
            # OR all caps company name
            company = None
            company_patterns = [
                r'^([A-Z][A-Za-z0-9\s&]+(?:Pvt|Ltd|LLC|Inc|Corp|Corporation|Technologies|Solutions|Services|Systems|Group|Company|Co|Progress)\.?)$',  # Company with suffix
                r'^([A-Z][A-Za-z0-9\s&]{3,50}(?:Pvt|Ltd|LLC|Inc|Corp|Corporation|Technologies|Solutions|Services|Systems|Group|Company|Co|Progress)\.?)$',  # Longer company names
            ]
            
            # Try to find company BEFORE date line (company usually comes first)
            for i, line in enumerate(lines):
                # Skip date line
                if date_line_index is not None and i == date_line_index:
                    continue
                
                # Check if line matches company pattern
                for pattern in company_patterns:
                    match = re.match(pattern, line)
                    if match:
                        potential_company = match.group(1).strip()
                        # Verify it's not a job title (titles usually have "Developer", "Engineer", etc.)
                        # But allow if it's clearly a company (has Pvt/Ltd/etc.)
                        if re.search(r'\b(Pvt|Ltd|LLC|Inc|Corp|Technologies|Solutions|Services|Systems|Group|Company|Co|Progress)\b', potential_company, re.IGNORECASE):
                            company = potential_company
                            break
                        # Also check: if line doesn't contain job title keywords, it might be company
                        if not re.search(r'\b(Developer|Engineer|Manager|Designer|Analyst|Specialist|Lead|Senior|Junior|Stack|Full)\b', potential_company, re.IGNORECASE):
                            # Additional check: if it's all caps and reasonable length, might be company
                            if potential_company.isupper() and 5 <= len(potential_company) <= 50:
                                company = potential_company
                                break
                if company:
                    break
            
            # Extract job title (usually contains "Developer", "Engineer", "Manager", etc.)
            # Title usually comes AFTER company but BEFORE dates
            title = None
            title_patterns = [
                r'\b(Senior|Junior|Lead|Principal|Staff|Associate|Full\s+Stack|Backend|Frontend|DevOps|Data|ML|AI|Cloud|Systems|Product|Project|Business|Technical|QA|Test|MERN)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*(?:Developer|Engineer|Manager|Designer|Analyst|Specialist|Architect|Consultant|Director)?',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Developer|Engineer|Manager|Designer|Analyst|Specialist|Architect|Consultant|Director))',
                r'\b(MERN|Full\s+Stack|Backend|Frontend|DevOps)\s+Developer\b'
            ]
            
            for i, line in enumerate(lines):
                # Skip date and company lines
                if (date_line_index is not None and i == date_line_index) or line == company:
                    continue
                
                for pattern in title_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        title = match.group(0).strip()
                        break
                if title:
                    break
            
            # If title not found, check if first non-date, non-company line might be title
            if not title:
                for i, line in enumerate(lines):
                    if (date_line_index is not None and i == date_line_index) or line == company:
                        continue
                    # If line is short and contains job-related keywords, it might be title
                    if len(line) < 60 and re.search(r'\b(Developer|Engineer|Manager|Designer|Analyst|Specialist|Lead|Senior|Junior|Stack)\b', line, re.IGNORECASE):
                        title = line
                        break
            
            # CRITICAL: Only add if we have BOTH company AND title (or at least company with dates)
            # This prevents adding education entries as experience
            if company and (title or start_date):
                # STRICT Final check: ensure company is not an educational institution
                company_upper = company.upper()
                is_education = (
                    re.search(r'\b(UNIVERSITY|COLLEGE|INSTITUTE|SCHOOL|ACADEMY)\b', company_upper) or
                    # Also check if company name contains common university names
                    any(uni in company_upper for uni in ["PUNE UNIVERSITY", "MUMBAI UNIVERSITY", "DELHI UNIVERSITY", 
                                                         "BANGALORE UNIVERSITY", "CHENNAI UNIVERSITY", "HYDERABAD UNIVERSITY",
                                                         "KOLKATA UNIVERSITY", "CALCUTTA UNIVERSITY"])
                )
                
                # Also check description for education keywords
                entry_text_lower = entry.lower()
                has_education_keywords = any(keyword in entry_text_lower for keyword in [
                    "academic coursework", "academic course work", "bachelor", "master", "mca", "bsc", "msc",
                    "degree", "diploma", "graduation", "student"
                ])
                
                if not is_education and not has_education_keywords:
                    # Get description (all remaining lines)
                    description_lines = []
                    for i, line in enumerate(lines):
                        if (date_line_index is not None and i == date_line_index) or line == company or line == title:
                            continue
                        description_lines.append(line)
                    description = "\n".join(description_lines).strip() if description_lines else None
                    
                    experience.append({
                        "title": title or "Unknown",
                        "company": company,
                        "start_date": start_date,
                        "end_date": end_date,
                        "description": description,
                        "location": None,
                        "technologies": [],
                        "metrics": []
                    })
                else:
                    logger.info("filtered_education_entry_from_experience", company=company, reason="education_institution" if is_education else "education_keywords")
        
        return experience
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education entries from text"""
        education = []
        
        # Split by double newlines or bullet points
        entries = re.split(r'\n\s*\n|\n\s*[-•]\s*', text)
        
        for entry in entries:
            entry = entry.strip()
            if not entry or len(entry) < 5:
                continue
            
            # Extract degree (usually first line or contains "Bachelor", "Master", "PhD", etc.)
            degree = None
            degree_patterns = [
                r'(Bachelor|B\.?S\.?|B\.?A\.?|B\.?E\.?|B\.?Tech)',
                r'(Master|M\.?S\.?|M\.?A\.?|M\.?E\.?|M\.?Tech|MBA)',
                r'(PhD|Ph\.?D\.?|Doctorate|D\.?Phil)',
                r'(Diploma|Certificate)'
            ]
            
            for pattern in degree_patterns:
                match = re.search(pattern, entry, re.IGNORECASE)
                if match:
                    # Get full degree line
                    lines = entry.split('\n')
                    for line in lines:
                        if re.search(pattern, line, re.IGNORECASE):
                            degree = line.strip()
                            break
                    break
            
            # Extract institution (usually contains "University", "College", "Institute", etc.)
            institution = None
            inst_patterns = [
                r'([A-Z][A-Za-z\s]+(?:University|College|Institute|School|Academy))',
            ]
            
            for pattern in inst_patterns:
                match = re.search(pattern, entry)
                if match:
                    institution = match.group(1).strip()
                    break
            
            # Extract year
            year = None
            year_match = re.search(r'\b(19|20)\d{2}\b', entry)
            if year_match:
                year = year_match.group(0)
            
            # Extract field of study (usually after degree, before institution)
            field = None
            if degree and institution:
                # Text between degree and institution
                parts = entry.split(degree)
                if len(parts) > 1:
                    middle = parts[1].split(institution)[0] if institution in parts[1] else ""
                    field = middle.strip(' ,-–—')
            
            if degree or institution:
                education.append({
                    "degree": degree or "Unknown",
                    "institution": institution or "Unknown",
                    "field": field,
                    "year": year,
                    "gpa": None,
                    "location": None
                })
        
        return education
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text with categorization support"""
        skills = []
        
        # Remove section headers
        text = re.sub(r'^(?:SKILLS?|TECHNICAL\s+SKILLS?|COMPETENCIES?)\s*:?\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Skill category mappings
        category_keywords = {
            "frontend": ["frontend", "react", "angular", "vue", "next.js", "typescript", "tailwind", "javascript", "html", "css"],
            "backend": ["backend", "django", "fastapi", "node.js", "flask", "nestjs", "laravel", "express", "spring"],
            "database": ["database", "postgresql", "mongodb", "mysql", "redis", "sql", "nosql"],
            "devops": ["devops", "docker", "kubernetes", "git", "jira", "bitbucket", "ci/cd", "aws", "azure", "gcp"],
            "tools": ["tools", "git", "jira", "bitbucket", "rest", "api", "microservices"],
            "frameworks": ["framework", "react", "angular", "vue", "django", "flask", "express", "nestjs"]
        }
        
        # Check if text has categorized structure (e.g., "Frontend: React, Angular")
        lines = text.split('\n')
        categorized = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line has category format: "Category: skill1, skill2" or "Category/Suffix: skill1, skill2"
            # Handles: "Frontend:", "Backend:", "DevOps/Tools:", "Database:", etc.
            # Also handles: "Front end:", "Back end:", "Dev Ops / Tools:", etc.
            # Pattern: Category name (with spaces, optional / suffix) followed by colon and skills
            category_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s*/\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)?)\s*:?\s*(.+)$', line)
            if category_match:
                category_name = category_match.group(1).lower()
                skills_text = category_match.group(2).strip()
                
                # CRITICAL: Extract individual skills from the skills text (comma/semicolon separated)
                category_skills = self._extract_skills_from_text(skills_text)
                
                # Only add if we got actual individual skills (not the whole string)
                if category_skills and len(category_skills) > 0:
                    # Filter out the category name itself if it got extracted
                    category_skills = [s for s in category_skills if s.lower() != category_name.lower()]
                    skills.extend(category_skills)
                    categorized = True
                    logger.info("extracted_skills_from_category", category=category_name, count=len(category_skills))
                else:
                    # Fallback: if extraction failed, try splitting by comma directly
                    if ',' in skills_text:
                        category_skills = [s.strip() for s in skills_text.split(',') if s.strip()]
                        skills.extend(category_skills)
                        categorized = True
            else:
                # Regular line without category - but check if it's a skill list
                # If line contains multiple skills separated by commas, extract them
                if ',' in line or ';' in line:
                    line_skills = self._extract_skills_from_text(line)
                    skills.extend(line_skills)
                else:
                    # Single skill or description line
                    line_skills = self._extract_skills_from_text(line)
                    skills.extend(line_skills)
        
        # If no categorization found, extract all skills from text
        if not categorized:
            skills = self._extract_skills_from_text(text)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            skill_lower = skill.lower().strip()
            # Filter invalid skills
            if (skill_lower and 
                2 <= len(skill) <= 50 and 
                skill_lower not in ['and', 'or', 'the', 'a', 'an', 'coordination', 'tai'] and
                skill_lower not in seen):
                seen.add(skill_lower)
                unique_skills.append(skill.strip())
        
        return unique_skills
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract individual skills from a text string - IMPROVED"""
        skills = []
        
        # First, try splitting by comma (most common separator)
        if ',' in text:
            parts = text.split(',')
        # Then try semicolon
        elif ';' in text:
            parts = text.split(';')
        # Then try "and"
        elif ' and ' in text.lower():
            parts = re.split(r'\s+and\s+', text, flags=re.IGNORECASE)
        # Then try bullet points
        elif re.search(r'[-•]', text):
            parts = re.split(r'\s*[-•]\s*', text)
        # Otherwise, split by newlines
        else:
            parts = text.split('\n')
        
        for part in parts:
            skill = part.strip()
            # Clean up skill name (remove extra spaces, colons, leading/trailing punctuation)
            skill = re.sub(r'^[:\-•]\s*', '', skill).strip()
            skill = re.sub(r'\s+', ' ', skill)  # Normalize whitespace
            
            # Validate skill (should be reasonable length and not just punctuation)
            if skill and 2 <= len(skill) <= 50 and not re.match(r'^[:\-•\s,;]+$', skill):
                # Preserve dots in skill names (e.g., "React.js", "Next.js", "Node.js")
                skills.append(skill)
        
        return skills
    
    def _extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """Extract projects from text - IMPROVED"""
        projects = []
        
        # Filter out summary/profile sections
        if re.search(r'\b(profile|summary|objective|about|overview|versatile|senior|developer|experience|years)\b', text, re.IGNORECASE):
            # This is likely a summary, not a project
            return []
        
        # Split by double newlines or bullet points
        entries = re.split(r'\n\s*\n|\n\s*[-•]\s*', text)
        
        for entry in entries:
            entry = entry.strip()
            if not entry or len(entry) < 10:
                continue
            
            # Skip if it looks like a summary/profile
            if re.search(r'\b(versatile|senior|developer|experience|years|proven|leader|projects)\b', entry, re.IGNORECASE):
                if len(entry) > 100:  # Long text is likely summary
                    continue
            
            lines = entry.split('\n')
            name = lines[0].strip() if lines else None
            
            # Project name should be short and specific (not a long sentence)
            if not name or len(name) > 60 or name.lower() in ["profile summary", "summary", "objective", "about"]:
                continue
            
            # Rest is description
            description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else None
            
            # Extract technologies (common tech keywords)
            tech_keywords = [
                'Python', 'Java', 'JavaScript', 'React', 'Node', 'Django', 'Flask',
                'AWS', 'Docker', 'Kubernetes', 'MongoDB', 'PostgreSQL', 'MySQL',
                'TensorFlow', 'PyTorch', 'Machine Learning', 'AI', 'Deep Learning',
                'Angular', 'Vue', 'Next.js', 'TypeScript', 'FastAPI', 'NestJS'
            ]
            technologies = []
            for keyword in tech_keywords:
                if keyword.lower() in entry.lower():
                    technologies.append(keyword)
            
            if name:
                projects.append({
                    "name": name,
                    "description": description,
                    "technologies": technologies if technologies else [],
                    "url": None
                })
        
        return projects
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from text"""
        certifications = []
        
        # Split by comma, newline, or bullet
        entries = re.split(r'[,\n]|\s*[-•]\s*', text)
        
        for entry in entries:
            cert = entry.strip()
            if cert and len(cert) >= 5 and len(cert) <= 100:
                certifications.append(cert)
        
        return certifications

