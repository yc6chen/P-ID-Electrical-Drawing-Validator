"""
Data models for validation results.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np


@dataclass
class ValidationResult:
    """Result of text validation against association rules."""

    valid: bool
    confidence: float  # 0.0 to 1.0
    raw_text: str
    associations: List[str] = field(default_factory=list)
    license_numbers: List[str] = field(default_factory=list)
    peng_designation: Optional[str] = None
    reason: Optional[str] = None
    validation_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'valid': self.valid,
            'confidence': self.confidence,
            'associations': self.associations,
            'license_numbers': self.license_numbers,
            'peng_designation': self.peng_designation,
            'reason': self.reason,
            'raw_text': self.raw_text[:100] + '...' if len(self.raw_text) > 100 else self.raw_text
        }


@dataclass
class RegionValidation:
    """Combined OCR and validation result for a detected region."""

    region: Any  # DetectedRegion from detection module
    ocr_result: Any  # OCRExtractionResult
    validation_result: ValidationResult
    roi_image: Optional[np.ndarray] = None

    @property
    def is_valid_signature(self) -> bool:
        """Check if this region contains a valid P.Eng signature."""
        return self.validation_result.valid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'region': self.region.to_dict() if hasattr(self.region, 'to_dict') else str(self.region),
            'ocr': self.ocr_result.to_dict() if hasattr(self.ocr_result, 'to_dict') else str(self.ocr_result),
            'validation': self.validation_result.to_dict(),
            'is_valid': self.is_valid_signature
        }


@dataclass
class PageValidationResult:
    """Validation results for an entire page."""

    page_number: int
    region_validations: List[RegionValidation] = field(default_factory=list)
    has_valid_signature: bool = False
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def valid_region_count(self) -> int:
        """Get count of valid regions."""
        return sum(1 for rv in self.region_validations if rv.is_valid_signature)

    @property
    def total_region_count(self) -> int:
        """Get total count of validated regions."""
        return len(self.region_validations)

    def get_best_validation(self) -> Optional[RegionValidation]:
        """
        Get the validation with highest confidence.

        Returns:
            RegionValidation with highest confidence, or None if no validations
        """
        if not self.region_validations:
            return None

        return max(
            self.region_validations,
            key=lambda rv: rv.validation_result.confidence
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'page_number': self.page_number,
            'has_valid_signature': self.has_valid_signature,
            'valid_regions': self.valid_region_count,
            'total_regions': self.total_region_count,
            'region_validations': [rv.to_dict() for rv in self.region_validations],
            'processing_time': self.processing_time,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class DrawingValidationResult:
    """Overall validation result for an entire drawing (all pages)."""

    filepath: str
    page_results: List[PageValidationResult] = field(default_factory=list)
    overall_valid: bool = False
    total_processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_pages(self) -> int:
        """Get total number of pages."""
        return len(self.page_results)

    @property
    def valid_pages_count(self) -> int:
        """Get count of pages with valid signatures."""
        return sum(1 for pr in self.page_results if pr.has_valid_signature)

    @property
    def has_any_valid_signature(self) -> bool:
        """Check if any page has a valid signature."""
        return any(pr.has_valid_signature for pr in self.page_results)

    def get_all_associations(self) -> List[str]:
        """Get all unique associations found across all pages."""
        associations = set()
        for page_result in self.page_results:
            for rv in page_result.region_validations:
                associations.update(rv.validation_result.associations)
        return sorted(list(associations))

    def get_all_license_numbers(self) -> List[str]:
        """Get all unique license numbers found across all pages."""
        licenses = set()
        for page_result in self.page_results:
            for rv in page_result.region_validations:
                licenses.update(rv.validation_result.license_numbers)
        return sorted(list(licenses))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'filepath': self.filepath,
            'overall_valid': self.overall_valid,
            'total_pages': self.total_pages,
            'valid_pages': self.valid_pages_count,
            'associations': self.get_all_associations(),
            'license_numbers': self.get_all_license_numbers(),
            'page_results': [pr.to_dict() for pr in self.page_results],
            'total_processing_time': self.total_processing_time,
            'timestamp': self.timestamp.isoformat()
        }
