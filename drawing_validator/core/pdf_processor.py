"""PDF and image processing module for the Drawing Validator application."""

from pathlib import Path
from typing import Dict, Optional
import io

try:
    import fitz  # PyMuPDF
    from PIL import Image
    import pypdf
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    raise

from .settings import SUPPORTED_EXTENSIONS, PDF_DPI


class PDFProcessor:
    """
    Handles loading and processing of PDF and image files.

    This class provides methods to load documents, extract pages as images,
    and retrieve metadata for validation purposes.
    """

    def load_document(self, filepath: str) -> Dict:
        """
        Load a document (PDF or image) and extract relevant information.

        Args:
            filepath: Path to the file to load

        Returns:
            Dictionary containing:
                - filepath (str): The path to the loaded file
                - page_count (int): Number of pages (1 for images)
                - first_page_image (PIL.Image): First page as an image
                - source_text (str): Text extracted from first page
                - error (str or None): Error message if loading failed
        """
        filepath_obj = Path(filepath)

        # Initialize result dictionary
        result = {
            'filepath': str(filepath),
            'page_count': 0,
            'first_page_image': None,
            'source_text': '',
            'error': None
        }

        try:
            # Check if file exists
            if not filepath_obj.exists():
                result['error'] = f"File not found: {filepath}"
                return result

            # Check file extension
            ext = filepath_obj.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                result['error'] = f"Unsupported file format: {ext}"
                return result

            # Process based on file type
            if ext == '.pdf':
                return self._load_pdf(filepath, result)
            else:
                return self._load_image(filepath, result)

        except Exception as e:
            result['error'] = f"Error loading file: {str(e)}"
            return result

    def _load_pdf(self, filepath: str, result: Dict) -> Dict:
        """
        Load a PDF file and extract information.

        Args:
            filepath: Path to the PDF file
            result: Result dictionary to populate

        Returns:
            Updated result dictionary
        """
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(filepath)

            # Get page count
            result['page_count'] = len(doc)

            if result['page_count'] == 0:
                result['error'] = "PDF contains no pages"
                return result

            # Load first page
            page = doc.load_page(0)

            # Extract text from first page
            result['source_text'] = page.get_text()

            # Render first page as image at specified DPI
            # Create transformation matrix for desired DPI
            zoom = PDF_DPI / 72  # 72 is the default DPI
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Convert PyMuPDF pixmap to PIL Image
            img_data = pix.tobytes("png")
            result['first_page_image'] = Image.open(io.BytesIO(img_data))

            doc.close()

        except Exception as e:
            result['error'] = f"Error processing PDF: {str(e)}"

        return result

    def _load_image(self, filepath: str, result: Dict) -> Dict:
        """
        Load an image file.

        Args:
            filepath: Path to the image file
            result: Result dictionary to populate

        Returns:
            Updated result dictionary
        """
        try:
            # Open image with PIL
            img = Image.open(filepath)

            # Set page count to 1 for images
            result['page_count'] = 1
            result['first_page_image'] = img
            result['source_text'] = ''  # No text extraction for images in Phase 1

        except Exception as e:
            result['error'] = f"Error loading image: {str(e)}"

        return result

    def get_document_metadata(self, filepath: str) -> Dict:
        """
        Extract metadata from a PDF document using pypdf.

        Args:
            filepath: Path to the PDF file

        Returns:
            Dictionary containing metadata (author, title, subject, etc.)
        """
        metadata = {
            'author': None,
            'title': None,
            'subject': None,
            'creator': None,
            'producer': None,
            'creation_date': None,
            'modification_date': None,
            'error': None
        }

        try:
            filepath_obj = Path(filepath)

            # Only process PDFs
            if filepath_obj.suffix.lower() != '.pdf':
                metadata['error'] = "Not a PDF file"
                return metadata

            # Read PDF with pypdf
            with open(filepath, 'rb') as file:
                reader = pypdf.PdfReader(file)

                # Extract metadata if available
                if reader.metadata:
                    metadata['author'] = reader.metadata.get('/Author')
                    metadata['title'] = reader.metadata.get('/Title')
                    metadata['subject'] = reader.metadata.get('/Subject')
                    metadata['creator'] = reader.metadata.get('/Creator')
                    metadata['producer'] = reader.metadata.get('/Producer')
                    metadata['creation_date'] = reader.metadata.get('/CreationDate')
                    metadata['modification_date'] = reader.metadata.get('/ModDate')

        except Exception as e:
            metadata['error'] = f"Error extracting metadata: {str(e)}"

        return metadata
