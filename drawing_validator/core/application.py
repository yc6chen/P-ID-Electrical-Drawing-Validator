"""Main application class for the Drawing Validator."""

import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pdf_processor import PDFProcessor
from core.settings import APP_TITLE, APP_WIDTH, APP_HEIGHT
from core.image_processor import ImagePreprocessor
from ui.main_window import MainWindow
from ui.file_browser import FileBrowser
from utils.helpers import get_safe_filename
from detection.seal_detector import SealDetector
from ocr.text_extractor import OCRTextExtractor
from validation.association_validator import AssociationValidator
from validation.validation_models import RegionValidation, PageValidationResult


class DrawingValidatorApp(tk.Tk):
    """
    Main application class for the Engineering Drawing Validator.

    This class manages the application window, document processing,
    and user interactions.
    """

    def __init__(self):
        """Initialize the Drawing Validator application."""
        super().__init__()

        # Set window properties
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")

        # Initialize components
        self.pdf_processor = PDFProcessor()
        self.file_browser = FileBrowser()
        self.image_preprocessor = ImagePreprocessor()

        # Initialize detection engine (Phase 2)
        try:
            self.seal_detector = SealDetector()
            self.detection_enabled = True
        except Exception as e:
            print(f"Warning: Could not initialize seal detector: {e}")
            print("Detection features will be disabled.")
            self.seal_detector = None
            self.detection_enabled = False

        # Initialize OCR and validation engines (Phase 3)
        try:
            self.ocr_extractor = OCRTextExtractor(use_easyocr_fallback=True)
            self.association_validator = AssociationValidator()
            self.validation_enabled = True
        except Exception as e:
            print(f"Warning: Could not initialize OCR/validation: {e}")
            print("Validation features will be disabled.")
            self.ocr_extractor = None
            self.association_validator = None
            self.validation_enabled = False

        # Current document state
        self.current_document: Optional[Dict] = None
        self.detection_results = None  # Store detection results
        self.validation_results = None  # Store validation results

        # Create main window UI
        self.main_window = MainWindow(
            root=self,
            on_open_file=self.open_file,
            on_process=self.process_current_file,
            on_exit=self.quit_application
        )

        # Set minimum window size
        self.minsize(800, 600)

        # Center window on screen
        self._center_window()

        # Set status
        self.main_window.update_status("Ready")

    def _center_window(self) -> None:
        """Center the application window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def open_file(self) -> None:
        """
        Open a file dialog and load the selected document.

        This method handles the file selection, loading, and display
        of the first page.
        """
        # Open file dialog
        filepath = self.file_browser.open_file_dialog()

        if not filepath:
            return  # User cancelled

        # Update status
        self.main_window.update_status(f"Loading: {get_safe_filename(filepath)}...")

        try:
            # Load document using PDF processor
            result = self.pdf_processor.load_document(filepath)

            # Check for errors
            if result['error']:
                messagebox.showerror(
                    "Error Loading File",
                    f"Failed to load file:\n{result['error']}"
                )
                self.main_window.update_status("Ready")
                return

            # Store document data
            self.current_document = result

            # Display first page image
            if result['first_page_image']:
                self.main_window.display_image(result['first_page_image'])

                # Update status with file info
                filename = get_safe_filename(filepath)
                page_count = result['page_count']
                status_msg = f"Loaded: {filename} ({page_count} page{'s' if page_count != 1 else ''})"
                self.main_window.update_status(status_msg)

                # Enable process button
                self.main_window.enable_process_button(True)
            else:
                messagebox.showwarning(
                    "Warning",
                    "File loaded but no image could be extracted."
                )
                self.main_window.update_status("Ready")

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Unexpected error while loading file:\n{str(e)}"
            )
            self.main_window.update_status("Ready")

    def process_current_file(self) -> None:
        """
        Process the currently loaded file with Phase 2 detection.

        This method runs the detection engine to find engineering seals
        and signatures in the loaded document.
        """
        if not self.current_document:
            messagebox.showwarning(
                "No Document",
                "Please load a document first."
            )
            return

        # Check if detection is enabled
        if not self.detection_enabled or not self.seal_detector:
            messagebox.showwarning(
                "Detection Unavailable",
                "Detection engine is not available.\n"
                "Please ensure OpenCV and NumPy are installed:\n"
                "pip install opencv-python numpy"
            )
            return

        # Update status
        self.main_window.update_status("Running seal detection...")

        try:
            # Get the first page image
            first_page_image = self.current_document.get('first_page_image')
            if not first_page_image:
                messagebox.showerror(
                    "Error",
                    "No image available for detection."
                )
                self.main_window.update_status("Ready")
                return

            # Convert PIL Image to OpenCV format
            import numpy as np
            cv_image = self.image_preprocessor.pil_to_cv2(first_page_image)

            # Run detection
            print("\n" + "=" * 70)
            print("PHASE 2: SEAL DETECTION")
            print("=" * 70)

            detection_result = self.seal_detector.detect(cv_image, page_num=0)
            self.detection_results = detection_result

            # Print detection summary
            summary = self.seal_detector.get_detection_summary(detection_result)
            print(f"\nDetection Summary:")
            print(f"  - Total detections: {summary['total_detections']}")
            print(f"  - Processing time: {summary['processing_time']:.2f}s")
            print(f"  - Image dimensions: {summary['image_dimensions']}")

            print(f"\nDetections by method:")
            for method, count in summary['by_method'].items():
                if count > 0:
                    print(f"  - {method}: {count}")

            print(f"\nDetections by confidence:")
            for level, count in summary['by_confidence'].items():
                if count > 0:
                    print(f"  - {level}: {count}")

            # Print individual detections
            if detection_result.regions:
                print(f"\nDetailed Detection Results:")
                print("-" * 70)
                for i, region in enumerate(detection_result.regions, 1):
                    print(f"\n{i}. Region at ({region.x}, {region.y}) "
                          f"[{region.width}x{region.height}]")
                    print(f"   Method: {region.detection_method}")
                    print(f"   Confidence: {region.confidence:.3f}")
                    if region.template_name:
                        print(f"   Template: {region.template_name}")
                    if region.color:
                        print(f"   Color: {region.color}")
                print("-" * 70)
            else:
                print("\nNo seal or signature regions detected.")

            print("\n" + "=" * 70)
            print("END OF DETECTION OUTPUT")
            print("=" * 70 + "\n")

            # PHASE 3: OCR and Validation
            region_validations = []
            if detection_result.regions and self.validation_enabled:
                print("\n" + "=" * 70)
                print("PHASE 3: OCR & VALIDATION")
                print("=" * 70)

                self.main_window.update_status("Running OCR and validation...")

                for i, region in enumerate(detection_result.regions, 1):
                    print(f"\nProcessing Region {i}/{len(detection_result.regions)}...")

                    # Extract ROI
                    roi = region.extract_roi(cv_image)

                    # Run OCR
                    ocr_result = self.ocr_extractor.extract_text_from_region(roi)
                    print(f"  OCR Engine: {ocr_result.engine_used}")
                    print(f"  Extracted Text: {ocr_result.text[:100]}..." if len(ocr_result.text) > 100 else f"  Extracted Text: {ocr_result.text}")
                    print(f"  OCR Confidence: {ocr_result.confidence:.3f}")

                    # Run validation if text was extracted
                    if ocr_result.has_text:
                        validation_result = self.association_validator.validate_text(
                            ocr_result.text, roi
                        )
                        print(f"  Validation: {'VALID' if validation_result.valid else 'INVALID'}")
                        print(f"  Confidence: {validation_result.confidence:.3f}")
                        if validation_result.associations:
                            print(f"  Associations: {', '.join(validation_result.associations)}")
                        if validation_result.license_numbers:
                            print(f"  License Numbers: {', '.join(validation_result.license_numbers)}")

                        region_validations.append(RegionValidation(
                            region=region,
                            ocr_result=ocr_result,
                            validation_result=validation_result,
                            roi_image=roi
                        ))

                print("\n" + "=" * 70)
                print("END OF VALIDATION OUTPUT")
                print("=" * 70 + "\n")

                # Create page validation result
                import time
                self.validation_results = PageValidationResult(
                    page_number=0,
                    region_validations=region_validations,
                    has_valid_signature=any(rv.is_valid_signature for rv in region_validations),
                    processing_time=time.time()
                )

            # Display image with detection overlays
            if detection_result.regions:
                self.main_window.display_image_with_detections(
                    first_page_image,
                    detection_result.regions
                )

                # Prepare status message
                if region_validations:
                    valid_count = sum(1 for rv in region_validations if rv.is_valid_signature)
                    status_msg = f"Complete: {len(detection_result.regions)} regions, {valid_count} valid signature(s)"
                else:
                    status_msg = f"Detection complete: {len(detection_result.regions)} region(s) found"

                self.main_window.update_status(status_msg)

                # Show completion message with results
                if region_validations:
                    valid_count = sum(1 for rv in region_validations if rv.is_valid_signature)
                    messagebox.showinfo(
                        "Processing Complete",
                        f"Detection: {len(detection_result.regions)} region(s) found\n"
                        f"Validation: {valid_count} valid signature(s)\n\n"
                        f"Processing time: {detection_result.processing_time:.2f}s\n"
                        f"Check the console for detailed results."
                    )
                else:
                    messagebox.showinfo(
                        "Detection Complete",
                        f"Found {len(detection_result.regions)} potential seal/signature region(s).\n\n"
                        f"Processing time: {detection_result.processing_time:.2f}s\n"
                        f"Check the console for detailed results."
                    )
            else:
                self.main_window.update_status("Detection complete: No seals found")
                messagebox.showinfo(
                    "Detection Complete",
                    "No engineering seals or signatures detected.\n\n"
                    "This could mean:\n"
                    "- The document has no seals\n"
                    "- The seals don't match the templates\n"
                    "- Try adjusting detection parameters"
                )

        except Exception as e:
            print(f"\nError during detection: {e}")
            import traceback
            traceback.print_exc()

            messagebox.showerror(
                "Detection Error",
                f"An error occurred during detection:\n{str(e)}\n\n"
                "Check the console for details."
            )
            self.main_window.update_status("Detection failed")

    def quit_application(self) -> None:
        """Exit the application."""
        if messagebox.askokcancel("Quit", "Do you want to exit the application?"):
            self.destroy()

    def run(self) -> None:
        """Start the application main loop."""
        self.mainloop()
