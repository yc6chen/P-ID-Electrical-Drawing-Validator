"""
Detects known engineering seals using template matching.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import os

from .detection_models import DetectedRegion, DetectionConfig


class TemplateMatcher:
    """
    Template matching detector for finding known engineering seal patterns.

    This class uses OpenCV's template matching with multi-scale detection
    to find engineering seals that match provided templates.
    """

    def __init__(self, templates_dir: str = "templates", config: Optional[DetectionConfig] = None):
        """
        Initialize the template matcher.

        Args:
            templates_dir: Directory containing template images
            config: Detection configuration (uses defaults if None)
        """
        self.config = config or DetectionConfig()
        self.templates_dir = templates_dir
        self.templates: Dict[str, np.ndarray] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all template images from the templates directory."""
        # Get the absolute path to templates directory
        base_dir = Path(__file__).parent.parent.parent
        templates_path = base_dir / self.templates_dir

        if not templates_path.exists():
            print(f"Warning: Templates directory not found: {templates_path}")
            return

        # Load all image files from templates directory
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            for template_file in templates_path.glob(ext):
                template_name = template_file.stem
                template_img = cv2.imread(str(template_file), cv2.IMREAD_GRAYSCALE)

                if template_img is not None:
                    self.templates[template_name] = template_img
                    print(f"Loaded template: {template_name} ({template_img.shape})")
                else:
                    print(f"Warning: Failed to load template: {template_file}")

        if not self.templates:
            print("Warning: No templates loaded. Template matching will not work.")

    def detect(self, image: np.ndarray) -> List[DetectedRegion]:
        """
        Perform multi-scale template matching to detect known seals.

        Args:
            image: Input image as BGR numpy array

        Returns:
            List of detected regions
        """
        if not self.templates:
            return []

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = image

        results = []

        # Process each template
        for template_name, template in self.templates.items():
            template_results = self._match_template_multiscale(
                gray_image,
                template,
                template_name
            )
            results.extend(template_results)

        # Apply non-maximum suppression to remove overlapping detections
        results = self._apply_non_max_suppression(results)

        return results

    def _match_template_multiscale(
        self,
        image: np.ndarray,
        template: np.ndarray,
        template_name: str
    ) -> List[DetectedRegion]:
        """
        Perform template matching at multiple scales.

        Args:
            image: Grayscale image to search
            template: Template to find
            template_name: Name of the template

        Returns:
            List of detected regions
        """
        results = []
        img_height, img_width = image.shape

        # Generate scale factors
        scale_start, scale_end = self.config.template_scale_range
        scales = np.linspace(scale_start, scale_end, self.config.template_scale_steps)

        for scale in scales:
            # Resize template
            scaled_template = self._resize_template(template, scale)

            # Skip if template is larger than image
            if (scaled_template.shape[0] > img_height or
                scaled_template.shape[1] > img_width):
                continue

            # Perform template matching
            match_result = cv2.matchTemplate(
                image,
                scaled_template,
                cv2.TM_CCOEFF_NORMED
            )

            # Find locations above threshold
            locations = np.where(match_result >= self.config.template_confidence_threshold)

            # Create DetectedRegion for each match
            for pt in zip(*locations[::-1]):
                confidence = float(match_result[pt[1], pt[0]])

                region = DetectedRegion(
                    x=int(pt[0]),
                    y=int(pt[1]),
                    width=int(scaled_template.shape[1]),
                    height=int(scaled_template.shape[0]),
                    confidence=confidence,
                    detection_method="template_matching",
                    template_name=template_name
                )
                results.append(region)

        return results

    def _resize_template(self, template: np.ndarray, scale: float) -> np.ndarray:
        """
        Resize template by scale factor.

        Args:
            template: Template image
            scale: Scale factor

        Returns:
            Resized template
        """
        new_width = int(template.shape[1] * scale)
        new_height = int(template.shape[0] * scale)

        # Ensure minimum size
        if new_width < 10 or new_height < 10:
            return template

        resized = cv2.resize(
            template,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
        )

        return resized

    def _apply_non_max_suppression(
        self,
        regions: List[DetectedRegion]
    ) -> List[DetectedRegion]:
        """
        Apply non-maximum suppression to remove overlapping detections.

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

            # Remove overlapping regions
            sorted_regions = [
                r for r in sorted_regions
                if not current.overlaps_with(r, self.config.nms_threshold)
            ]

        return keep

    def add_template(self, template_name: str, template_image: np.ndarray) -> None:
        """
        Add a new template for matching.

        Args:
            template_name: Name for the template
            template_image: Template image (grayscale or color)
        """
        # Convert to grayscale if needed
        if len(template_image.shape) == 3:
            template_image = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)

        self.templates[template_name] = template_image
        print(f"Added template: {template_name} ({template_image.shape})")

    def remove_template(self, template_name: str) -> bool:
        """
        Remove a template from the matcher.

        Args:
            template_name: Name of template to remove

        Returns:
            True if template was removed, False if not found
        """
        if template_name in self.templates:
            del self.templates[template_name]
            return True
        return False

    def get_template_names(self) -> List[str]:
        """Get list of loaded template names."""
        return list(self.templates.keys())
