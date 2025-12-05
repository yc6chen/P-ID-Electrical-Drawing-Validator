"""
Script to verify that engineering seal templates are loading correctly.
"""

import sys
import os

# Add drawing_validator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'drawing_validator'))

print("=" * 70)
print("TEMPLATE VERIFICATION SCRIPT")
print("=" * 70)

# Check if required libraries are installed
print("\n1. Checking dependencies...")
try:
    import cv2
    import numpy as np
    print("   ✓ OpenCV installed:", cv2.__version__)
    print("   ✓ NumPy installed:", np.__version__)
except ImportError as e:
    print(f"   ✗ Missing dependency: {e}")
    print("\n   Please install: pip install opencv-python numpy")
    sys.exit(1)

# Check if templates directory exists
print("\n2. Checking templates directory...")
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
if os.path.exists(templates_dir):
    print(f"   ✓ Templates directory found: {templates_dir}")

    # List all image files
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        import glob
        image_files.extend(glob.glob(os.path.join(templates_dir, ext)))

    print(f"   ✓ Found {len(image_files)} template image(s)")
    for img_file in image_files:
        file_size = os.path.getsize(img_file) / 1024  # KB
        print(f"      - {os.path.basename(img_file)} ({file_size:.1f} KB)")
else:
    print(f"   ✗ Templates directory not found: {templates_dir}")
    sys.exit(1)

# Try to load templates with the TemplateMatcher
print("\n3. Testing TemplateMatcher...")
try:
    from detection.template_matcher import TemplateMatcher

    matcher = TemplateMatcher(templates_dir='templates')

    template_names = matcher.get_template_names()

    if template_names:
        print(f"   ✓ Successfully loaded {len(template_names)} template(s):")

        for name in template_names:
            template = matcher.templates[name]
            height, width = template.shape[:2]
            print(f"      - {name}: {width}x{height} pixels")
    else:
        print("   ⚠ No templates were loaded!")
        print("      Check that template files are valid image formats (PNG, JPG)")

except Exception as e:
    print(f"   ✗ Error loading templates: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test the full SealDetector
print("\n4. Testing SealDetector initialization...")
try:
    from detection.seal_detector import SealDetector

    detector = SealDetector(templates_dir='templates')

    print("   ✓ SealDetector initialized successfully")
    print(f"   ✓ Detection confidence threshold: {detector.config.min_confidence}")

except Exception as e:
    print(f"   ✗ Error initializing SealDetector: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test detection on a simple test image
print("\n5. Testing detection on sample image...")
try:
    # Create a simple test image (white background)
    test_image = np.ones((800, 600, 3), dtype=np.uint8) * 255

    # Run detection
    result = detector.detect(test_image, page_num=0)

    print(f"   ✓ Detection completed successfully")
    print(f"   ✓ Processing time: {result.processing_time:.3f} seconds")
    print(f"   ✓ Detections found: {result.detection_count}")

    if result.detection_count > 0:
        print("\n   Note: Detections on blank image (likely false positives):")
        for i, region in enumerate(result.regions[:3], 1):  # Show first 3
            print(f"      {i}. {region.detection_method} at ({region.x}, {region.y}) "
                  f"- confidence: {region.confidence:.3f}")

except Exception as e:
    print(f"   ✗ Error during detection: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
print("\n✓ All checks passed!")
print(f"✓ {len(template_names)} template(s) loaded and ready for detection")
print("\nYou can now run the application:")
print("   cd drawing_validator")
print("   python main.py")
print("\nTemplates loaded:")
for name in template_names:
    print(f"   - {name}")
print("\n" + "=" * 70)
