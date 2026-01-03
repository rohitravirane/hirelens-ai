"""
PDF to Image conversion for vision-based parsing
Handles both text-based and scanned PDFs
"""
import io
from pathlib import Path
from typing import List, Optional
import structlog
from PIL import Image
import pdf2image

logger = structlog.get_logger()


class PDFToImageConverter:
    """Convert PDF pages to images for vision-based processing"""
    
    def __init__(self, dpi: int = 200):
        """
        Initialize PDF to image converter
        
        Args:
            dpi: Resolution for image conversion (higher = better quality, slower)
        """
        self.dpi = dpi
    
    def convert(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF to list of PIL Images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PIL Image objects, one per page
        """
        try:
            # Use pdf2image (requires poppler)
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=self.dpi,
                fmt='RGB'
            )
            logger.info("pdf_converted_to_images", 
                       pdf_path=pdf_path, 
                       pages=len(images),
                       dpi=self.dpi)
            return images
        except Exception as e:
            logger.error("pdf_to_image_conversion_failed", 
                        pdf_path=pdf_path, 
                        error=str(e))
            raise
    
    def convert_bytes(self, pdf_bytes: bytes) -> List[Image.Image]:
        """
        Convert PDF bytes to list of PIL Images
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            List of PIL Image objects, one per page
        """
        try:
            images = pdf2image.convert_from_bytes(
                pdf_bytes,
                dpi=self.dpi,
                fmt='RGB'
            )
            logger.info("pdf_bytes_converted_to_images", 
                       pages=len(images),
                       dpi=self.dpi)
            return images
        except Exception as e:
            logger.error("pdf_bytes_to_image_conversion_failed", 
                        error=str(e))
            raise


