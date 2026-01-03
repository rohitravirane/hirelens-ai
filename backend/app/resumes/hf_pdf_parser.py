"""
Hugging Face PDF Parser - World-class resume extraction
Uses local models - no API keys required, models auto-download
"""
from typing import Dict, List, Any, Optional
import json
import re
import structlog
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

from app.core.config import settings

logger = structlog.get_logger()


class HFPDFParser:
    """Hugging Face PDF Parser for world-class resume extraction - Local models only"""
    
    def __init__(self):
        # Force GPU if available, regardless of settings
        if torch.cuda.is_available():
            self.device = "cuda"
            logger.info("using_gpu_for_pdf_parsing", device=torch.cuda.get_device_name(0))
        else:
            self.device = "cpu"
            logger.warning("gpu_not_available_using_cpu_for_pdf_parsing")
        self.text_generator = None
        self.model_name = None
        self._init_models()
    
    def _init_models(self):
        """Initialize Hugging Face models for resume parsing - Local models only"""
        try:
            # Use local models - no API keys needed
            # Models will be auto-downloaded on first use
            # Choose model based on device capability
            
            # Use model from config (allows customization)
            # Default: TinyLlama for CPU, can be changed to phi-2 or Mistral for GPU
            self.model_name = settings.HUGGINGFACE_PARSER_MODEL
            
            # Auto-select based on device if not configured
            if self.model_name == "TinyLlama/TinyLlama-1.1B-Chat-v1.0" and self.device == "cuda":
                # GPU available - suggest better model
                logger.info("gpu_available_suggest_better_model", suggested="microsoft/phi-2")
            
            logger.info("hf_pdf_parser_initialized", device=self.device, model=self.model_name, use_local=True)
        except Exception as e:
            logger.error("hf_pdf_parser_init_failed", error=str(e))
    
    def parse_resume(self, text: str) -> Dict[str, Any]:
        """
        Parse resume using local Hugging Face models
        Models are auto-downloaded on first use - no API keys needed
        """
        try:
            # Use local text generation model for structured extraction
            parsed_data = self._parse_with_local_llm(text)
            if parsed_data:
                return parsed_data
            
            # Fallback: Use rule-based parsing
            logger.warning("using_fallback_parsing")
            return self._parse_with_rules(text)
            
        except Exception as e:
            logger.error("hf_parsing_failed", error=str(e))
            return self._parse_with_rules(text)
    
    def _parse_with_local_llm(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse using local Hugging Face models
        Models are auto-downloaded on first use - no API keys needed
        """
        try:
            # Initialize text generator if not already done
            if self.text_generator is None:
                self._init_text_generator()
            
            if self.text_generator is None:
                logger.warning("text_generator_not_available")
                return None
            
            # Create structured extraction prompt
            prompt = f"""Extract structured information from this resume. Return ONLY valid JSON:

{{
  "name": "Full name",
  "email": "Email address",
  "phone": "Phone number",
  "skills": ["skill1", "skill2"],
  "experience": [{{"title": "Job title", "company": "Company", "start_date": "YYYY-MM", "end_date": "YYYY-MM or present", "description": "Description"}}],
  "education": [{{"degree": "Degree", "institution": "Institution", "year": "YYYY"}}],
  "projects": [{{"name": "Project name", "description": "Description", "technologies": ["tech1"]}}],
  "certifications": ["cert1"],
  "languages": ["lang1"]
}}

Resume text:
{text[:2000]}

Return ONLY valid JSON, no markdown."""

            # Generate structured output using model directly (production-optimized)
            if not hasattr(self, 'tokenizer') or self.tokenizer is None:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Tokenize input (truncate if too long for model context)
            max_input_length = 2048 if "mistral" in self.model_name.lower() else 1024
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=max_input_length
            ).to(self.device)
            
            # Generate with production optimizations
            with torch.no_grad():
                outputs = self.text_generator.generate(
                    **inputs,
                    max_new_tokens=1500,  # Increased for better extraction
                    temperature=0.0,  # Deterministic output
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1,  # Prevent repetition
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove prompt from output
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    logger.info("hf_local_llm_success", model=self.model_name)
                    return parsed
                except json.JSONDecodeError as e:
                    logger.warning("json_decode_error", error=str(e))
            
            return None
            
        except Exception as e:
            logger.error("local_llm_parsing_failed", error=str(e))
            return None
    
    def _init_text_generator(self):
        """
        Initialize local text generation model - production-ready with optimizations
        Auto-downloads on first use, uses quantization for memory efficiency
        """
        try:
            logger.info("loading_local_hf_model", model=self.model_name, device=self.device, use_quantization=settings.USE_QUANTIZATION)
            
            # Production optimizations: Use quantization for large models
            use_quantization = settings.USE_QUANTIZATION and ("mistral" in self.model_name.lower() or "7b" in self.model_name.lower())
            
            try:
                # Load tokenizer first - use_fast=False to avoid compatibility issues
                try:
                    tokenizer = AutoTokenizer.from_pretrained(
                        self.model_name,
                        trust_remote_code=True,
                        use_fast=False,  # Avoid PyPreTokenizerTypeWrapper errors
                    )
                except Exception as tokenizer_error:
                    # Fallback: try without use_fast parameter
                    logger.warning("tokenizer_load_failed_trying_fallback", error=str(tokenizer_error))
                    tokenizer = AutoTokenizer.from_pretrained(
                        self.model_name,
                        trust_remote_code=True,
                    )
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                # Prepare model loading kwargs with production optimizations
                model_kwargs = {
                    "trust_remote_code": True,
                    "low_cpu_mem_usage": True,
                }
                
                # Add quantization for production (reduces memory by 50-75%)
                if use_quantization and self.device == "cuda":
                    try:
                        from transformers import BitsAndBytesConfig
                        quantization_config = BitsAndBytesConfig(
                            load_in_8bit=True,
                            llm_int8_threshold=6.0,
                            llm_int8_has_fp16_weight=False,
                        )
                        model_kwargs["quantization_config"] = quantization_config
                        model_kwargs["device_map"] = "auto"
                        logger.info("using_8bit_quantization", model=self.model_name)
                    except ImportError:
                        logger.warning("bitsandbytes_not_available", fallback="no_quantization")
                elif self.device == "cuda":
                    model_kwargs["torch_dtype"] = torch.float16
                    model_kwargs["device_map"] = "auto"
                else:
                    # CPU: Use float32, no quantization
                    model_kwargs["torch_dtype"] = torch.float32
                
                # Add memory limits if configured
                if settings.model_max_memory_dict:
                    model_kwargs["max_memory"] = settings.model_max_memory_dict
                
                # Load model
                self.text_generator = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    **model_kwargs
                )
                
                # Move to CPU if not using device_map
                if self.device == "cpu" and "device_map" not in model_kwargs:
                    self.text_generator = self.text_generator.to(self.device)
                
                # Store tokenizer for later use
                self.tokenizer = tokenizer
                
                logger.info("local_hf_model_loaded_production", 
                          model=self.model_name, 
                          device=self.device,
                          quantized=use_quantization,
                          memory_efficient=True)
                
            except Exception as e:
                logger.error("model_load_failed", error=str(e), model=self.model_name)
                # Fallback to smaller model if Mistral fails
                if "mistral" in self.model_name.lower():
                    logger.warning("mistral_load_failed_trying_phi2", error=str(e))
                    try:
                        self.model_name = "microsoft/phi-2"
                        self._init_text_generator()  # Retry with phi-2
                        return
                    except Exception as e2:
                        logger.error("phi2_fallback_failed", error=str(e2))
                
                # Final fallback: TinyLlama
                try:
                    logger.warning("trying_tinyllama_fallback")
                    self.model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
                    tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                    if tokenizer.pad_token is None:
                        tokenizer.pad_token = tokenizer.eos_token
                    
                    self.text_generator = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float32,
                        low_cpu_mem_usage=True,
                    ).to(self.device)
                    
                    self.tokenizer = tokenizer
                    logger.info("fallback_model_loaded", model=self.model_name)
                except Exception as e3:
                    logger.error("all_models_failed", error=str(e3))
                    self.text_generator = None
                    
        except Exception as e:
            logger.error("text_generator_init_failed", error=str(e))
            self.text_generator = None
    
    
    def _parse_with_rules(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based parsing"""
        from app.resumes.parser import ResumeParser
        parser = ResumeParser()
        return parser.parse(text)


# Global instance
hf_pdf_parser = HFPDFParser()

