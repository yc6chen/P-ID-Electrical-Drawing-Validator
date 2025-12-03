"""Utility functions for the Drawing Validator application."""

from pathlib import Path
from typing import Optional


def validate_file_path(filepath: str) -> bool:
    """
    Validate that a file path exists and is accessible.

    Args:
        filepath: Path to validate

    Returns:
        True if the path exists and is a file, False otherwise
    """
    try:
        path = Path(filepath)
        return path.exists() and path.is_file()
    except Exception:
        return False


def get_safe_filename(filepath: str) -> str:
    """
    Extract just the filename from a path safely.

    Args:
        filepath: Full path to file

    Returns:
        Just the filename portion
    """
    try:
        return Path(filepath).name
    except Exception:
        return "Unknown"


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
