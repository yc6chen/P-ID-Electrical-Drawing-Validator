"""File browser dialog utilities for selecting documents."""

from tkinter import filedialog
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.settings import SUPPORTED_EXTENSIONS


class FileBrowser:
    """
    Handles file selection dialogs for opening documents.

    Provides methods to open file dialogs with appropriate filters
    for supported file types.
    """

    @staticmethod
    def open_file_dialog() -> Optional[str]:
        """
        Open a file dialog to select a document.

        Returns:
            Path to the selected file, or None if cancelled
        """
        # Build file type filters
        filetypes = [
            ("All Supported Files", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)),
            ("PDF Files", "*.pdf"),
            ("Image Files", "*.png *.jpg *.jpeg *.tiff *.bmp"),
            ("All Files", "*.*")
        ]

        # Open file dialog
        filepath = filedialog.askopenfilename(
            title="Select Drawing File",
            filetypes=filetypes
        )

        # Return None if dialog was cancelled
        if not filepath:
            return None

        return filepath

    @staticmethod
    def open_directory_dialog() -> Optional[str]:
        """
        Open a directory dialog to select a folder.

        Returns:
            Path to the selected directory, or None if cancelled
        """
        directory = filedialog.askdirectory(
            title="Select Directory"
        )

        if not directory:
            return None

        return directory
