# P&ID Electrical Drawing Validator

A Python desktop application that validates P&ID and electrical drawings for P.Eng signatures from specific Canadian engineering associations (APEGA, APEGS, EGBC, Engineers Geoscientists Manitoba).

## Current Status: Phase 4 Complete ✅

The application is now **production-ready** with comprehensive batch processing, multi-page navigation, export functionality, and deployment packaging.

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
- **ROI Extraction**: Isolates detected regions for OCR processing
- **Multiple Detection Methods**: Combines results from all detection algorithms for comprehensive coverage

### Phase 3: OCR & Validation ✅
- **Dual OCR Engines**: Tesseract and EasyOCR with automatic fallback
- **Text Extraction**: Extracts text from detected seal/signature regions
- **Association Validation**: Validates P.Eng signatures against Canadian associations (APEGA, APEGS, EGBC, Engineers Geoscientists Manitoba)
- **License Number Detection**: Identifies and extracts P.Eng license numbers
- **Confidence Scoring**: Provides confidence scores for validation results
- **Multi-Engine Support**: Automatically switches between OCR engines for best results

### Phase 4: Production Features ✅
- **Multi-Page Navigation**: Navigate through multi-page PDFs with page controls
- **Batch Processing**: Process multiple files in one operation with progress tracking
- **Export & Reporting**: Generate PDF reports and CSV exports of validation results
- **Performance Optimization**: Multi-threading, caching, and memory management
- **User Settings**: Configurable processing parameters saved between sessions
- **Deployment Packaging**: PyInstaller scripts for standalone executables

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
│   ├── config_manager.py       # Phase 4: User settings management
│   ├── performance_cache.py    # Phase 4: Caching system
│   └── settings.py             # Configuration
├── detection/                  # Phase 2: Detection module
│   ├── seal_detector.py        # Main detection orchestrator
│   ├── template_matcher.py    # Template matching
│   ├── contour_detector.py    # Contour/shape detection
│   ├── color_detector.py      # Color-based detection
│   ├── region_processor.py    # ROI extraction
│   └── detection_models.py    # Data models
├── ocr/                        # Phase 3: OCR module
│   ├── text_extractor.py       # Main OCR orchestrator
│   ├── ocr_engines.py          # OCR engine wrappers
│   ├── ocr_models.py           # OCR data models
│   └── text_preprocessor.py   # Text preprocessing
├── validation/                 # Phase 3: Validation module
│   ├── association_validator.py  # P.Eng association validation
│   ├── confidence_scorer.py    # Confidence scoring
│   └── validation_models.py    # Validation data models
├── batch/                      # Phase 4: Batch processing
│   ├── batch_processor.py      # Batch orchestration
│   └── batch_models.py         # Batch data models
├── export/                     # Phase 4: Export module
│   ├── report_generator.py     # PDF report generation
│   └── csv_exporter.py         # CSV export
├── navigation/                 # Phase 4: Multi-page navigation
│   └── page_navigator.py       # Page navigation controls
├── ui/
│   ├── main_window.py          # Main UI layout
│   ├── image_viewer.py         # Enhanced image viewer
│   ├── results_panel.py        # Results display
│   ├── batch_panel.py          # Phase 4: Batch processing panel
│   ├── settings_dialog.py      # Phase 4: Settings dialog
│   └── file_browser.py         # File selection dialog
├── deployment/                 # Phase 4: Deployment
│   ├── build_spec.py           # PyInstaller spec
│   └── README_DEPLOYMENT.md    # Deployment guide
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

## Advanced Features

### Batch Processing
1. **Add Files**: Click "Add Files" or "Add Folder" in the Batch panel
2. **Process**: Click "Process Batch" to validate all files
3. **Progress Tracking**: Monitor real-time progress with cancel capability
4. **Results**: View comprehensive batch summary after processing

### Multi-Page PDFs
- Automatically loads all pages from PDF documents
- Navigate using page controls
- Process all pages with one click
- View page-specific validation results

### Export & Reporting
- **PDF Reports**: Generate professional validation reports with detailed results
- **CSV Export**: Export results to CSV for database import or analysis
- **Batch Summaries**: Get statistics across all processed files
- Access export options from the File menu

### Settings & Configuration
- **Processing Mode**: Fast, Balanced, Accurate, or Thorough
- **OCR Engine**: Choose between Tesseract or EasyOCR
- **Performance**: Configure caching, threading, and DPI settings
- **Export Options**: Set default export formats and auto-save preferences
- Access settings from Tools > Settings menu

## Dependencies

### Core Dependencies
- **pymupdf** (>=1.23.0): PDF processing
- **Pillow** (>=10.0.0): Image handling
- **opencv-python** (>=4.8.0): Computer vision and detection
- **numpy** (>=1.24.0): Numerical operations

### Phase 3 Dependencies
- **pytesseract** (>=0.3.10): OCR engine wrapper
- **easyocr** (>=1.6.2): Alternative OCR engine

### Phase 4 Dependencies
- **reportlab** (>=4.0.0): PDF report generation
- **pandas** (>=2.0.0): CSV export and data manipulation

### Optional
- **pyinstaller** (>=5.0.0): Application packaging for deployment

**Note**: Tesseract-OCR must be installed separately on the system:
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

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
