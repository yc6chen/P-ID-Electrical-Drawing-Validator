"""
Data models for OCR results.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class OCRExtractionResult:
    """Result of OCR text extraction."""

    text: str
    confidence: float  # 0.0 to 1.0
    engine_used: str  # "tesseract", "easyocr", "none"
    preprocessing_steps: List[str] = field(default_factory=list)
    raw_image: Optional[np.ndarray] = None
    bounding_boxes: Optional[List[Dict]] = None  # Character/word boxes

    @property
    def has_text(self) -> bool:
        """Check if any text was extracted."""
        return bool(self.text.strip())

    @property
    def text_length(self) -> int:
        """Get length of extracted text."""
        return len(self.text.strip())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'engine_used': self.engine_used,
            'preprocessing_steps': self.preprocessing_steps,
            'has_text': self.has_text,
            'text_length': self.text_length
        }
