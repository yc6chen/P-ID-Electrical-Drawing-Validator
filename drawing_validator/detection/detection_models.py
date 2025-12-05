"""
Data models for detection results and configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import numpy as np


@dataclass
class DetectionConfig:
    """Configuration parameters for detection algorithms."""

    # Template matching
    template_confidence_threshold: float = 0.65
    template_scale_range: tuple = (0.5, 1.5)
    template_scale_steps: int = 10

    # Contour detection
    contour_min_area: float = 500
    contour_max_area: float = 10000
    contour_min_aspect_ratio: float = 2.0
    contour_max_aspect_ratio: float = 8.0
    contour_min_width: int = 100
    contour_max_width: int = 800
    contour_min_height: int = 30
    contour_max_height: int = 200

    # Color detection
    color_min_area: float = 300
    color_max_area: float = 5000
    color_min_circularity: float = 0.6

    # General
    min_confidence: float = 0.65
    nms_threshold: float = 0.3  # Non-maximum suppression threshold


@dataclass
class DetectedRegion:
    """Represents a detected potential signature/seal region."""

    x: int  # Top-left x coordinate
    y: int  # Top-left y coordinate
    width: int
    height: int
    confidence: float  # 0.0 to 1.0
    detection_method: str  # "template_matching", "contour_detection", "color_detection"

    # Optional metadata
    template_name: Optional[str] = None
    color: Optional[str] = None
    page_num: int = 0

    @property
    def bbox(self) -> tuple:
        """Get bounding box as (x1, y1, x2, y2)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    @property
    def center(self) -> tuple:
        """Get center point of the region."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        """Get area of the region."""
        return self.width * self.height

    def extract_roi(self, image: np.ndarray) -> np.ndarray:
        """
        Extract region of interest from full image.

        Args:
            image: Full image as numpy array

        Returns:
            Cropped region as numpy array
        """
        x1, y1, x2, y2 = self.bbox
        # Ensure coordinates are within image bounds
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image.shape[1], x2)
        y2 = min(image.shape[0], y2)
        return image[y1:y2, x1:x2]

    def overlaps_with(self, other: 'DetectedRegion', threshold: float = 0.3) -> bool:
        """
        Check if this region overlaps with another region.

        Args:
            other: Another DetectedRegion
            threshold: IoU threshold for considering overlap

        Returns:
            True if regions overlap significantly
        """
        # Calculate intersection
        x1 = max(self.x, other.x)
        y1 = max(self.y, other.y)
        x2 = min(self.x + self.width, other.x + other.width)
        y2 = min(self.y + self.height, other.y + other.height)

        if x2 < x1 or y2 < y1:
            return False

        intersection = (x2 - x1) * (y2 - y1)
        union = self.area + other.area - intersection

        iou = intersection / union if union > 0 else 0
        return iou > threshold

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'confidence': self.confidence,
            'detection_method': self.detection_method,
            'template_name': self.template_name,
            'color': self.color,
            'page_num': self.page_num
        }


@dataclass
class DetectionResult:
    """Container for all detection results from a page."""

    page_num: int
    regions: List[DetectedRegion] = field(default_factory=list)
    processing_time: float = 0.0
    image_dimensions: tuple = (0, 0)

    @property
    def has_detections(self) -> bool:
        """Check if any regions were detected."""
        return len(self.regions) > 0

    @property
    def detection_count(self) -> int:
        """Get total number of detected regions."""
        return len(self.regions)

    def get_regions_by_method(self, method: str) -> List[DetectedRegion]:
        """
        Get regions detected by a specific method.

        Args:
            method: Detection method name

        Returns:
            List of regions detected by that method
        """
        return [r for r in self.regions if r.detection_method == method]

    def get_highest_confidence_regions(self, n: int = 5) -> List[DetectedRegion]:
        """
        Get the top N regions by confidence.

        Args:
            n: Number of regions to return

        Returns:
            List of top N regions sorted by confidence
        """
        sorted_regions = sorted(self.regions, key=lambda r: r.confidence, reverse=True)
        return sorted_regions[:n]

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'page_num': self.page_num,
            'regions': [r.to_dict() for r in self.regions],
            'processing_time': self.processing_time,
            'image_dimensions': self.image_dimensions,
            'detection_count': self.detection_count
        }
