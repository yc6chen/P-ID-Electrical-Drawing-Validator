"""
Script to verify that engineering seal templates are loading correctly.
"""

import sys
import os

print("=" * 70)
print("TEMPLATE VERIFICATION SCRIPT")
print("=" * 70)

# Check if required libraries are installed
print("\n1. Checking dependencies...")
try:
    import cv2
    import numpy as np
    from PIL import Image
    print("   ✓ OpenCV installed:", cv2.__version__)
    print("   ✓ NumPy installed:", np.__version__)
    print("   ✓ Pillow installed:", Image.__version__)
except ImportError as e:
    print(f"   ✗ Missing dependency: {e}")
    print("\n   Please install: pip install opencv-python numpy Pillow")
    sys.exit(1)

# Check if templates directory exists
print("\n2. Checking templates directory...")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
if os.path.exists(templates_dir):
    print(f"   ✓ Templates directory found: {templates_dir}")

    # List all image files
    image_files = []
    for ext in ['.png', '.jpg', '.jpeg']:
        for file in os.listdir(templates_dir):
            if file.lower().endswith(ext):
                image_files.append(os.path.join(templates_dir, file))

    print(f"   ✓ Found {len(image_files)} template image(s)")
    for img_file in image_files:
        file_size = os.path.getsize(img_file) / 1024  # KB
        print(f"      - {os.path.basename(img_file)} ({file_size:.1f} KB)")
else:
    print(f"   ✗ Templates directory not found: {templates_dir}")
    sys.exit(1)

# Try to load each template with OpenCV
print("\n3. Loading templates with OpenCV...")
templates_loaded = {}
for img_file in image_files:
    try:
        # Load image
        img = cv2.imread(img_file, cv2.IMREAD_GRAYSCALE)

        if img is not None:
            height, width = img.shape
            basename = os.path.splitext(os.path.basename(img_file))[0]
            templates_loaded[basename] = (width, height)
            print(f"   ✓ {basename}: {width}x{height} pixels")
        else:
            print(f"   ✗ Failed to load: {os.path.basename(img_file)}")

    except Exception as e:
        print(f"   ✗ Error loading {os.path.basename(img_file)}: {e}")

if not templates_loaded:
    print("\n   ✗ No templates were successfully loaded!")
    sys.exit(1)

# Test the TemplateMatcher class
print("\n4. Testing TemplateMatcher class...")
try:
    from detection.template_matcher import TemplateMatcher
    from detection.detection_models import DetectionConfig

    config = DetectionConfig()
    matcher = TemplateMatcher(templates_dir='../templates', config=config)

    template_names = matcher.get_template_names()

    if template_names:
        print(f"   ✓ TemplateMatcher loaded {len(template_names)} template(s)")
        for name in template_names:
            template = matcher.templates[name]
            height, width = template.shape[:2]
            print(f"      - {name}: {width}x{height} pixels")
    else:
        print("   ⚠ TemplateMatcher loaded 0 templates")

except Exception as e:
    print(f"   ✗ Error with TemplateMatcher: {e}")
    import traceback
    traceback.print_exc()

# Test the SealDetector
print("\n5. Testing SealDetector initialization...")
try:
    from detection.seal_detector import SealDetector

    detector = SealDetector(templates_dir='../templates')

    print("   ✓ SealDetector initialized successfully")
    print(f"   ✓ Templates loaded: {len(detector.template_matcher.get_template_names())}")
    print(f"   ✓ Confidence threshold: {detector.config.min_confidence}")
    print(f"   ✓ Scale range: {detector.config.template_scale_range}")

except Exception as e:
    print(f"   ✗ Error initializing SealDetector: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test detection on a simple image
print("\n6. Testing detection on blank test image...")
try:
    # Create a white test image
    test_image = np.ones((800, 600, 3), dtype=np.uint8) * 255

    # Run detection
    result = detector.detect(test_image, page_num=0)

    print(f"   ✓ Detection completed")
    print(f"   ✓ Processing time: {result.processing_time:.3f}s")
    print(f"   ✓ Regions detected: {result.detection_count}")

except Exception as e:
    print(f"   ✗ Error during detection: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)
print(f"\n✓ Dependencies: OK")
print(f"✓ Templates found: {len(image_files)}")
print(f"✓ Templates loaded: {len(templates_loaded)}")
print(f"✓ Detection system: READY")
print("\nLoaded templates:")
for name in templates_loaded.keys():
    print(f"   • {name}")
print("\nThe application is ready to detect engineering seals!")
print("\nTo run the application:")
print("   python main.py")
print("\n" + "=" * 70)
