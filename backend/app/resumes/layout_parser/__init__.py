"""
Layout-aware resume parser using Vision + Layout + Semantic understanding
Uses LayoutLMv3 for document understanding, PaddleOCR for scanned PDFs,
and local LLM for semantic normalization.
"""
from app.resumes.layout_parser.layout_parser import LayoutParser

__all__ = ["LayoutParser"]





