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
from ui.main_window import MainWindow
from ui.file_browser import FileBrowser
from utils.helpers import get_safe_filename


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

        # Current document state
        self.current_document: Optional[Dict] = None

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
        Process the currently loaded file.

        This is a placeholder for Phase 2 processing logic.
        Currently just prints the document information to the console.
        """
        if not self.current_document:
            messagebox.showwarning(
                "No Document",
                "Please load a document first."
            )
            return

        # Update status
        self.main_window.update_status("Processing document...")

        # Print document information to console
        print("\n" + "=" * 70)
        print("PROCESSING DOCUMENT - Phase 1 Output")
        print("=" * 70)

        # Print all document details
        print(f"\nFilepath: {self.current_document.get('filepath')}")
        print(f"Page Count: {self.current_document.get('page_count')}")
        print(f"Has Image: {self.current_document.get('first_page_image') is not None}")

        # Print text content (truncated)
        text = self.current_document.get('source_text', '')
        if text:
            text_preview = text[:500] + "..." if len(text) > 500 else text
            print(f"\nExtracted Text Preview:")
            print("-" * 70)
            print(text_preview)
            print("-" * 70)
        else:
            print("\nNo text extracted (image file or scanned PDF)")

        # Print error if any
        error = self.current_document.get('error')
        if error:
            print(f"\nError: {error}")

        # Try to get metadata (only for PDFs)
        if self.current_document.get('filepath', '').lower().endswith('.pdf'):
            try:
                metadata = self.pdf_processor.get_document_metadata(
                    self.current_document['filepath']
                )
                print(f"\nMetadata:")
                print("-" * 70)
                for key, value in metadata.items():
                    if value and key != 'error':
                        print(f"{key.capitalize()}: {value}")
                print("-" * 70)
            except Exception as e:
                print(f"\nCould not extract metadata: {e}")

        print("\n" + "=" * 70)
        print("END OF PROCESSING OUTPUT")
        print("=" * 70 + "\n")

        # Update status
        self.main_window.update_status("Processing complete - check console output")

        # Show completion message
        messagebox.showinfo(
            "Processing Complete",
            "Document information has been printed to the console.\n"
            "Check the terminal/console for detailed output."
        )

    def quit_application(self) -> None:
        """Exit the application."""
        if messagebox.askokcancel("Quit", "Do you want to exit the application?"):
            self.destroy()

    def run(self) -> None:
        """Start the application main loop."""
        self.mainloop()
