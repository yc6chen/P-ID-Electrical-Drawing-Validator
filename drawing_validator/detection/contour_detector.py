"""
Detects rectangular signature blocks using contour analysis.
"""

import cv2
import numpy as np
from typing import List, Optional

from .detection_models import DetectedRegion, DetectionConfig


class ContourDetector:
    """
    Contour-based detector for finding rectangular signature blocks.

    This class uses OpenCV's contour detection to find rectangular regions
    that likely contain signatures or stamps.
    """

    def __init__(self, config: Optional[DetectionConfig] = None):
        """
        Initialize the contour detector.

        Args:
            config: Detection configuration (uses defaults if None)
        """
        self.config = config or DetectionConfig()

    def detect(self, image: np.ndarray) -> List[DetectedRegion]:
        """
        Find rectangular regions that might contain signatures.

        Args:
            image: Input image as BGR numpy array

        Returns:
            List of detected regions
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply adaptive thresholding for varying lighting
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2
        )

        # Apply morphological operations to clean up noise
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        results = []

        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)

            # Calculate contour properties
            area = cv2.contourArea(contour)
            if area == 0:
                continue

            aspect_ratio = w / h if h > 0 else 0

            # Filter for signature block characteristics
            if self._is_signature_block(area, aspect_ratio, w, h):
                # Calculate confidence based on rectangle properties
                confidence = self._calculate_confidence(contour, area, aspect_ratio)

                region = DetectedRegion(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=confidence,
                    detection_method="contour_detection"
                )
                results.append(region)

        # Remove overlapping detections
        results = self._remove_overlaps(results)

        return results

    def _is_signature_block(
        self,
        area: float,
        aspect_ratio: float,
        width: int,
        height: int
    ) -> bool:
        """
        Heuristic to identify signature blocks.

        Args:
            area: Contour area
            aspect_ratio: Width / height ratio
            width: Bounding box width
            height: Bounding box height

        Returns:
            True if region matches signature block characteristics
        """
        # Check against configured thresholds
        area_ok = self.config.contour_min_area < area < self.config.contour_max_area
        aspect_ok = self.config.contour_min_aspect_ratio < aspect_ratio < self.config.contour_max_aspect_ratio
        width_ok = self.config.contour_min_width < width < self.config.contour_max_width
        height_ok = self.config.contour_min_height < height < self.config.contour_max_height

        return area_ok and aspect_ok and width_ok and height_ok

    def _calculate_confidence(
        self,
        contour: np.ndarray,
        area: float,
        aspect_ratio: float
    ) -> float:
        """
        Calculate confidence score for a contour based on its properties.

        Args:
            contour: The contour
            area: Contour area
            aspect_ratio: Width / height ratio

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence

        # Calculate rectangularity (how close to a perfect rectangle)
        x, y, w, h = cv2.boundingRect(contour)
        bbox_area = w * h
        if bbox_area > 0:
            rectangularity = area / bbox_area
            confidence += rectangularity * 0.2

        # Bonus for ideal aspect ratios (wide rectangles)
        ideal_aspect = 4.0
        aspect_score = 1.0 - min(abs(aspect_ratio - ideal_aspect) / ideal_aspect, 1.0)
        confidence += aspect_score * 0.2

        # Calculate solidity (ratio of contour area to convex hull area)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            solidity = area / hull_area
            confidence += solidity * 0.1

        # Clamp confidence to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))

        return confidence

    def _remove_overlaps(self, regions: List[DetectedRegion]) -> List[DetectedRegion]:
        """
        Remove overlapping regions, keeping the highest confidence ones.

        Args:
            regions: List of detected regions

        Returns:
            Filtered list with overlaps removed
        """
        if not regions:
            return []

        # Sort by confidence (highest first)
        sorted_regions = sorted(regions, key=lambda r: r.confidence, reverse=True)

        # Keep track of which regions to keep
        keep = []

        while sorted_regions:
            # Take the highest confidence region
            current = sorted_regions.pop(0)
            keep.append(current)

            # Remove significantly overlapping regions
            sorted_regions = [
                r for r in sorted_regions
                if not current.overlaps_with(r, threshold=0.5)
            ]

        return keep

    def detect_with_edges(self, image: np.ndarray) -> List[DetectedRegion]:
        """
        Alternative detection method using edge detection.

        This method uses Canny edge detection followed by contour finding.

        Args:
            image: Input image as BGR numpy array

        Returns:
            List of detected regions
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)

        # Dilate edges to connect nearby edges
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(
            dilated,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        results = []

        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)

            # Calculate properties
            area = w * h  # Use bounding box area for edge-based detection
            aspect_ratio = w / h if h > 0 else 0

            # Filter for signature block characteristics
            if self._is_signature_block(area, aspect_ratio, w, h):
                # Calculate confidence
                confidence = self._calculate_confidence(contour, cv2.contourArea(contour), aspect_ratio)

                region = DetectedRegion(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=confidence * 0.8,  # Slightly lower confidence for edge-based
                    detection_method="contour_detection"
                )
                results.append(region)

        # Remove overlapping detections
        results = self._remove_overlaps(results)

        return results
