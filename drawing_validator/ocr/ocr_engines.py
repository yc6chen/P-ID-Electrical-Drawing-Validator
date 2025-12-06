"""
OCR engine wrappers for Tesseract and EasyOCR.
"""

import numpy as np
from typing import Optional
import logging

from .ocr_models import OCRExtractionResult


class TesseractEngine:
    """Wrapper for Tesseract OCR engine."""

    def __init__(self):
        """Initialize Tesseract engine."""
        self.logger = logging.getLogger(__name__)
        self._tesseract_available = False
        self._check_tesseract()

    def _check_tesseract(self):
        """Check if Tesseract is available."""
        try:
            import pytesseract
            # Try to get version to verify Tesseract is installed
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            self.logger.info("Tesseract OCR is available")
        except Exception as e:
            self.logger.warning(f"Tesseract OCR not available: {e}")
            self._tesseract_available = False

    def extract(self, image: np.ndarray) -> OCRExtractionResult:
        """
        Extract text using Tesseract.

        Args:
            image: Preprocessed image as numpy array

        Returns:
            OCRExtractionResult with extracted text and metadata
        """
        if not self._tesseract_available:
            return OCRExtractionResult(
                text="",
                confidence=0.0,
                engine_used="tesseract_unavailable",
                preprocessing_steps=[]
            )

        try:
            import pytesseract

            # Configure Tesseract for engineering seals
            # PSM 6: Assume a single uniform block of text
            # OEM 3: Default, based on what is available
            custom_config = r'--oem 3 --psm 6'

            # Extract text with confidence data
            data = pytesseract.image_to_data(
                image,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )

            # Combine all text
            text_parts = []
            confidences = []

            for i, text in enumerate(data['text']):
                conf = int(data['conf'][i])
                if conf > 0 and text.strip():  # Filter out low confidence
                    text_parts.append(text)
                    confidences.append(conf)

            full_text = ' '.join(text_parts)

            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            avg_confidence = avg_confidence / 100.0  # Convert to 0-1 scale

            return OCRExtractionResult(
                text=full_text,
                confidence=avg_confidence,
                engine_used="tesseract",
                preprocessing_steps=[],
                raw_image=image
            )

        except Exception as e:
            self.logger.error(f"Tesseract extraction failed: {e}")
            return OCRExtractionResult(
                text="",
                confidence=0.0,
                engine_used="tesseract_error",
                preprocessing_steps=[]
            )


class EasyOCREngine:
    """Wrapper for EasyOCR engine (fallback option)."""

    def __init__(self):
        """Initialize EasyOCR engine."""
        self.logger = logging.getLogger(__name__)
        self._reader = None
        self._easyocr_available = False
        self._initialize_reader()

    def _initialize_reader(self):
        """Initialize EasyOCR reader lazily."""
        try:
            import easyocr
            self._reader = easyocr.Reader(['en'], gpu=False)
            self._easyocr_available = True
            self.logger.info("EasyOCR is available")
        except Exception as e:
            self.logger.warning(f"EasyOCR not available: {e}")
            self._easyocr_available = False

    def extract(self, image: np.ndarray) -> OCRExtractionResult:
        """
        Extract text using EasyOCR.

        Args:
            image: Preprocessed image as numpy array

        Returns:
            OCRExtractionResult with extracted text and metadata
        """
        if not self._easyocr_available or self._reader is None:
            return OCRExtractionResult(
                text="",
                confidence=0.0,
                engine_used="easyocr_unavailable",
                preprocessing_steps=[]
            )

        try:
            # Perform OCR
            results = self._reader.readtext(image)

            # Extract text and confidence
            text_parts = []
            confidences = []

            for bbox, text, conf in results:
                if text.strip():
                    text_parts.append(text)
                    confidences.append(conf)

            full_text = ' '.join(text_parts)

            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return OCRExtractionResult(
                text=full_text,
                confidence=avg_confidence,
                engine_used="easyocr",
                preprocessing_steps=[],
                raw_image=image
            )

        except Exception as e:
            self.logger.error(f"EasyOCR extraction failed: {e}")
            return OCRExtractionResult(
                text="",
                confidence=0.0,
                engine_used="easyocr_error",
                preprocessing_steps=[]
            )
