# P&ID Electrical Drawing Validator

A Python desktop application that validates P&ID and electrical drawings for P.Eng signatures from specific Canadian engineering associations (APEGA, APEGS, EGBC, Engineers Geoscientists Manitoba).

## Current Status: Phase 2 Complete ✅

The application now includes a fully functional **Detection Engine** that can automatically identify engineering seals and signature regions in drawings.

## Features

### Phase 1: Foundation ✅
- Desktop UI with Tkinter
- PDF and image file loading (PDF, PNG, JPG, TIFF)
- Multi-page document support
- Image display with zoom and pan capabilities
- File metadata extraction

### Phase 2: Detection Engine ✅
- **Template Matching**: Detects known engineering seal patterns using multi-scale template matching
- **Contour Detection**: Identifies rectangular signature blocks using shape analysis
- **Color-Based Detection**: Finds colored engineering seals (red, blue, green, black)
- **Visual Overlay**: Displays detected regions with colored bounding boxes and confidence scores
- **ROI Extraction**: Isolates detected regions for future OCR processing (Phase 3)
- **Multiple Detection Methods**: Combines results from all detection algorithms for comprehensive coverage

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd P-ID-Electrical-Drawing-Validator
```

2. Install dependencies:
```bash
cd drawing_validator
pip install -r requirements.txt
```

3. (Optional) Create template images:
```bash
python ../create_placeholder_templates.py
```

## Usage

### Running the Application

```bash
cd drawing_validator
python main.py
```

### Using the Detection Engine

1. **Open a Document**: Click "Open File" or use File > Open File (Ctrl+O)
   - Supported formats: PDF, PNG, JPG, JPEG, TIFF

2. **Run Detection**: Click the "Process" button in the toolbar

3. **View Results**:
   - Detected seals and signatures are highlighted with colored bounding boxes:
     - **Green**: Template matches (known seals)
     - **Blue**: Contour detections (signature blocks)
     - **Red**: Color-based detections (colored seals)
   - Confidence scores are displayed above each detection
   - Detailed results are printed to the console

### Detection Methods

#### Template Matching
- Matches known engineering seal patterns from the `templates/` directory
- Multi-scale detection (50%-150% of template size)
- Configurable confidence threshold (default: 0.65)

#### Contour Detection
- Finds rectangular regions typical of signature blocks
- Analyzes shape properties: area, aspect ratio, rectangularity
- Ideal for detecting hand-drawn or stamped signature areas

#### Color Detection
- Identifies seals by their distinctive colors
- Supports red, blue, green, and black engineering seals
- HSV color space filtering for robust color detection

## Project Structure

```
drawing_validator/
├── core/
│   ├── application.py          # Main application class
│   ├── pdf_processor.py        # PDF/image loading
│   ├── image_processor.py      # Image preprocessing
│   └── settings.py             # Configuration
├── detection/                  # Phase 2: Detection module
│   ├── seal_detector.py        # Main detection orchestrator
│   ├── template_matcher.py    # Template matching
│   ├── contour_detector.py    # Contour/shape detection
│   ├── color_detector.py      # Color-based detection
│   ├── region_processor.py    # ROI extraction
│   └── detection_models.py    # Data models
├── ui/
│   ├── main_window.py          # Main UI layout
│   ├── image_viewer.py         # Enhanced image viewer
│   └── file_browser.py         # File selection dialog
├── tests/
│   └── test_detection.py       # Unit tests
├── main.py                     # Application entry point
└── requirements.txt            # Dependencies

templates/                      # Engineering seal templates
├── apega_seal_placeholder.png
├── egbc_seal_placeholder.png
└── ...
```

## Configuration

### Detection Parameters

Edit detection settings in `drawing_validator/detection/detection_models.py`:

```python
class DetectionConfig:
    # Template matching
    template_confidence_threshold: float = 0.65
    template_scale_range: tuple = (0.5, 1.5)

    # Contour detection
    contour_min_area: float = 500
    contour_max_area: float = 10000

    # Color detection
    color_min_area: float = 300
    color_max_area: float = 5000
```

### Adding Custom Templates

1. Extract clear images of engineering seals
2. Save as PNG files in the `templates/` directory
3. Recommended size: 80-150 pixels for circular seals
4. Templates are automatically loaded on startup

## Testing

Run unit tests:
```bash
cd drawing_validator
python -m pytest tests/test_detection.py -v
```

Or:
```bash
python tests/test_detection.py
```

## Roadmap

### Phase 3: OCR & Text Extraction (Upcoming)
- Tesseract OCR integration
- Text extraction from detected regions
- Engineer name and license number parsing
- Association identifier extraction

### Phase 4: Validation & Verification (Upcoming)
- Association database lookup
- License number validation
- Multi-page batch processing
- Validation report generation
- Export results to PDF/CSV

## Dependencies

- **pymupdf** (>=1.24.0): PDF processing
- **Pillow** (>=10.0.0): Image handling
- **pypdf** (>=3.17.0): PDF metadata
- **opencv-python** (>=4.8.0): Computer vision and detection
- **numpy** (>=1.24.0): Numerical operations

## Troubleshooting

### Detection Not Working
- Ensure OpenCV and NumPy are installed: `pip install opencv-python numpy`
- Check console for error messages
- Verify templates exist in `templates/` directory

### No Detections Found
- The document may not contain engineering seals
- Seals may not match the templates
- Try adjusting detection parameters in `DetectionConfig`
- Check if seal colors match the configured HSV ranges

### Performance Issues
- Large images (>5000x5000) may take longer to process
- Consider reducing image resolution before detection
- Template matching with many templates can be slow

## License

[License information to be added]

## Contributing

[Contributing guidelines to be added]

## Support

For issues or questions, please open an issue on GitHub.
