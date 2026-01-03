"""
LayoutLMv3 processor for vision + layout-aware document understanding
Uses microsoft/layoutlmv3-large for pixel-level + layout-aware understanding
"""
from typing import List, Dict, Any, Optional
from PIL import Image
import structlog
import torch
from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
import numpy as np

logger = structlog.get_logger()

# Global model instances (lazy loaded)
_processor = None
_model = None
_device = None


def _load_layoutlmv3(device: Optional[str] = None):
    """Lazy load LayoutLMv3 model and processor with crash protection"""
    global _processor, _model, _device
    
    # VISION-FIRST: LayoutLMv3 is mandatory for production-grade parsing
    # No environment variable to skip it - this is the core architecture
    
    if _processor is None or _model is None:
        try:
            from app.core.config import settings
            import os
            import signal
            
            # Check memory before loading (prevent OOM crashes)
            # IMPORTANT: Skip memory check in forked processes - will check during model loading
            # Memory check causes CUDA fork issues, so we'll handle OOM during actual model loading
            device = None  # Will be auto-detected based on CUDA availability
            
            # Determine device - Prefer CPU for stability if memory is low
            # IMPORTANT: Wrap CUDA checks in try-except for fork compatibility
            if device is None:
                # Check if we should force CPU for stability
                force_cpu = os.getenv("FORCE_CPU_LAYOUTLM", "false").lower() == "true"
                if force_cpu:
                    _device = "cpu"
                    logger.info("force_cpu_enabled_using_cpu")
                else:
                    # Safe CUDA check for fork compatibility
                    try:
                        cuda_available = torch.cuda.is_available()
                    except RuntimeError as e:
                        logger.warning("cuda_check_failed_in_fork", error=str(e))
                        cuda_available = False
                    
                    if cuda_available:
                        _device = "cuda"
                        logger.info("gpu_available_using_cuda")
                    else:
                        _device = "cpu"
                        logger.warning("gpu_not_available_using_cpu")
            else:
                _device = device
                if _device == "cuda":
                    try:
                        if not torch.cuda.is_available():
                            logger.warning("cuda_requested_but_not_available_falling_back_to_cpu")
                            _device = "cpu"
                    except RuntimeError as e:
                        logger.warning("cuda_check_failed_in_fork", error=str(e))
                        _device = "cpu"
            
            logger.info("loading_layoutlmv3", device=_device)
            
            # MANDATORY: Use layoutlmv3-large for vision-first architecture
            # RTX 4060 (8GB) can handle large model with float16 + proper memory management
            model_name = "microsoft/layoutlmv3-large"
            
            if _device == "cuda":
                # Skip GPU info check - will be handled during model loading
                # CUDA info queries can fail even with solo pool, so we'll try loading and handle OOM if needed
                logger.info("using_cuda_for_layoutlmv3_large")
                # Will try large model first, fallback to CPU/base if OOM occurs
            else:
                # CPU: Use base model for performance
                model_name = "microsoft/layoutlmv3-base"
                logger.info("using_base_model_cpu_mode")
            
            # Set memory-efficient loading
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            
            # Load processor with error handling
            # Note: LayoutLMv3Processor may require PyTesseract for OCR, but we can use it without OCR
            try:
                # Set environment variable to skip OCR if PyTesseract not available
                import os
                # LayoutLMv3Processor can work without OCR if text is provided
                _processor = LayoutLMv3Processor.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    local_files_only=False
                )
            except Exception as e:
                logger.error("processor_loading_failed", error=str(e), exc_info=True)
                # Try to continue without processor (will use fallback)
                _processor = None
                if _model is None:
                    return None, None, "cpu"
            
            # Load model with production-optimized settings
            try:
                # For GPU: Use float16 for memory efficiency (RTX 4060 compatible)
                # For CPU: Use float32 for stability
                # Try safetensors first to avoid PyTorch 2.6+ requirement
                model_kwargs = {
                    "trust_remote_code": True,
                    "low_cpu_mem_usage": True,
                    "torch_dtype": torch.float16 if _device == "cuda" else torch.float32,
                }
                
                # Note: device_map='auto' is not supported for LayoutLMv3ForTokenClassification
                # We'll manually move the model to device after loading
                
                # PRIORITY: Try LayoutLMv3-large with safetensors first (BEST QUALITY)
                # Only fall back to base if absolutely necessary
                try:
                    model_kwargs["use_safetensors"] = True
                    _model = LayoutLMv3ForTokenClassification.from_pretrained(
                        model_name,
                        **model_kwargs
                    )
                    logger.info("layoutlmv3_large_loaded_with_safetensors", 
                               model=model_name, device=_device)
                except (ValueError, OSError, Exception) as safetensors_error:
                    error_msg = str(safetensors_error)
                    # Try large model WITHOUT safetensors (requires PyTorch 2.6+)
                    # This maintains quality - only fall back if this also fails
                    logger.warning("safetensors_failed_trying_large_without_safetensors", 
                                 error=error_msg[:200], model=model_name)
                    try:
                        model_kwargs.pop("use_safetensors", None)
                        _model = LayoutLMv3ForTokenClassification.from_pretrained(
                            model_name,
                            **model_kwargs
                        )
                        logger.info("layoutlmv3_large_loaded_without_safetensors", 
                                   model=model_name, device=_device)
                    except Exception as large_error:
                        # LAST RESORT: Only use base model if large completely fails
                        # This should rarely happen with PyTorch 2.3+
                        logger.error("layoutlmv3_large_failed_using_base_as_fallback", 
                                    error=str(large_error)[:200],
                                    error_type=type(large_error).__name__,
                                    exc_info=True)
                        
                        # Try base model as fallback
                        try:
                            base_model_name = "microsoft/layoutlmv3-base"
                            logger.info("attempting_base_model_fallback", model=base_model_name)
                            model_kwargs_base = {
                                "trust_remote_code": True,
                                "low_cpu_mem_usage": True,
                                "torch_dtype": torch.float32,  # Base model uses float32
                                "use_safetensors": True
                            }
                            _model = LayoutLMv3ForTokenClassification.from_pretrained(
                                base_model_name,
                                **model_kwargs_base
                            )
                            logger.info("layoutlmv3_base_loaded_as_fallback", model=base_model_name)
                        except Exception as base_error:
                            logger.error("layoutlmv3_base_also_failed", 
                                       error=str(base_error)[:200],
                                       error_type=type(base_error).__name__,
                                       exc_info=True)
                            # Try base without safetensors as final fallback
                            try:
                                model_kwargs_base.pop("use_safetensors", None)
                                _model = LayoutLMv3ForTokenClassification.from_pretrained(
                                    base_model_name,
                                    **model_kwargs_base
                                )
                                logger.warning("base_model_loaded_without_safetensors_fallback", 
                                             model=base_model_name)
                            except Exception as final_error:
                                logger.error("layoutlmv3_all_attempts_failed", 
                                           error=str(final_error)[:200],
                                           error_type=type(final_error).__name__)
                                _model = None
                
                # Move to device with error handling
                try:
                    _model.to(_device)
                    _model.eval()
                    logger.info("layoutlmv3_model_moved_to_device", device=_device)
                except RuntimeError as e:
                    if "out of memory" in str(e).lower():
                        logger.error("gpu_oom_falling_back_to_cpu", error=str(e))
                        _device = "cpu"
                        # Reload model for CPU with base model
                        model_name = "microsoft/layoutlmv3-base"
                        logger.info("reloading_with_base_model_for_cpu")
                        _model = LayoutLMv3ForTokenClassification.from_pretrained(
                            model_name,
                            trust_remote_code=True,
                            low_cpu_mem_usage=True,
                            torch_dtype=torch.float32,
                            use_safetensors=True  # Avoid torch.load vulnerability
                        )
                        _model.to(_device)
                        _model.eval()
                    else:
                        raise
                
                # Safe GPU name logging (may fail in forked processes)
                gpu_name = "N/A"
                if _device == "cuda":
                    try:
                        gpu_name = torch.cuda.get_device_name(0)
                    except RuntimeError:
                        gpu_name = "CUDA (fork-safe)"
                    except Exception:
                        gpu_name = "CUDA (unknown)"
                
                logger.info("layoutlmv3_loaded", device=_device, model=model_name, gpu_name=gpu_name)
                        
            except Exception as e:
                logger.error("model_loading_failed", error=str(e), exc_info=True)
                _processor = None
                _model = None
                return None, None, "cpu"
            
        except ImportError as e:
            logger.error("layoutlmv3_import_failed", error=str(e))
            _processor = None
            _model = None
        except Exception as e:
            logger.error("layoutlmv3_loading_failed", error=str(e), exc_info=True)
            _processor = None
            _model = None
    
    return _processor, _model, _device


class LayoutLMProcessor:
    """
    Process documents using LayoutLMv3 for vision + layout understanding
    """
    
    def __init__(self, device: Optional[str] = None):
        """
        Initialize LayoutLM processor
        
        Args:
            device: Device to use ('cuda' or 'cpu')
        """
        self.device = device
        self.processor, self.model, self.device = _load_layoutlmv3(device)
        self.is_available = self.processor is not None and self.model is not None
        
        # CRITICAL: Log initialization status
        if not self.is_available:
            logger.error("layoutlmv3_initialization_failed",
                        processor_loaded=self.processor is not None,
                        model_loaded=self.model is not None,
                        device=self.device,
                        message="LayoutLMv3 is MANDATORY for vision-first architecture. Check model download and loading logs.")
        else:
            logger.info("layoutlmv3_initialization_successful",
                       device=self.device,
                       processor_type=type(self.processor).__name__ if self.processor else None,
                       model_type=type(self.model).__name__ if self.model else None)
    
    def process_page(self, image: Image.Image, text: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single page image with LayoutLMv3 with crash protection
        
        Args:
            image: PIL Image of the page
            text: Optional pre-extracted text (if available)
            
        Returns:
            Dict with:
            - tokens: List of tokens with positions
            - bboxes: Bounding boxes for each token
            - layout_structure: Detected layout elements (tables, headers, etc.)
            - text_blocks: Grouped text blocks by section
        """
        if not self.is_available:
            logger.warning("layoutlmv3_not_available")
            return self._fallback_extraction(image, text)
        
        try:
            # If text not provided, extract using OCR or basic extraction
            if text is None:
                text = ""
            
            # Resize image if too large (prevent memory issues)
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info("image_resized_for_processing", original_size=image.size, new_size=new_size)
            
            # Process with LayoutLMv3 with error handling
            # Note: LayoutLMv3Processor may require PyTesseract for OCR, but can work with provided text
            try:
                encoding = self.processor(
                    image,
                    text if text else "",  # Provide text to avoid OCR requirement
                    return_tensors="pt",
                    padding="max_length",
                    truncation=True,
                    max_length=512
                )
            except Exception as e:
                error_msg = str(e)
                if "PyTesseract" in error_msg or "tesseract" in error_msg.lower():
                    logger.warning("pytesseract_not_available_using_text_only", 
                                 hint="Install tesseract-ocr and pytesseract for OCR support")
                    # Try with empty text (processor might still work)
                    try:
                        encoding = self.processor(
                            image,
                            "",  # Empty text
                            return_tensors="pt",
                            padding="max_length",
                            truncation=True,
                            max_length=512
                        )
                    except Exception:
                        logger.error("processor_encoding_failed_even_with_empty_text", error=error_msg)
                        return self._fallback_extraction(image, text)
                else:
                    logger.error("processor_encoding_failed", error=error_msg)
                    return self._fallback_extraction(image, text)
            
            # Move to device and match model dtype (float16 for GPU, float32 for CPU)
            try:
                # Get model dtype to match inputs
                model_dtype = next(self.model.parameters()).dtype
                
                # Move to device and convert floating point tensors to model dtype
                # First get encoding from processor (already done above)
                # Now convert to match model dtype
                converted_encoding = {}
                for k, v in encoding.items():
                    if v.dtype.is_floating_point:
                        converted_encoding[k] = v.to(self.device).to(model_dtype)
                    else:
                        converted_encoding[k] = v.to(self.device)
                encoding = converted_encoding
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    logger.error("gpu_oom_during_encoding_falling_back")
                    # Try CPU
                    try:
                        self.device = "cpu"
                        model_dtype = torch.float32  # CPU uses float32
                        converted_encoding = {}
                        for k, v in encoding.items():
                            if v.dtype.is_floating_point:
                                converted_encoding[k] = v.to(self.device).to(model_dtype)
                            else:
                                converted_encoding[k] = v.to(self.device)
                        encoding = converted_encoding
                    except Exception:
                        return self._fallback_extraction(image, text)
                else:
                    raise
            
            # Run inference with error handling
            try:
                with torch.no_grad():
                    outputs = self.model(**encoding)
            except RuntimeError as e:
                if "out of memory" in str(e).lower() or "SIGSEGV" in str(e):
                    logger.error("inference_oom_or_crash_falling_back", error=str(e))
                    return self._fallback_extraction(image, text)
                else:
                    raise
            
            # Extract predictions safely
            try:
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_labels = torch.argmax(predictions, dim=-1)
                
                # Get tokens and bounding boxes
                tokens = self.processor.tokenizer.convert_ids_to_tokens(
                    encoding["input_ids"][0].cpu().numpy()
                )
                bboxes = encoding["bbox"][0].cpu().numpy()
            except Exception as e:
                logger.error("prediction_extraction_failed", error=str(e))
                return self._fallback_extraction(image, text)
            
            # Extract layout structure
            layout_structure = self._extract_layout_structure(
                tokens, bboxes, predicted_labels, image.size
            )
            
            # Group text blocks by section
            text_blocks = self._group_text_blocks(tokens, bboxes, layout_structure)
            
            logger.info("layoutlmv3_processing_complete",
                       tokens_count=len(tokens),
                       blocks_count=len(text_blocks))
            
            return {
                "tokens": tokens,
                "bboxes": bboxes,
                "layout_structure": layout_structure,
                "text_blocks": text_blocks,
                "raw_text": " ".join(tokens)
            }
            
        except Exception as e:
            logger.error("layoutlmv3_processing_failed", error=str(e), exc_info=True)
            return self._fallback_extraction(image, text)
    
    def _extract_layout_structure(
        self, 
        tokens: List[str], 
        bboxes: np.ndarray,
        labels: torch.Tensor,
        image_size: tuple
    ) -> Dict[str, Any]:
        """Extract layout structure from model predictions"""
        structure = {
            "headers": [],
            "tables": [],
            "lists": [],
            "paragraphs": []
        }
        
        # Group tokens by position to detect structure
        # This is a simplified version - full implementation would use
        # LayoutLMv3's layout understanding capabilities
        
        return structure
    
    def _group_text_blocks(
        self,
        tokens: List[str],
        bboxes: np.ndarray,
        layout_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Group tokens into text blocks by spatial proximity and layout"""
        blocks = []
        
        # Simple grouping by vertical position
        # Full implementation would use clustering or layout analysis
        current_block = []
        current_y = None
        
        for i, (token, bbox) in enumerate(zip(tokens, bboxes)):
            if token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
            
            y_center = (bbox[1] + bbox[3]) / 2
            
            if current_y is None or abs(y_center - current_y) < 20:
                current_block.append({
                    "token": token,
                    "bbox": bbox.tolist()
                })
                current_y = y_center
            else:
                if current_block:
                    blocks.append({
                        "tokens": current_block,
                        "y_position": current_y
                    })
                current_block = [{
                    "token": token,
                    "bbox": bbox.tolist()
                }]
                current_y = y_center
        
        if current_block:
            blocks.append({
                "tokens": current_block,
                "y_position": current_y
            })
        
        return blocks
    
    def _fallback_extraction(self, image: Image.Image, text: Optional[str]) -> Dict[str, Any]:
        """Fallback when LayoutLMv3 is not available"""
        logger.warning("using_fallback_extraction")
        return {
            "tokens": [],
            "bboxes": [],
            "layout_structure": {},
            "text_blocks": [],
            "raw_text": text or ""
        }

