"""
Validate extracted text against Canadian engineering association requirements.
"""

import re
import numpy as np
from typing import Dict, List, Any, Optional
import logging

from .validation_models import ValidationResult
from .confidence_scorer import ConfidenceScorer


class AssociationValidator:
    """
    Validate OCR text against Canadian engineering association patterns.

    Supports: APEGA, APEGS, EGBC, Engineers Geoscientists Manitoba (EGM)
    """

    # Association-specific regex patterns
    ASSOCIATION_PATTERNS = {
        'APEGA': {
            'patterns': [
                r'APEGA',
                r'APEGGA',  # Old name
                r'Association\s+of\s+Professional\s+Engineers.*Alberta',
                r'Professional\s+Engineers.*Geoscientists.*Alberta',
                r'Alberta.*(?:Engineers|Engineering)',
            ],
            'license_patterns': [
                r'(?:APEGA|License|Lic\.?|Reg\.?)\s*(?:No\.?|Number|#)?\s*:?\s*([A-Z]\d{5,6})',
                r'\b([A-Z]\d{5,6})\b',  # Standalone license format
            ],
            'license_format': r'^[A-Z]\d{5,6}$',
            'abbreviations': ['APEGA', 'APEGGA'],
        },
        'APEGS': {
            'patterns': [
                r'APEGS',
                r'Association\s+of\s+Professional\s+Engineers.*Saskatchewan',
                r'Professional\s+Engineers.*Geoscientists.*Saskatchewan',
                r'Saskatchewan.*(?:Engineers|Engineering)',
            ],
            'license_patterns': [
                r'(?:APEGS|License|Lic\.?|Reg\.?)\s*(?:No\.?|Number|#)?\s*:?\s*([A-Z]\d{5,6})',
                r'\b([A-Z]\d{5,6})\b',
            ],
            'license_format': r'^[A-Z]\d{5,6}$',
            'abbreviations': ['APEGS', 'SK'],
        },
        'EGBC': {
            'patterns': [
                r'EGBC',
                r'Engineers.*Geoscientists.*(?:British\s+Columbia|BC)',
                r'British\s+Columbia.*(?:Engineers|Engineering)',
                r'APEGBC',  # Old name
            ],
            'license_patterns': [
                r'(?:EGBC|License|Lic\.?|Reg\.?)\s*(?:No\.?|Number|#)?\s*:?\s*([A-Z]\d{5,6})',
                r'\b([A-Z]\d{5,6})\b',
            ],
            'license_format': r'^[A-Z]\d{5,6}$',
            'abbreviations': ['EGBC', 'BC'],
        },
        'EGM': {
            'patterns': [
                r'Engineers\s+Geoscientists\s+Manitoba',
                r'EGM\b',
                r'Manitoba.*(?:Engineers|Engineering)',
                r'APEGM',  # Old name
            ],
            'license_patterns': [
                r'(?:EGM|License|Lic\.?|Reg\.?)\s*(?:No\.?|Number|#)?\s*:?\s*([A-Z]\d{5,6})',
                r'\b([A-Z]\d{5,6})\b',
            ],
            'license_format': r'^[A-Z]\d{5,6}$',
            'abbreviations': ['EGM', 'Manitoba', 'MB'],
        }
    }

    def __init__(self):
        """Initialize the validator."""
        self.confidence_scorer = ConfidenceScorer()
        self.logger = logging.getLogger(__name__)

    def validate_text(
        self,
        text: str,
        region_image: Optional[np.ndarray] = None
    ) -> ValidationResult:
        """
        Comprehensive validation of extracted text.

        Steps:
        1. Check for P.Eng designation
        2. Identify association(s)
        3. Extract license numbers
        4. Calculate confidence
        5. Determine overall validity

        Args:
            text: Extracted OCR text
            region_image: Optional image for quality assessment

        Returns:
            ValidationResult with detailed validation information
        """
        text_upper = text.upper()

        # Step 1: Check for P.Eng designation
        peng_check = self._check_peng_designation(text_upper)
        if not peng_check['found']:
            return ValidationResult(
                valid=False,
                confidence=0.0,
                reason="No valid P.Eng designation found",
                raw_text=text
            )

        # Step 2: Identify associations
        association_matches = {}
        for assoc_name, rules in self.ASSOCIATION_PATTERNS.items():
            match_info = self._check_association_patterns(text, text_upper, rules)
            if match_info['found']:
                association_matches[assoc_name] = match_info

        if not association_matches:
            return ValidationResult(
                valid=False,
                confidence=0.2,  # Has P.Eng but no association
                reason="No recognized engineering association found",
                raw_text=text,
                peng_designation=peng_check['designation']
            )

        # Step 3: Extract license numbers
        license_numbers = self._extract_license_numbers(text_upper, association_matches)

        # Step 4: Calculate confidence
        confidence = self.confidence_scorer.calculate_validation_confidence(
            peng_check=peng_check,
            association_matches=association_matches,
            license_numbers=license_numbers,
            raw_text=text,
            region_image=region_image
        )

        # Step 5: Determine overall validity
        # Threshold: 0.6 confidence required for validity
        is_valid = confidence >= 0.6

        return ValidationResult(
            valid=is_valid,
            associations=list(association_matches.keys()),
            license_numbers=license_numbers,
            confidence=confidence,
            raw_text=text,
            peng_designation=peng_check['designation'],
            validation_details={
                'peng_check': peng_check,
                'association_matches': association_matches,
                'license_extracted': len(license_numbers) > 0
            }
        )

    def _check_peng_designation(self, text_upper: str) -> Dict[str, Any]:
        """
        Check for various P.Eng designation formats.

        Args:
            text_upper: Text in uppercase

        Returns:
            Dictionary with 'found' boolean and 'designation' string
        """
        peng_patterns = [
            r'\bP\.?\s*ENG\.?\b',
            r'\bPROFESSIONAL\s+ENGINEER\b',
            r'\bPENG\b',
            r'\bP\.E\.\b',
            r'\bING\.?\b',  # French abbreviation (ingénieur)
        ]

        for pattern in peng_patterns:
            match = re.search(pattern, text_upper)
            if match:
                return {
                    'found': True,
                    'designation': match.group(),
                    'pattern': pattern
                }

        return {'found': False, 'designation': None}

    def _check_association_patterns(
        self,
        text: str,
        text_upper: str,
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if text matches association-specific patterns.

        Args:
            text: Original text (mixed case)
            text_upper: Uppercased text
            rules: Association rules dictionary

        Returns:
            Dictionary with match information
        """
        match_info = {
            'found': False,
            'exact_match': False,
            'license_found': False,
            'matched_patterns': []
        }

        # Check association name patterns
        for pattern in rules['patterns']:
            if re.search(pattern, text_upper, re.IGNORECASE):
                match_info['found'] = True
                match_info['matched_patterns'].append(pattern)

                # Check if it's an exact abbreviation match
                if pattern in rules.get('abbreviations', []):
                    match_info['exact_match'] = True

        # Check for license patterns (if association found)
        if match_info['found']:
            for license_pattern in rules.get('license_patterns', []):
                if re.search(license_pattern, text_upper):
                    match_info['license_found'] = True
                    break

        return match_info

    def _extract_license_numbers(
        self,
        text_upper: str,
        association_matches: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Extract license numbers from text.

        Args:
            text_upper: Uppercased text
            association_matches: Dictionary of association matches

        Returns:
            List of extracted license numbers
        """
        license_numbers = []
        seen_licenses = set()

        # Try each association's license patterns
        for assoc_name, match_info in association_matches.items():
            rules = self.ASSOCIATION_PATTERNS[assoc_name]

            for license_pattern in rules.get('license_patterns', []):
                matches = re.finditer(license_pattern, text_upper)
                for match in matches:
                    if match.groups():
                        license_num = match.group(1)
                    else:
                        license_num = match.group(0)

                    # Clean the license number
                    license_num = re.sub(r'[^\w]', '', license_num)

                    # Validate format
                    if re.match(rules['license_format'], license_num):
                        if license_num not in seen_licenses:
                            license_numbers.append(license_num)
                            seen_licenses.add(license_num)

        return license_numbers
