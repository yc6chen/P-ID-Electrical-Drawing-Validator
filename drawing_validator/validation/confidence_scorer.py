"""
Calculate confidence scores for validation results.
"""

import cv2
import numpy as np
from typing import Dict, List, Any, Optional
import re


class ConfidenceScorer:
    """
    Calculate confidence scores for validation results.

    Confidence is based on multiple factors including text clarity,
    association matches, license number format, and image quality.
    """

    def calculate_validation_confidence(
        self,
        peng_check: Dict[str, Any],
        association_matches: Dict[str, Dict[str, Any]],
        license_numbers: List[str],
        raw_text: str,
        region_image: Optional[np.ndarray] = None
    ) -> float:
        """
        Calculate overall validation confidence (0.0 to 1.0).

        Factors:
        1. P.Eng designation clarity and format (30% weight)
        2. Association pattern matches (40% weight)
        3. License number presence and format (20% weight)
        4. Image quality (10% weight, if provided)

        Args:
            peng_check: Dictionary with P.Eng designation check results
            association_matches: Dictionary of association match details
            license_numbers: List of extracted license numbers
            raw_text: Raw OCR text
            region_image: Optional image for quality assessment

        Returns:
            Confidence score from 0.0 to 1.0
        """
        confidence = 0.0

        # Factor 1: P.Eng designation (30% weight)
        if peng_check.get('found', False):
            confidence += 0.3

            # Bonus for specific, clear formats
            designation = peng_check.get('designation', '')
            if 'PROFESSIONAL ENGINEER' in designation:
                confidence += 0.1
            elif 'P.ENG' in designation or 'P.ENG.' in designation:
                confidence += 0.05
            elif 'PENG' in designation:
                confidence += 0.03

        # Factor 2: Association matches (40% weight)
        assoc_count = len(association_matches)
        if assoc_count == 1:
            confidence += 0.3
        elif assoc_count >= 2:
            # Multiple associations increase confidence
            confidence += 0.4

        # Check match quality for each association
        for assoc_name, match_info in association_matches.items():
            if match_info.get('exact_match', False):
                confidence += 0.05
            if match_info.get('license_found', False):
                confidence += 0.05

        # Factor 3: License numbers (20% weight)
        if license_numbers:
            confidence += 0.15

            # Validate license format
            valid_licenses = []
            for license_num in license_numbers:
                # Canadian P.Eng license format: Letter followed by 5-6 digits
                if re.match(r'^[A-Z]\d{5,6}$', license_num):
                    valid_licenses.append(license_num)

            if valid_licenses:
                confidence += 0.05  # Bonus for valid format

        # Factor 4: Image quality (10% weight, if image provided)
        if region_image is not None:
            image_quality = self._assess_image_quality(region_image)
            confidence += image_quality * 0.1

        # Additional bonus for text characteristics
        text_quality_bonus = self._assess_text_quality(raw_text)
        confidence += text_quality_bonus

        # Cap at 1.0
        return min(confidence, 1.0)

    def _assess_image_quality(self, image: np.ndarray) -> float:
        """
        Assess image quality for OCR (0.0 to 1.0).

        Measures contrast and sharpness as indicators of quality.

        Args:
            image: Input image as numpy array

        Returns:
            Quality score from 0.0 to 1.0
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Calculate contrast (standard deviation of pixel values)
            contrast = np.std(gray)

            # Calculate sharpness (Laplacian variance)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = laplacian.var()

            # Normalize scores
            # Good contrast is typically > 50, good sharpness > 100
            contrast_score = min(contrast / 50.0, 1.0)
            sharpness_score = min(sharpness / 100.0, 1.0)

            return (contrast_score + sharpness_score) / 2.0

        except Exception:
            # If assessment fails, return neutral score
            return 0.5

    def _assess_text_quality(self, text: str) -> float:
        """
        Assess extracted text quality based on content.

        Args:
            text: Extracted text

        Returns:
            Quality bonus (0.0 to 0.1)
        """
        bonus = 0.0

        # Bonus for reasonable length
        text_len = len(text.strip())
        if 20 <= text_len <= 200:
            bonus += 0.02
        elif text_len > 200:
            # Very long text might indicate over-extraction
            bonus -= 0.01

        # Bonus for presence of multiple keywords
        text_upper = text.upper()
        keyword_count = 0

        keywords = [
            'ENGINEER', 'PROFESSIONAL', 'ASSOCIATION',
            'LICENSE', 'LICENCE', 'REGISTRATION',
            'ALBERTA', 'SASKATCHEWAN', 'BRITISH COLUMBIA', 'MANITOBA'
        ]

        for keyword in keywords:
            if keyword in text_upper:
                keyword_count += 1

        if keyword_count >= 3:
            bonus += 0.03
        elif keyword_count >= 2:
            bonus += 0.02
        elif keyword_count >= 1:
            bonus += 0.01

        # Bonus for containing numbers (likely license number)
        if re.search(r'\d{4,}', text):
            bonus += 0.01

        # Penalize excessive special characters or noise
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        if special_char_ratio > 0.3:
            bonus -= 0.02

        return max(0.0, min(bonus, 0.1))
