"""
Detects engineering seals by their distinctive colors (red/blue).
"""

import cv2
import numpy as np
from typing import List, Dict, Optional

from .detection_models import DetectedRegion, DetectionConfig


class ColorDetector:
    """
    Color-based detector for finding engineering seals by their distinctive colors.

    Engineering seals are often printed in specific colors (red, blue, etc.).
    This detector uses HSV color space filtering to find these colored regions.
    """

    def __init__(self, config: Optional[DetectionConfig] = None):
        """
        Initialize the color detector.

        Args:
            config: Detection configuration (uses defaults if None)
        """
        self.config = config or DetectionConfig()

        # HSV color ranges for engineering seals
        # These ranges are tuned for typical engineering seal colors
        self.color_ranges = {
            'engineering_red': {
                'lower': np.array([0, 50, 50]),
                'upper': np.array([10, 255, 255])
            },
            'engineering_red_wrap': {  # Red wraps around in HSV (170-180)
                'lower': np.array([170, 50, 50]),
                'upper': np.array([180, 255, 255])
            },
            'engineering_blue': {
                'lower': np.array([100, 50, 50]),
                'upper': np.array([130, 255, 255])
            },
            'engineering_green': {
                'lower': np.array([40, 40, 40]),
                'upper': np.array([80, 255, 255])
            },
            'engineering_black': {
                'lower': np.array([0, 0, 0]),
                'upper': np.array([180, 255, 50])
            }
        }

    def detect(self, image: np.ndarray) -> List[DetectedRegion]:
        """
        Detect colored seals using HSV color filtering.

        Args:
            image: Input image as BGR numpy array

        Returns:
            List of detected regions
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Apply Gaussian blur to reduce noise
        hsv = cv2.GaussianBlur(hsv, (5, 5), 0)

        results = []

        # Process each color range
        for color_name, ranges in self.color_ranges.items():
            color_results = self._detect_color_range(
                hsv,
                ranges['lower'],
                ranges['upper'],
                color_name
            )
            results.extend(color_results)

        # Merge red and red_wrap results (they're the same color)
        results = self._merge_red_detections(results)

        # Remove overlapping detections
        results = self._remove_overlaps(results)

        return results

    def _detect_color_range(
        self,
        hsv_image: np.ndarray,
        lower_bound: np.ndarray,
        upper_bound: np.ndarray,
        color_name: str
    ) -> List[DetectedRegion]:
        """
        Detect regions within a specific color range.

        Args:
            hsv_image: Image in HSV color space
            lower_bound: Lower HSV bound
            upper_bound: Upper HSV bound
            color_name: Name of the color being detected

        Returns:
            List of detected regions for this color
        """
        # Create mask for color range
        mask = cv2.inRange(hsv_image, lower_bound, upper_bound)

        # Clean up mask with morphological operations
        mask = self._clean_mask(mask)

        # Find contours in the mask
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        results = []

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by area
            if not (self.config.color_min_area < area < self.config.color_max_area):
                continue

            # Check shape characteristics
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue

            # Calculate circularity (4 * pi * area / perimeter^2)
            # Perfect circle = 1.0, as shape becomes less circular, value decreases
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            # Engineering seals can be circular or rectangular
            # Accept both circular shapes and rectangular shapes
            is_circular = circularity > self.config.color_min_circularity

            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0

            # Rectangular seals tend to be squarish (aspect ratio near 1)
            is_rectangular = 0.5 < aspect_ratio < 2.0

            if is_circular or is_rectangular:
                # Calculate confidence based on shape and color intensity
                confidence = self._calculate_confidence(
                    circularity,
                    area,
                    aspect_ratio,
                    is_circular
                )

                # Clean color name for display
                display_color = color_name.replace('engineering_', '').replace('_wrap', '')

                region = DetectedRegion(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=confidence,
                    detection_method="color_detection",
                    color=display_color
                )
                results.append(region)

        return results

    def _clean_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Clean up the color mask using morphological operations.

        Args:
            mask: Binary mask

        Returns:
            Cleaned mask
        """
        # Remove small noise
        kernel_small = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small)

        # Close small gaps
        kernel_large = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_large)

        # Dilate slightly to connect nearby regions
        mask = cv2.dilate(mask, kernel_small, iterations=1)

        return mask

    def _calculate_confidence(
        self,
        circularity: float,
        area: float,
        aspect_ratio: float,
        is_circular: bool
    ) -> float:
        """
        Calculate confidence score based on shape properties.

        Args:
            circularity: How circular the shape is (0-1)
            area: Area of the region
            aspect_ratio: Width / height ratio
            is_circular: Whether the shape is circular

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.6  # Base confidence for color detection

        if is_circular:
            # Bonus for high circularity
            confidence += circularity * 0.2
        else:
            # Bonus for square-like shapes
            square_score = 1.0 - abs(1.0 - aspect_ratio)
            confidence += square_score * 0.15

        # Bonus for ideal size range (middle of the allowed range)
        ideal_area = (self.config.color_min_area + self.config.color_max_area) / 2
        area_score = 1.0 - min(abs(area - ideal_area) / ideal_area, 1.0)
        confidence += area_score * 0.1

        # Clamp to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))

        return confidence

    def _merge_red_detections(self, regions: List[DetectedRegion]) -> List[DetectedRegion]:
        """
        Merge red and red_wrap detections (same color, split due to HSV wrap).

        Args:
            regions: List of all detected regions

        Returns:
            List with red detections merged
        """
        # Just rename 'red_wrap' to 'red' for consistency
        for region in regions:
            if region.color == 'red_wrap':
                region.color = 'red'

        return regions

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
                if not current.overlaps_with(r, threshold=0.3)
            ]

        return keep

    def add_color_range(
        self,
        color_name: str,
        lower_bound: np.ndarray,
        upper_bound: np.ndarray
    ) -> None:
        """
        Add a custom color range for detection.

        Args:
            color_name: Name for this color range
            lower_bound: Lower HSV bound (numpy array [H, S, V])
            upper_bound: Upper HSV bound (numpy array [H, S, V])
        """
        self.color_ranges[color_name] = {
            'lower': lower_bound,
            'upper': upper_bound
        }
        print(f"Added color range: {color_name}")

    def get_color_ranges(self) -> Dict[str, Dict[str, np.ndarray]]:
        """Get the current color ranges being used."""
        return self.color_ranges.copy()
