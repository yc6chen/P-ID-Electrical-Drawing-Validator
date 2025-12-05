"""
Detection module for identifying engineering seals and signatures in drawings.

This module provides various detection methods including template matching,
contour detection, and color-based detection.
"""

from .detection_models import DetectedRegion, DetectionResult, DetectionConfig
from .seal_detector import SealDetector

__all__ = [
    'DetectedRegion',
    'DetectionResult',
    'DetectionConfig',
    'SealDetector'
]
