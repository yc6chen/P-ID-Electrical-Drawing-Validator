"""
Region of Interest (ROI) extraction and processing utilities.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

from .detection_models import DetectedRegion


class RegionProcessor:
    """
    Utilities for extracting and processing regions of interest.

    This class provides methods to extract, enhance, and save ROIs
    for further processing (e.g., OCR in Phase 3).
    """

    @staticmethod
    def extract_roi(
        image: np.ndarray,
        region: DetectedRegion,
        padding: int = 10
    ) -> np.ndarray:
        """
        Extract region of interest with optional padding.

        Args:
            image: Full image
            region: Detected region to extract
            padding: Additional padding around the region (pixels)

        Returns:
            Cropped ROI image
        """
        # Get image dimensions
        img_height, img_width = image.shape[:2]

        # Calculate padded coordinates
        x1 = max(0, region.x - padding)
        y1 = max(0, region.y - padding)
        x2 = min(img_width, region.x + region.width + padding)
        y2 = min(img_height, region.y + region.height + padding)

        # Extract ROI
        roi = image[y1:y2, x1:x2]

        return roi

    @staticmethod
    def extract_all_rois(
        image: np.ndarray,
        regions: List[DetectedRegion],
        padding: int = 10
    ) -> List[Tuple[DetectedRegion, np.ndarray]]:
        """
        Extract all ROIs from an image.

        Args:
            image: Full image
            regions: List of detected regions
            padding: Additional padding around each region

        Returns:
            List of tuples (region, roi_image)
        """
        rois = []

        for region in regions:
            roi = RegionProcessor.extract_roi(image, region, padding)
            rois.append((region, roi))

        return rois

    @staticmethod
    def enhance_roi_for_ocr(roi: np.ndarray) -> np.ndarray:
        """
        Enhance ROI for better OCR performance (Phase 3).

        Args:
            roi: ROI image

        Returns:
            Enhanced ROI ready for OCR
        """
        # Convert to grayscale if needed
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi

        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Apply adaptive thresholding for better text contrast
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        return binary

    @staticmethod
    def resize_roi(
        roi: np.ndarray,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        scale_factor: Optional[float] = None
    ) -> np.ndarray:
        """
        Resize ROI while maintaining aspect ratio.

        Args:
            roi: ROI image
            target_width: Target width (optional)
            target_height: Target height (optional)
            scale_factor: Scale factor (optional, overrides target dimensions)

        Returns:
            Resized ROI
        """
        height, width = roi.shape[:2]

        if scale_factor is not None:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
        else:
            # Calculate scale to fit target dimensions
            scale_w = target_width / width if target_width else 1.0
            scale_h = target_height / height if target_height else 1.0
            scale = min(scale_w, scale_h)

            new_width = int(width * scale)
            new_height = int(height * scale)

        # Resize
        resized = cv2.resize(
            roi,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
        )

        return resized

    @staticmethod
    def save_roi(
        roi: np.ndarray,
        filepath: str,
        region: Optional[DetectedRegion] = None
    ) -> bool:
        """
        Save ROI to file.

        Args:
            roi: ROI image
            filepath: Output file path
            region: Optional region metadata for filename

        Returns:
            True if saved successfully
        """
        try:
            # Create directory if it doesn't exist
            output_path = Path(filepath)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save image
            success = cv2.imwrite(str(output_path), roi)

            if success:
                print(f"Saved ROI to: {filepath}")
            else:
                print(f"Failed to save ROI to: {filepath}")

            return success

        except Exception as e:
            print(f"Error saving ROI: {e}")
            return False

    @staticmethod
    def save_all_rois(
        rois: List[Tuple[DetectedRegion, np.ndarray]],
        output_dir: str,
        prefix: str = "roi"
    ) -> List[str]:
        """
        Save all ROIs to files.

        Args:
            rois: List of (region, roi_image) tuples
            output_dir: Output directory
            prefix: Filename prefix

        Returns:
            List of saved file paths
        """
        saved_paths = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for i, (region, roi) in enumerate(rois):
            # Generate filename
            method = region.detection_method.replace('_', '-')
            confidence = int(region.confidence * 100)
            filename = f"{prefix}_{i:03d}_{method}_conf{confidence}.png"
            filepath = output_path / filename

            # Save ROI
            if RegionProcessor.save_roi(roi, str(filepath), region):
                saved_paths.append(str(filepath))

        print(f"Saved {len(saved_paths)} ROIs to {output_dir}")
        return saved_paths

    @staticmethod
    def draw_roi_overlay(
        image: np.ndarray,
        region: DetectedRegion,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw a single ROI overlay on the image.

        Args:
            image: Full image
            region: Region to highlight
            color: BGR color for the overlay
            thickness: Line thickness

        Returns:
            Image with overlay drawn
        """
        # Make a copy
        overlay = image.copy()

        # Draw rectangle
        cv2.rectangle(
            overlay,
            (region.x, region.y),
            (region.x + region.width, region.y + region.height),
            color,
            thickness
        )

        # Draw label
        label = f"{region.confidence:.2f}"
        if region.template_name:
            label = f"{region.template_name} {label}"
        elif region.color:
            label = f"{region.color} {label}"

        # Draw label background
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 1
        label_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]

        cv2.rectangle(
            overlay,
            (region.x, region.y - label_size[1] - 8),
            (region.x + label_size[0] + 4, region.y),
            color,
            -1
        )

        # Draw label text
        cv2.putText(
            overlay,
            label,
            (region.x + 2, region.y - 4),
            font,
            font_scale,
            (255, 255, 255),
            font_thickness
        )

        return overlay

    @staticmethod
    def create_roi_grid(
        rois: List[np.ndarray],
        grid_cols: int = 4,
        cell_size: Tuple[int, int] = (200, 200),
        padding: int = 10
    ) -> np.ndarray:
        """
        Create a grid visualization of multiple ROIs.

        Args:
            rois: List of ROI images
            grid_cols: Number of columns in grid
            cell_size: Size of each cell (width, height)
            padding: Padding between cells

        Returns:
            Grid image
        """
        if not rois:
            return np.zeros((cell_size[1], cell_size[0], 3), dtype=np.uint8)

        # Calculate grid dimensions
        n_rois = len(rois)
        grid_rows = (n_rois + grid_cols - 1) // grid_cols

        # Calculate output size
        grid_width = grid_cols * cell_size[0] + (grid_cols + 1) * padding
        grid_height = grid_rows * cell_size[1] + (grid_rows + 1) * padding

        # Create blank canvas
        grid = np.ones((grid_height, grid_width, 3), dtype=np.uint8) * 240

        # Place ROIs in grid
        for i, roi in enumerate(rois):
            row = i // grid_cols
            col = i % grid_cols

            # Resize ROI to fit cell
            roi_resized = RegionProcessor.resize_roi(
                roi,
                target_width=cell_size[0] - 2 * padding,
                target_height=cell_size[1] - 2 * padding
            )

            # Ensure 3 channels
            if len(roi_resized.shape) == 2:
                roi_resized = cv2.cvtColor(roi_resized, cv2.COLOR_GRAY2BGR)

            # Calculate position
            y_start = row * cell_size[1] + (row + 1) * padding
            x_start = col * cell_size[0] + (col + 1) * padding

            roi_h, roi_w = roi_resized.shape[:2]

            # Place ROI in grid
            grid[y_start:y_start + roi_h, x_start:x_start + roi_w] = roi_resized

            # Draw border
            cv2.rectangle(
                grid,
                (x_start - 1, y_start - 1),
                (x_start + roi_w, y_start + roi_h),
                (100, 100, 100),
                1
            )

        return grid
