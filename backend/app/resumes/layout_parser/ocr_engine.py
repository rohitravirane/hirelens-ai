"""
OCR Engine for scanned PDFs using PaddleOCR (100% offline)
"""
from typing import List, Dict, Any, Optional
from PIL import Image
import structlog
import numpy as np

logger = structlog.get_logger()

# Lazy loading for PaddleOCR
_paddleocr = None


def _get_paddleocr():
    """Lazy load PaddleOCR to avoid import overhead"""
    global _paddleocr
    if _paddleocr is None:
        try:
            from paddleocr import PaddleOCR
            # Initialize with English language, CPU mode
            # Use_angle_cls=True for better text detection in rotated images
            _paddleocr = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                use_gpu=False,  # Set to True if GPU available
                show_log=False
            )
            logger.info("paddleocr_initialized")
        except ImportError:
            logger.warning("paddleocr_not_available", 
                         hint="Install with: pip install paddlepaddle paddleocr")
            _paddleocr = None
        except Exception as e:
            logger.error("paddleocr_initialization_failed", error=str(e))
            _paddleocr = None
    return _paddleocr


class OCREngine:
    """OCR engine using PaddleOCR for scanned PDFs"""
    
    def __init__(self):
        self.ocr = _get_paddleocr()
        self.is_available = self.ocr is not None
    
    def extract_text(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract text from image using OCR
        
        Args:
            image: PIL Image object
            
        Returns:
            Dict with 'text' (combined text) and 'boxes' (bounding boxes with text)
        """
        if not self.is_available:
            logger.warning("ocr_not_available_skipping")
            return {"text": "", "boxes": []}
        
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Run OCR
            result = self.ocr.ocr(img_array, cls=True)
            
            # Parse result
            text_parts = []
            boxes = []
            
            if result and result[0]:
                for line in result[0]:
                    if line:
                        # PaddleOCR returns: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)]
                        box_coords = line[0]  # Bounding box coordinates
                        text_info = line[1]  # (text, confidence)
                        text = text_info[0]
                        confidence = text_info[1]
                        
                        text_parts.append(text)
                        boxes.append({
                            "text": text,
                            "confidence": confidence,
                            "bbox": box_coords
                        })
            
            combined_text = "\n".join(text_parts)
            
            logger.info("ocr_extraction_complete", 
                       text_length=len(combined_text),
                       boxes_count=len(boxes))
            
            return {
                "text": combined_text,
                "boxes": boxes
            }
        except Exception as e:
            logger.error("ocr_extraction_failed", error=str(e))
            return {"text": "", "boxes": []}
    
    def is_scanned_pdf(self, image: Image.Image, text_from_pdf: str) -> bool:
        """
        Determine if PDF is scanned (image-based) vs text-based
        
        Args:
            image: First page image
            text_from_pdf: Text extracted directly from PDF
            
        Returns:
            True if likely scanned, False if text-based
        """
        # If PDF text extraction yields very little text, likely scanned
        if len(text_from_pdf.strip()) < 100:
            return True
        
        # If text extraction yields mostly whitespace or very few words, likely scanned
        words = text_from_pdf.split()
        if len(words) < 20:
            return True
        
        return False




