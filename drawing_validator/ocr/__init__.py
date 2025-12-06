"""
OCR (Optical Character Recognition) module for extracting text from detected regions.
"""

from .text_extractor import OCRTextExtractor
from .ocr_models import OCRExtractionResult

__all__ = [
    'OCRTextExtractor',
    'OCRExtractionResult',
]
