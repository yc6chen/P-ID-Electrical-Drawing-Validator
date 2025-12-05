"""
Image preprocessing utilities to optimize images for detection algorithms.
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional


class ImagePreprocessor:
    """
    Provides image preprocessing methods to prepare images for detection.

    This class contains static methods for various preprocessing operations
    including conversion, enhancement, and noise reduction.
    """

    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """
        Convert PIL Image to OpenCV format (BGR numpy array).

        Args:
            pil_image: PIL Image object

        Returns:
            OpenCV image as numpy array in BGR format
        """
        # Convert PIL to RGB numpy array
        rgb_array = np.array(pil_image.convert('RGB'))
        # Convert RGB to BGR for OpenCV
        bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        return bgr_array

    @staticmethod
    def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
        """
        Convert OpenCV image (BGR numpy array) to PIL Image.

        Args:
            cv2_image: OpenCV image as numpy array in BGR format

        Returns:
            PIL Image object
        """
        # Convert BGR to RGB
        rgb_array = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        # Convert to PIL Image
        return Image.fromarray(rgb_array)

    @staticmethod
    def preprocess_for_detection(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply standard preprocessing pipeline for detection.

        This method prepares the image for various detection algorithms by
        applying noise reduction and normalization.

        Args:
            image: Input image as BGR numpy array

        Returns:
            Tuple of (grayscale_image, color_image) both preprocessed
        """
        # Make a copy to avoid modifying original
        color_image = image.copy()

        # Apply slight Gaussian blur to reduce noise
        color_image = cv2.GaussianBlur(color_image, (3, 3), 0)

        # Convert to grayscale for template and contour detection
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        gray_image = ImagePreprocessor.enhance_contrast(gray_image)

        return gray_image, color_image

    @staticmethod
    def enhance_contrast(image: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE or histogram equalization for better feature detection.

        Args:
            image: Grayscale image as numpy array

        Returns:
            Contrast-enhanced grayscale image
        """
        # Create CLAHE object
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        # Apply CLAHE
        enhanced = clahe.apply(image)

        return enhanced

    @staticmethod
    def prepare_for_color_detection(image: np.ndarray) -> np.ndarray:
        """
        Convert to HSV color space for color-based detection.

        HSV (Hue, Saturation, Value) color space is better for color-based
        detection as it separates color information from brightness.

        Args:
            image: BGR image as numpy array

        Returns:
            Image in HSV color space
        """
        # Apply slight blur to reduce noise
        blurred = cv2.GaussianBlur(image, (5, 5), 0)

        # Convert to HSV
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        return hsv

    @staticmethod
    def normalize_brightness(image: np.ndarray) -> np.ndarray:
        """
        Normalize brightness of the image.

        Args:
            image: Grayscale or color image

        Returns:
            Brightness-normalized image
        """
        # Convert to LAB color space if color image
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)

            # Merge channels
            lab = cv2.merge([l, a, b])

            # Convert back to BGR
            normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # For grayscale, apply histogram equalization
            normalized = cv2.equalizeHist(image)

        return normalized

    @staticmethod
    def resize_image(
        image: np.ndarray,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        scale_factor: Optional[float] = None
    ) -> np.ndarray:
        """
        Resize image while maintaining aspect ratio.

        Args:
            image: Input image
            max_width: Maximum width (optional)
            max_height: Maximum height (optional)
            scale_factor: Scale factor (optional, overrides max dimensions)

        Returns:
            Resized image
        """
        height, width = image.shape[:2]

        if scale_factor is not None:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
        else:
            # Calculate scale to fit within max dimensions
            scale_w = max_width / width if max_width else 1.0
            scale_h = max_height / height if max_height else 1.0
            scale = min(scale_w, scale_h, 1.0)  # Don't upscale

            new_width = int(width * scale)
            new_height = int(height * scale)

        # Resize with high-quality interpolation
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

        return resized

    @staticmethod
    def denoise_image(image: np.ndarray, strength: int = 10) -> np.ndarray:
        """
        Apply denoising to reduce image noise.

        Args:
            image: Input image (BGR or grayscale)
            strength: Denoising strength (default: 10)

        Returns:
            Denoised image
        """
        if len(image.shape) == 3:
            # Color image
            denoised = cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
        else:
            # Grayscale image
            denoised = cv2.fastNlMeansDenoising(image, None, strength, 7, 21)

        return denoised

    @staticmethod
    def detect_edges(image: np.ndarray, low_threshold: int = 50, high_threshold: int = 150) -> np.ndarray:
        """
        Detect edges using Canny edge detector.

        Args:
            image: Grayscale image
            low_threshold: Lower threshold for edge detection
            high_threshold: Upper threshold for edge detection

        Returns:
            Edge map as binary image
        """
        edges = cv2.Canny(image, low_threshold, high_threshold)
        return edges
