"""
Main OCR engine with preprocessing and multiple fallback strategies.
Handles: poor quality images, stamps, rotated text, mixed fonts.
"""

import numpy as np
from typing import List, Tuple
import logging

from .ocr_models import OCRExtractionResult
from .ocr_engines import TesseractEngine, EasyOCREngine
from .text_preprocessor import TextImagePreprocessor


class OCRTextExtractor:
    """
    Main OCR text extraction engine.

    Combines multiple OCR engines and preprocessing strategies to
    maximize text extraction success from engineering seals.
    """

    def __init__(self, use_easyocr_fallback: bool = True):
        """
        Initialize OCR extractor.

        Args:
            use_easyocr_fallback: Whether to use EasyOCR as fallback (default: True)
        """
        self.tesseract_engine = TesseractEngine()
        self.easyocr_engine = EasyOCREngine() if use_easyocr_fallback else None
        self.preprocessor = TextImagePreprocessor()
        self.logger = logging.getLogger(__name__)

    def extract_text_from_region(self, region_image: np.ndarray) -> OCRExtractionResult:
        """
        Extract text from a region image with multiple strategies.

        Strategy:
        1. Preprocess image for optimal OCR (multiple versions)
        2. Try Tesseract with multiple preprocessing approaches
        3. Fall back to EasyOCR if Tesseract fails
        4. Return text with confidence and metadata

        Args:
            region_image: Image region to extract text from

        Returns:
            OCRExtractionResult with extracted text and metadata
        """
        # Step 1: Preprocess the image (multiple strategies)
        processed_images = self.preprocessor.prepare_for_ocr(region_image)

        results = []

        # Step 2: Try Tesseract with different preprocessing
        for img_name, processed_img in processed_images.items():
            tesseract_result = self.tesseract_engine.extract(processed_img)
            if tesseract_result.text.strip():
                # Add preprocessing info
                tesseract_result.preprocessing_steps = [img_name]
                results.append((f"tesseract_{img_name}", tesseract_result))

        # Step 3: Try EasyOCR as fallback if Tesseract didn't find much
        if self.easyocr_engine and (not results or all(len(r[1].text.strip()) < 5 for r in results)):
            self.logger.debug("Falling back to EasyOCR")
            easyocr_result = self.easyocr_engine.extract(region_image)
            if easyocr_result.text.strip():
                easyocr_result.preprocessing_steps = ["original"]
                results.append(("easyocr", easyocr_result))

        # Step 4: Select best result
        if not results:
            return OCRExtractionResult(
                text="",
                confidence=0.0,
                engine_used="none",
                preprocessing_steps=[],
                raw_image=region_image
            )

        # Choose result with highest score (confidence + keyword matching)
        best_result = self._select_best_result(results)

        return best_result

    def _select_best_result(
        self,
        results: List[Tuple[str, OCRExtractionResult]]
    ) -> OCRExtractionResult:
        """
        Select the best OCR result based on confidence and content.

        Engineering-specific keywords increase result score.

        Args:
            results: List of (engine_name, result) tuples

        Returns:
            Best OCRExtractionResult
        """
        # Keywords commonly found in engineering seals
        engineering_keywords = [
            'engineer', 'eng', 'p.eng', 'peng', 'professional',
            'apega', 'apegs', 'egbc', 'manitoba',
            'license', 'licence', 'registration', 'reg',
            'alberta', 'saskatchewan', 'british columbia', 'bc',
            'association', 'geoscientist'
        ]

        scored_results = []
        for engine_name, result in results:
            # Base score from OCR confidence
            score = result.confidence

            # Bonus for engineering keywords
            text_lower = result.text.lower()
            keyword_count = sum(1 for keyword in engineering_keywords if keyword in text_lower)
            keyword_bonus = keyword_count * 0.1  # 10% per keyword
            score += keyword_bonus

            # Bonus for reasonable text length (not too short, not too long)
            text_len = len(result.text.strip())
            if 10 <= text_len <= 500:
                score += 0.05
            elif text_len > 500:
                score -= 0.05  # Penalize extremely long extractions

            # Bonus for specific patterns (P.Eng, license numbers, etc.)
            if 'p.eng' in text_lower or 'peng' in text_lower:
                score += 0.15
            if any(c.isdigit() for c in result.text):  # Contains numbers (license #)
                score += 0.05

            scored_results.append((score, engine_name, result))

        # Return highest scored result
        scored_results.sort(reverse=True, key=lambda x: x[0])
        best_result = scored_results[0][2]
        best_result.engine_used = scored_results[0][1]  # Update engine name

        self.logger.debug(
            f"Selected result from {best_result.engine_used} "
            f"with score {scored_results[0][0]:.2f}"
        )

        return best_result
