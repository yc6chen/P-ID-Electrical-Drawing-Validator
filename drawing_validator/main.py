"""
Engineering Drawing Validator - Phase 1
Main entry point for the application.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.application import DrawingValidatorApp


def main():
    """Launch the Drawing Validator application."""
    try:
        app = DrawingValidatorApp()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
