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
from core.config_manager import ConfigManager
from core.performance_cache import ProcessingCache
from ui.main_window import MainWindow
from ui.file_browser import FileBrowser
from ui.settings_dialog import SettingsDialog
from utils.helpers import get_safe_filename
from detection.seal_detector import SealDetector
from ocr.text_extractor import OCRTextExtractor
from validation.association_validator import AssociationValidator
from validation.validation_models import RegionValidation, PageValidationResult, DrawingValidationResult
from navigation.page_navigator import PageNavigator
from batch.batch_processor import BatchProcessor
from export.report_generator import ReportGenerator
from export.csv_exporter import CSVExporter


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

        # Phase 4: Configuration and performance
        self.config_manager = ConfigManager()
        self.app_config = self.config_manager.get_config()
        self.cache = ProcessingCache(max_size=self.app_config.cache_size) if self.app_config.enable_cache else None

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

        # Phase 4: Navigation, batch processing, and export
        self.page_navigator = PageNavigator()
        self.page_navigator.on_page_changed = self._on_page_changed
        self.batch_processor = BatchProcessor(max_workers=self.app_config.batch_max_workers)
        self.report_generator = ReportGenerator()
        self.csv_exporter = CSVExporter()

        # Current document state
        self.current_document: Optional[Dict] = None
        self.detection_results = None  # Store detection results
        self.validation_results = None  # Store validation results
        self.batch_result = None  # Store batch processing results

        # Create main window UI
        self.main_window = MainWindow(
            root=self,
            on_open_file=self.open_file,
            on_process=self.process_current_file,
            on_exit=self.quit_application,
            on_batch_process=self.open_batch_processing,
            on_export_pdf=self.export_to_pdf,
            on_export_csv=self.export_to_csv,
            on_settings=self.open_settings,
            on_next_page=self.next_page,
            on_prev_page=self.previous_page
        )

        # Set minimum window size
        self.minsize(800, 600)

        # Center window on screen
        self._center_window()

        # Set up window close handler
        self.protocol("WM_DELETE_WINDOW", self.quit_application)

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

        Phase 4: Enhanced with multi-page navigation support.
        """
        # Open file dialog
        filepath = self.file_browser.open_file_dialog()

        if not filepath:
            return  # User cancelled

        # Update status
        self.main_window.update_status(f"Loading: {get_safe_filename(filepath)}...")

        try:
            # Phase 4: Load with page navigator for multi-page support
            if filepath.lower().endswith('.pdf'):
                # Load multi-page PDF
                success = self.page_navigator.load_multi_page_pdf(filepath)
            else:
                # Load single image
                success = self.page_navigator.load_single_image(filepath)

            if not success:
                messagebox.showerror(
                    "Error Loading File",
                    "Failed to load file. Please check the file format."
                )
                self.main_window.update_status("Ready")
                return

            # Display first page
            first_page = self.page_navigator.get_current_page_image()
            if first_page:
                self.main_window.display_image(first_page)

                # Update status with file info
                filename = get_safe_filename(filepath)
                page_count = self.page_navigator.total_pages
                status_msg = f"Loaded: {filename} ({page_count} page{'s' if page_count != 1 else ''})"
                self.main_window.update_status(status_msg)

                # Update page navigation
                self._update_page_navigation()

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

    def _update_page_navigation(self) -> None:
        """Update page navigation UI elements."""
        page_info = self.page_navigator.get_page_info()
        self.main_window.update_page_info(page_info)
        self.main_window.enable_page_navigation(
            self.page_navigator.has_previous,
            self.page_navigator.has_next
        )

    def _on_page_changed(self, page_num: int) -> None:
        """
        Handle page change event.

        Args:
            page_num: New page number (0-indexed)
        """
        # Display new page image
        page_image = self.page_navigator.get_current_page_image()
        if page_image:
            self.main_window.display_image(page_image)

            # Display page results if available
            page_result = self.page_navigator.get_current_page_result()
            if page_result:
                # If we have detection results for this page, show them
                if page_result.region_validations:
                    import numpy as np
                    cv_image = self.image_preprocessor.pil_to_cv2(page_image)
                    regions = [rv.region for rv in page_result.region_validations]
                    self.main_window.display_image_with_detections(page_image, regions)

        # Update navigation UI
        self._update_page_navigation()

    def next_page(self) -> None:
        """Navigate to next page."""
        if self.page_navigator.next_page():
            self._update_page_navigation()

    def previous_page(self) -> None:
        """Navigate to previous page."""
        if self.page_navigator.previous_page():
            self._update_page_navigation()

    def process_current_file(self) -> None:
        """
        Process the currently loaded file with detection and validation.

        Phase 4: Enhanced to process current page from page navigator.
        """
        if not self.page_navigator.page_images:
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
            # Get the current page image
            current_page_image = self.page_navigator.get_current_page_image()
            if not current_page_image:
                messagebox.showerror(
                    "Error",
                    "No image available for detection."
                )
                self.main_window.update_status("Ready")
                return

            # Convert PIL Image to OpenCV format
            import numpy as np
            cv_image = self.image_preprocessor.pil_to_cv2(current_page_image)

            # Run detection
            print("\n" + "=" * 70)
            print("SEAL DETECTION")
            print("=" * 70)

            current_page_num = self.page_navigator.current_page
            detection_result = self.seal_detector.detect(cv_image, page_num=current_page_num)
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

            # OCR and Validation
            region_validations = []
            if detection_result.regions and self.validation_enabled:
                print("\n" + "=" * 70)
                print("OCR & VALIDATION")
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
                page_result = PageValidationResult(
                    page_number=current_page_num,
                    region_validations=region_validations,
                    has_valid_signature=any(rv.is_valid_signature for rv in region_validations),
                    processing_time=time.time()
                )
                self.validation_results = page_result

                # Store result in page navigator
                self.page_navigator.set_page_result(current_page_num, page_result)

            # Display image with detection overlays
            if detection_result.regions:
                self.main_window.display_image_with_detections(
                    current_page_image,
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

    def open_batch_processing(self) -> None:
        """Open batch processing dialog."""
        from tkinter import filedialog
        from ui.batch_panel import BatchProcessingPanel

        # Create batch processing window
        batch_window = tk.Toplevel(self)
        batch_window.title("Batch Processing")
        batch_window.geometry("700x600")
        batch_window.transient(self)

        # Create batch panel
        batch_panel = BatchProcessingPanel(
            batch_window,
            self.batch_processor,
            self._process_file_for_batch
        )
        batch_panel.pack(fill=tk.BOTH, expand=True)

        # Store batch result when window closes
        def on_close():
            self.batch_result = batch_panel.get_batch_result()
            batch_window.destroy()

        batch_window.protocol("WM_DELETE_WINDOW", on_close)

    def _process_file_for_batch(self, filepath: str):
        """
        Process a single file for batch processing.

        Args:
            filepath: Path to file to process

        Returns:
            DrawingValidationResult
        """
        try:
            # Load file with page navigator
            if filepath.lower().endswith('.pdf'):
                success = self.page_navigator.load_multi_page_pdf(filepath)
            else:
                success = self.page_navigator.load_single_image(filepath)

            if not success:
                return None

            # Process all pages
            all_page_results = []
            for page_num in range(self.page_navigator.total_pages):
                self.page_navigator.navigate_to_page(page_num)
                page_image = self.page_navigator.get_current_page_image()

                if page_image and self.detection_enabled and self.validation_enabled:
                    # Convert and detect
                    cv_image = self.image_preprocessor.pil_to_cv2(page_image)
                    detection_result = self.seal_detector.detect(cv_image, page_num)

                    # Validate regions
                    region_validations = []
                    for region in detection_result.regions:
                        roi = region.extract_roi(cv_image)
                        ocr_result = self.ocr_extractor.extract_text_from_region(roi)

                        if ocr_result.has_text:
                            validation_result = self.association_validator.validate_text(
                                ocr_result.text, roi
                            )
                            region_validations.append(RegionValidation(
                                region=region,
                                ocr_result=ocr_result,
                                validation_result=validation_result,
                                roi_image=roi
                            ))

                    # Create page result
                    page_result = PageValidationResult(
                        page_number=page_num,
                        region_validations=region_validations,
                        has_valid_signature=any(rv.is_valid_signature for rv in region_validations),
                        processing_time=0
                    )
                    all_page_results.append(page_result)

            # Create overall result
            drawing_result = DrawingValidationResult(
                filepath=filepath,
                page_results=all_page_results,
                overall_valid=any(pr.has_valid_signature for pr in all_page_results),
                total_processing_time=0
            )

            return drawing_result

        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            return None

    def export_to_pdf(self) -> None:
        """Export validation results to PDF report."""
        if not self.batch_result and not self.validation_results:
            messagebox.showwarning(
                "No Results",
                "Please process files before exporting."
            )
            return

        from tkinter import filedialog

        # Ask for save location
        filepath = filedialog.asksaveasfilename(
            title="Save PDF Report",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if not filepath:
            return

        try:
            if self.batch_result:
                # Export batch results
                self.report_generator.generate_validation_report(self.batch_result, filepath)
            else:
                # Export single file result
                single_result = DrawingValidationResult(
                    filepath=self.page_navigator.current_filepath or "unknown",
                    page_results=[self.validation_results] if self.validation_results else [],
                    overall_valid=self.validation_results.has_valid_signature if self.validation_results else False
                )
                self.report_generator.generate_simple_report(single_result, filepath)

            messagebox.showinfo(
                "Export Complete",
                f"PDF report saved to:\n{filepath}"
            )

            # Auto-open if configured
            if self.app_config.auto_open_reports:
                import os
                import platform
                if platform.system() == 'Windows':
                    os.startfile(filepath)
                elif platform.system() == 'Darwin':
                    os.system(f'open "{filepath}"')
                else:
                    os.system(f'xdg-open "{filepath}"')

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export PDF:\n{str(e)}"
            )

    def export_to_csv(self) -> None:
        """Export validation results to CSV."""
        if not self.batch_result:
            messagebox.showwarning(
                "No Batch Results",
                "CSV export is only available for batch processing results.\n"
                "Use batch processing first, then export."
            )
            return

        from tkinter import filedialog

        # Ask for save location
        filepath = filedialog.asksaveasfilename(
            title="Save CSV Export",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not filepath:
            return

        try:
            self.csv_exporter.export_to_csv(self.batch_result, filepath)

            messagebox.showinfo(
                "Export Complete",
                f"CSV export saved to:\n{filepath}"
            )

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export CSV:\n{str(e)}"
            )

    def open_settings(self) -> None:
        """Open settings dialog."""
        settings_dialog = SettingsDialog(self, self.config_manager)
        self.wait_window(settings_dialog)

        # Reload config if changed
        if hasattr(settings_dialog, 'config_changed') and settings_dialog.config_changed:
            self.app_config = self.config_manager.get_config()

            # Update components with new config
            if self.cache:
                self.cache.resize(self.app_config.cache_size)

            messagebox.showinfo(
                "Settings Updated",
                "Settings have been updated.\n"
                "Some changes may take effect after restarting the application."
            )

    def quit_application(self) -> None:
        """Exit the application."""
        if messagebox.askokcancel("Quit", "Do you want to exit the application?"):
            self.destroy()

    def run(self) -> None:
        """Start the application main loop."""
        self.mainloop()
