"""
Image preprocessing specifically optimized for engineering seal/stamp OCR.
"""

import cv2
import numpy as np
from typing import Dict


class TextImagePreprocessor:
    """
    Preprocessor for images before OCR to improve text extraction accuracy.
    """

    def prepare_for_ocr(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Generate multiple preprocessed versions of the image for OCR.

        Different preprocessing strategies work better for different image qualities.
        By trying multiple approaches, we increase the chance of successful OCR.

        Args:
            image: Input image as numpy array (BGR or grayscale)

        Returns:
            Dictionary mapping strategy name to preprocessed image
        """
        processed = {}

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Strategy 1: Basic grayscale
        processed["gray"] = gray

        # Strategy 2: Contrast enhanced
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        contrast = clahe.apply(gray)
        processed["contrast"] = contrast

        # Strategy 3: Adaptive threshold (binarization)
        binary = cv2.adaptiveThreshold(
            contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        processed["binary"] = binary

        # Strategy 4: Denoised
        denoised = cv2.fastNlMeansDenoising(binary, h=30)
        processed["denoised"] = denoised

        # Strategy 5: Deskewed (if text appears rotated)
        deskewed = self._deskew_image(denoised)
        processed["deskewed"] = deskewed

        # Strategy 6: Inverted (white text on dark background)
        inverted = cv2.bitwise_not(contrast)
        processed["inverted"] = inverted

        # Strategy 7: Color mask for red/blue text (if color image)
        if len(image.shape) == 3:
            red_text = self._extract_colored_text(image, 'red')
            blue_text = self._extract_colored_text(image, 'blue')
            if red_text is not None:
                processed["red_text"] = red_text
            if blue_text is not None:
                processed["blue_text"] = blue_text

        return processed

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew image based on text angle detection.

        Engineering seals are sometimes stamped at slight angles.
        This method attempts to correct rotation.

        Args:
            image: Binary or grayscale image

        Returns:
            Deskewed image
        """
        try:
            # Compute the skew angle using Hough transform
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(
                edges, 1, np.pi / 180, 100,
                minLineLength=100, maxLineGap=10
            )

            if lines is not None and len(lines) > 0:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    angles.append(angle)

                if angles:
                    median_angle = np.median(angles)
                    # Only deskew if significant angle
                    if abs(median_angle) > 0.5:
                        (h, w) = image.shape[:2]
                        center = (w // 2, h // 2)
                        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        rotated = cv2.warpAffine(
                            image, M, (w, h),
                            flags=cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_REPLICATE
                        )
                        return rotated
        except Exception:
            # If deskewing fails, return original
            pass

        return image

    def _extract_colored_text(self, image: np.ndarray, color: str) -> np.ndarray:
        """
        Extract text of a specific color from image.

        Engineering seals are often stamped in red or blue ink.

        Args:
            image: Color image (BGR)
            color: 'red' or 'blue'

        Returns:
            Binary image with colored text extracted, or None if extraction fails
        """
        try:
            # Convert to HSV for better color separation
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            if color == 'red':
                # Red color has two ranges in HSV (wraps around at 180)
                lower_red1 = np.array([0, 70, 50])
                upper_red1 = np.array([10, 255, 255])
                lower_red2 = np.array([170, 70, 50])
                upper_red2 = np.array([180, 255, 255])

                mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                mask = cv2.bitwise_or(mask1, mask2)

            elif color == 'blue':
                lower_blue = np.array([100, 50, 50])
                upper_blue = np.array([130, 255, 255])
                mask = cv2.inRange(hsv, lower_blue, upper_blue)

            else:
                return None

            # Apply morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # Only return if we found significant colored regions
            if np.sum(mask > 0) > 100:  # At least 100 pixels
                return mask

        except Exception:
            pass

        return None

    def enhance_for_small_text(self, image: np.ndarray, scale_factor: float = 2.0) -> np.ndarray:
        """
        Upscale small text regions for better OCR.

        Args:
            image: Input image
            scale_factor: Upscaling factor (default: 2.0)

        Returns:
            Upscaled image
        """
        height, width = image.shape[:2]
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        # Use cubic interpolation for better quality when upscaling
        upscaled = cv2.resize(
            image, (new_width, new_height),
            interpolation=cv2.INTER_CUBIC
        )

        return upscaled
