"""
Main seal detector that orchestrates multiple detection methods.
"""

import cv2
import numpy as np
import time
from typing import List, Optional
from pathlib import Path

from .detection_models import DetectedRegion, DetectionResult, DetectionConfig
from .template_matcher import TemplateMatcher
from .contour_detector import ContourDetector
from .color_detector import ColorDetector
from ..core.image_processor import ImagePreprocessor


class SealDetector:
    """
    Main detector that orchestrates multiple detection methods.

    This class coordinates template matching, contour detection, and
    color-based detection to find engineering seals and signatures.
    """

    def __init__(
        self,
        config: Optional[DetectionConfig] = None,
        templates_dir: str = "templates"
    ):
        """
        Initialize the seal detector.

        Args:
            config: Detection configuration (uses defaults if None)
            templates_dir: Directory containing seal templates
        """
        self.config = config or DetectionConfig()

        # Initialize individual detectors
        self.template_matcher = TemplateMatcher(templates_dir, self.config)
        self.contour_detector = ContourDetector(self.config)
        self.color_detector = ColorDetector(self.config)

        # Image preprocessor
        self.preprocessor = ImagePreprocessor()

        print("SealDetector initialized successfully")
        print(f"  - Templates loaded: {len(self.template_matcher.get_template_names())}")
        print(f"  - Min confidence threshold: {self.config.min_confidence}")

    def detect(self, image: np.ndarray, page_num: int = 0) -> DetectionResult:
        """
        Main detection pipeline that runs all detection methods.

        Args:
            image: Input image as BGR numpy array
            page_num: Page number (for multi-page documents)

        Returns:
            DetectionResult containing all detected regions
        """
        start_time = time.time()

        # Get image dimensions
        img_height, img_width = image.shape[:2]

        # Preprocess image
        gray_image, color_image = self.preprocessor.preprocess_for_detection(image)

        # Run all detection methods
        print(f"Running detection on page {page_num}...")

        # Template matching on grayscale
        template_results = self.template_matcher.detect(gray_image)
        print(f"  - Template matching: {len(template_results)} regions found")

        # Contour detection on grayscale
        contour_results = self.contour_detector.detect(gray_image)
        print(f"  - Contour detection: {len(contour_results)} regions found")

        # Color-based detection on color image
        color_results = self.color_detector.detect(color_image)
        print(f"  - Color detection: {len(color_results)} regions found")

        # Consolidate all results
        all_results = template_results + contour_results + color_results
        print(f"  - Total detections before consolidation: {len(all_results)}")

        # Consolidate and filter detections
        consolidated_results = self._consolidate_detections(all_results)
        print(f"  - Total detections after consolidation: {len(consolidated_results)}")

        # Filter by confidence threshold
        filtered_results = [
            r for r in consolidated_results
            if r.confidence >= self.config.min_confidence
        ]
        print(f"  - Detections after confidence filtering: {len(filtered_results)}")

        # Sort by confidence (highest first)
        filtered_results = sorted(
            filtered_results,
            key=lambda x: x.confidence,
            reverse=True
        )

        # Set page number for all regions
        for region in filtered_results:
            region.page_num = page_num

        # Calculate processing time
        processing_time = time.time() - start_time
        print(f"  - Detection completed in {processing_time:.2f} seconds")

        # Create and return result
        result = DetectionResult(
            page_num=page_num,
            regions=filtered_results,
            processing_time=processing_time,
            image_dimensions=(img_width, img_height)
        )

        return result

    def _consolidate_detections(
        self,
        detections: List[DetectedRegion]
    ) -> List[DetectedRegion]:
        """
        Remove overlapping detections, keeping highest confidence ones.

        When multiple detection methods find the same region, keep only
        the detection with the highest confidence score.

        Args:
            detections: List of all detected regions

        Returns:
            Consolidated list with overlaps removed
        """
        if not detections:
            return []

        # Sort by confidence (highest first)
        sorted_detections = sorted(
            detections,
            key=lambda r: r.confidence,
            reverse=True
        )

        # Keep track of which regions to keep
        keep = []

        while sorted_detections:
            # Take the highest confidence region
            current = sorted_detections.pop(0)
            keep.append(current)

            # Remove overlapping regions
            # Use a more lenient threshold for consolidation
            sorted_detections = [
                r for r in sorted_detections
                if not current.overlaps_with(r, self.config.nms_threshold)
            ]

        return keep

    def detect_multi_page(
        self,
        images: List[np.ndarray]
    ) -> List[DetectionResult]:
        """
        Run detection on multiple pages.

        Args:
            images: List of images as BGR numpy arrays

        Returns:
            List of DetectionResult, one per page
        """
        results = []

        print(f"\nDetecting seals in {len(images)} pages...")

        for page_num, image in enumerate(images):
            result = self.detect(image, page_num)
            results.append(result)

        # Print summary
        total_detections = sum(r.detection_count for r in results)
        print(f"\nDetection Summary:")
        print(f"  - Total pages processed: {len(images)}")
        print(f"  - Total regions detected: {total_detections}")
        print(f"  - Pages with detections: {sum(1 for r in results if r.has_detections)}")

        return results

    def extract_rois(
        self,
        image: np.ndarray,
        regions: List[DetectedRegion]
    ) -> List[np.ndarray]:
        """
        Extract regions of interest from an image.

        Args:
            image: Full image
            regions: List of detected regions

        Returns:
            List of cropped ROI images
        """
        rois = []

        for region in regions:
            roi = region.extract_roi(image)
            rois.append(roi)

        return rois

    def get_detection_summary(
        self,
        result: DetectionResult
    ) -> dict:
        """
        Generate a summary of detection results.

        Args:
            result: Detection result to summarize

        Returns:
            Dictionary containing summary statistics
        """
        summary = {
            'page_num': result.page_num,
            'total_detections': result.detection_count,
            'processing_time': result.processing_time,
            'image_dimensions': result.image_dimensions,
            'by_method': {},
            'by_confidence': {
                'high (>0.8)': 0,
                'medium (0.65-0.8)': 0,
                'low (<0.65)': 0
            }
        }

        # Count by method
        for method in ['template_matching', 'contour_detection', 'color_detection']:
            count = len(result.get_regions_by_method(method))
            summary['by_method'][method] = count

        # Count by confidence level
        for region in result.regions:
            if region.confidence > 0.8:
                summary['by_confidence']['high (>0.8)'] += 1
            elif region.confidence >= 0.65:
                summary['by_confidence']['medium (0.65-0.8)'] += 1
            else:
                summary['by_confidence']['low (<0.65)'] += 1

        return summary

    def visualize_detections(
        self,
        image: np.ndarray,
        regions: List[DetectedRegion]
    ) -> np.ndarray:
        """
        Draw bounding boxes on image for visualization.

        Args:
            image: Input image
            regions: List of detected regions

        Returns:
            Image with bounding boxes drawn
        """
        # Make a copy to avoid modifying original
        vis_image = image.copy()

        # Color scheme for different detection methods
        colors = {
            'template_matching': (0, 255, 0),  # Green
            'contour_detection': (255, 0, 0),  # Blue
            'color_detection': (0, 0, 255)     # Red
        }

        for region in regions:
            # Get color based on detection method
            color = colors.get(region.detection_method, (255, 255, 0))

            # Draw rectangle
            cv2.rectangle(
                vis_image,
                (region.x, region.y),
                (region.x + region.width, region.y + region.height),
                color,
                2
            )

            # Prepare label
            label = f"{region.detection_method[:4]}: {region.confidence:.2f}"
            if region.template_name:
                label = f"{region.template_name}: {region.confidence:.2f}"
            elif region.color:
                label = f"{region.color}: {region.confidence:.2f}"

            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(
                vis_image,
                (region.x, region.y - label_size[1] - 5),
                (region.x + label_size[0], region.y),
                color,
                -1
            )

            # Draw label text
            cv2.putText(
                vis_image,
                label,
                (region.x, region.y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )

        return vis_image
