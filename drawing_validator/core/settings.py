"""Configuration constants for the Drawing Validator application."""

from typing import List

# Supported file extensions
SUPPORTED_EXTENSIONS: List[str] = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']

# Application settings
APP_TITLE: str = "Engineering Drawing Validator - Phase 1"
APP_WIDTH: int = 1200
APP_HEIGHT: int = 700

# PDF rendering settings
PDF_DPI: int = 150  # DPI for rendering PDF pages to images
