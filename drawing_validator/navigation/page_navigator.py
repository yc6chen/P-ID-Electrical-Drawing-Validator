"""
Multi-page PDF navigation system with page controls.
"""

import logging
from typing import List, Optional, Callable
import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


class PageNavigator:
    """
    Multi-page PDF navigation with page image caching and controls.

    Manages loading, caching, and navigation through multi-page PDFs.
    """

    def __init__(self, parent=None):
        """
        Initialize page navigator.

        Args:
            parent: Parent UI component (optional)
        """
        self.parent = parent
        self.current_page = 0
        self.total_pages = 0
        self.page_images = []  # List of PIL Images
        self.page_results = []  # List of PageValidationResult objects
        self.current_filepath = None

        # Callbacks
        self.on_page_changed: Optional[Callable] = None

    def load_multi_page_pdf(self, pdf_path: str, dpi: int = 150) -> bool:
        """
        Load all pages of a PDF for navigation.

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for rendering pages

        Returns:
            True if successful
        """
        try:
            logger.info(f"Loading multi-page PDF: {pdf_path}")

            # Load PDF document
            with fitz.open(pdf_path) as doc:
                self.total_pages = len(doc)
                self.page_images = []
                self.page_results = []

                # Calculate zoom factor from DPI
                zoom = dpi / 72
                matrix = fitz.Matrix(zoom, zoom)

                # Load each page
                for page_num in range(self.total_pages):
                    logger.debug(f"Loading page {page_num + 1}/{self.total_pages}")

                    # Load page
                    page = doc.load_page(page_num)

                    # Render page to pixmap
                    pix = page.get_pixmap(matrix=matrix)

                    # Convert to PIL Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # Store page image
                    self.page_images.append(img)

                # Initialize navigation
                self.current_page = 0
                self.current_filepath = pdf_path

                logger.info(f"Loaded {self.total_pages} pages from PDF")
                return True

        except Exception as e:
            logger.error(f"Error loading multi-page PDF: {str(e)}")
            return False

    def load_single_image(self, image_path: str) -> bool:
        """
        Load a single image file (non-PDF).

        Args:
            image_path: Path to image file

        Returns:
            True if successful
        """
        try:
            logger.info(f"Loading single image: {image_path}")

            # Load image
            img = Image.open(image_path)

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Store as single page
            self.page_images = [img]
            self.page_results = []
            self.total_pages = 1
            self.current_page = 0
            self.current_filepath = image_path

            logger.info("Loaded single image")
            return True

        except Exception as e:
            logger.error(f"Error loading single image: {str(e)}")
            return False

    def navigate_to_page(self, page_num: int) -> bool:
        """
        Navigate to specific page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            True if navigation successful
        """
        if not self.page_images:
            logger.warning("No document loaded")
            return False

        if 0 <= page_num < self.total_pages:
            self.current_page = page_num
            logger.info(f"Navigated to page {page_num + 1} of {self.total_pages}")

            # Trigger callback
            if self.on_page_changed:
                self.on_page_changed(page_num)

            return True
        else:
            logger.warning(f"Invalid page number: {page_num}")
            return False

    def next_page(self) -> bool:
        """Navigate to next page."""
        return self.navigate_to_page(self.current_page + 1)

    def previous_page(self) -> bool:
        """Navigate to previous page."""
        return self.navigate_to_page(self.current_page - 1)

    def first_page(self) -> bool:
        """Navigate to first page."""
        return self.navigate_to_page(0)

    def last_page(self) -> bool:
        """Navigate to last page."""
        return self.navigate_to_page(self.total_pages - 1)

    def get_current_page_image(self) -> Optional[Image.Image]:
        """
        Get current page image.

        Returns:
            PIL Image of current page, or None
        """
        if 0 <= self.current_page < len(self.page_images):
            return self.page_images[self.current_page]
        return None

    def get_page_image(self, page_num: int) -> Optional[Image.Image]:
        """
        Get specific page image.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            PIL Image, or None if invalid
        """
        if 0 <= page_num < len(self.page_images):
            return self.page_images[page_num]
        return None

    def get_all_page_images(self) -> List[Image.Image]:
        """
        Get all page images.

        Returns:
            List of PIL Images
        """
        return self.page_images.copy()

    def set_page_result(self, page_num: int, result):
        """
        Store validation result for a specific page.

        Args:
            page_num: Page number (0-indexed)
            result: PageValidationResult object
        """
        # Ensure page_results list is large enough
        while len(self.page_results) <= page_num:
            self.page_results.append(None)

        self.page_results[page_num] = result
        logger.debug(f"Stored validation result for page {page_num + 1}")

    def get_page_result(self, page_num: int):
        """
        Get validation result for a specific page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            PageValidationResult or None
        """
        if 0 <= page_num < len(self.page_results):
            return self.page_results[page_num]
        return None

    def get_current_page_result(self):
        """Get validation result for current page."""
        return self.get_page_result(self.current_page)

    def has_results(self) -> bool:
        """Check if any page has validation results."""
        return any(result is not None for result in self.page_results)

    def clear(self):
        """Clear all loaded pages and results."""
        self.page_images.clear()
        self.page_results.clear()
        self.current_page = 0
        self.total_pages = 0
        self.current_filepath = None
        logger.info("Cleared page navigator")

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.current_page > 0

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.current_page < self.total_pages - 1

    @property
    def is_first_page(self) -> bool:
        """Check if on first page."""
        return self.current_page == 0

    @property
    def is_last_page(self) -> bool:
        """Check if on last page."""
        return self.current_page == self.total_pages - 1

    def get_page_info(self) -> str:
        """
        Get page information string.

        Returns:
            String like "Page 1 of 5"
        """
        if self.total_pages == 0:
            return "No document loaded"
        return f"Page {self.current_page + 1} of {self.total_pages}"
