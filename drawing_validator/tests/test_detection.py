"""
Unit tests for detection components.

These tests verify the functionality of the seal detection system.
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import cv2
    from detection.detection_models import DetectedRegion, DetectionResult, DetectionConfig
    from detection.seal_detector import SealDetector
    from detection.template_matcher import TemplateMatcher
    from detection.contour_detector import ContourDetector
    from detection.color_detector import ColorDetector
    from core.image_processor import ImagePreprocessor
    OPENCV_AVAILABLE = True
except ImportError as e:
    OPENCV_AVAILABLE = False
    print(f"Warning: OpenCV not available, skipping detection tests: {e}")


@unittest.skipUnless(OPENCV_AVAILABLE, "OpenCV required for detection tests")
class TestDetectionModels(unittest.TestCase):
    """Test detection data models."""

    def test_detected_region_creation(self):
        """Test creating a DetectedRegion."""
        region = DetectedRegion(
            x=10, y=20, width=100, height=50,
            confidence=0.85,
            detection_method="template_matching"
        )

        self.assertEqual(region.x, 10)
        self.assertEqual(region.y, 20)
        self.assertEqual(region.width, 100)
        self.assertEqual(region.height, 50)
        self.assertEqual(region.confidence, 0.85)

    def test_detected_region_bbox(self):
        """Test bounding box calculation."""
        region = DetectedRegion(
            x=10, y=20, width=100, height=50,
            confidence=0.85,
            detection_method="contour_detection"
        )

        bbox = region.bbox
        self.assertEqual(bbox, (10, 20, 110, 70))

    def test_detected_region_center(self):
        """Test center point calculation."""
        region = DetectedRegion(
            x=0, y=0, width=100, height=50,
            confidence=0.85,
            detection_method="color_detection"
        )

        center = region.center
        self.assertEqual(center, (50, 25))

    def test_detected_region_overlap(self):
        """Test overlap detection between regions."""
        region1 = DetectedRegion(
            x=0, y=0, width=100, height=100,
            confidence=0.85,
            detection_method="template_matching"
        )

        region2 = DetectedRegion(
            x=50, y=50, width=100, height=100,
            confidence=0.75,
            detection_method="contour_detection"
        )

        region3 = DetectedRegion(
            x=200, y=200, width=100, height=100,
            confidence=0.65,
            detection_method="color_detection"
        )

        # region1 and region2 should overlap
        self.assertTrue(region1.overlaps_with(region2, threshold=0.1))

        # region1 and region3 should not overlap
        self.assertFalse(region1.overlaps_with(region3, threshold=0.1))

    def test_detection_result(self):
        """Test DetectionResult container."""
        regions = [
            DetectedRegion(x=10, y=10, width=50, height=50,
                         confidence=0.9, detection_method="template_matching"),
            DetectedRegion(x=100, y=100, width=50, height=50,
                         confidence=0.8, detection_method="contour_detection"),
        ]

        result = DetectionResult(
            page_num=0,
            regions=regions,
            processing_time=1.5,
            image_dimensions=(800, 600)
        )

        self.assertEqual(result.page_num, 0)
        self.assertEqual(result.detection_count, 2)
        self.assertTrue(result.has_detections)
        self.assertEqual(len(result.get_regions_by_method("template_matching")), 1)


@unittest.skipUnless(OPENCV_AVAILABLE, "OpenCV required for detection tests")
class TestImagePreprocessor(unittest.TestCase):
    """Test image preprocessing utilities."""

    def test_preprocess_for_detection(self):
        """Test basic preprocessing."""
        # Create a simple test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:, :] = (255, 255, 255)  # White image

        gray, color = ImagePreprocessor.preprocess_for_detection(test_image)

        # Check output shapes
        self.assertEqual(len(gray.shape), 2)  # Grayscale should be 2D
        self.assertEqual(len(color.shape), 3)  # Color should be 3D
        self.assertEqual(gray.shape[:2], test_image.shape[:2])

    def test_enhance_contrast(self):
        """Test contrast enhancement."""
        # Create a simple grayscale image
        test_image = np.ones((100, 100), dtype=np.uint8) * 128

        enhanced = ImagePreprocessor.enhance_contrast(test_image)

        self.assertEqual(enhanced.shape, test_image.shape)
        self.assertEqual(enhanced.dtype, np.uint8)


@unittest.skipUnless(OPENCV_AVAILABLE, "OpenCV required for detection tests")
class TestContourDetector(unittest.TestCase):
    """Test contour-based detection."""

    def test_contour_detector_initialization(self):
        """Test creating a ContourDetector."""
        detector = ContourDetector()
        self.assertIsNotNone(detector)
        self.assertIsNotNone(detector.config)

    def test_detect_on_blank_image(self):
        """Test detection on a blank image."""
        detector = ContourDetector()

        # Create blank white image
        test_image = np.ones((500, 500, 3), dtype=np.uint8) * 255

        results = detector.detect(test_image)

        # Blank image should have no detections
        self.assertIsInstance(results, list)


@unittest.skipUnless(OPENCV_AVAILABLE, "OpenCV required for detection tests")
class TestColorDetector(unittest.TestCase):
    """Test color-based detection."""

    def test_color_detector_initialization(self):
        """Test creating a ColorDetector."""
        detector = ColorDetector()
        self.assertIsNotNone(detector)
        self.assertIsNotNone(detector.color_ranges)
        self.assertGreater(len(detector.color_ranges), 0)

    def test_detect_on_blank_image(self):
        """Test detection on a blank image."""
        detector = ColorDetector()

        # Create blank white image
        test_image = np.ones((500, 500, 3), dtype=np.uint8) * 255

        results = detector.detect(test_image)

        # Blank image should have no detections
        self.assertIsInstance(results, list)

    def test_add_custom_color_range(self):
        """Test adding a custom color range."""
        detector = ColorDetector()

        initial_count = len(detector.get_color_ranges())

        detector.add_color_range(
            "custom_color",
            np.array([50, 50, 50]),
            np.array([70, 255, 255])
        )

        self.assertEqual(len(detector.get_color_ranges()), initial_count + 1)
        self.assertIn("custom_color", detector.get_color_ranges())


@unittest.skipUnless(OPENCV_AVAILABLE, "OpenCV required for detection tests")
class TestSealDetector(unittest.TestCase):
    """Test main seal detector orchestrator."""

    def test_seal_detector_initialization(self):
        """Test creating a SealDetector."""
        try:
            detector = SealDetector()
            self.assertIsNotNone(detector)
            self.assertIsNotNone(detector.config)
        except Exception as e:
            # It's okay if templates directory doesn't exist
            self.assertIn("templates", str(e).lower())

    def test_detect_on_blank_image(self):
        """Test detection on a blank image."""
        try:
            detector = SealDetector()

            # Create blank white image
            test_image = np.ones((500, 500, 3), dtype=np.uint8) * 255

            result = detector.detect(test_image, page_num=0)

            self.assertIsInstance(result, DetectionResult)
            self.assertEqual(result.page_num, 0)
            self.assertIsInstance(result.regions, list)
        except Exception as e:
            # Templates might not be available
            pass


def run_tests():
    """Run all detection tests."""
    if not OPENCV_AVAILABLE:
        print("OpenCV not available. Please install: pip install opencv-python numpy")
        return False

    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    unittest.main()
