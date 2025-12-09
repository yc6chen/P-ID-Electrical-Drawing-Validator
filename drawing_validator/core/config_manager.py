"""
Configuration manager for user settings and application preferences.
"""

import json
import os
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessorConfig:
    """Configuration for processing engine."""

    # Processing mode
    processing_mode: str = "Balanced"  # Fast, Balanced, Accurate, Thorough

    # Performance settings
    parallel_processing: bool = True
    max_workers: int = 2
    processing_dpi: int = 150

    # Cache settings
    enable_cache: bool = True
    cache_size: int = 100

    # OCR settings
    primary_ocr_engine: str = "tesseract"  # tesseract or easyocr
    ocr_language: str = "eng"

    # Detection settings
    template_confidence_threshold: float = 0.65
    contour_min_area: float = 500
    color_min_area: float = 300

    # Batch settings
    batch_max_workers: int = 2
    batch_auto_save: bool = True

    # Export settings
    export_format: str = "pdf"  # pdf, csv, both
    auto_open_reports: bool = False

    # UI settings
    theme: str = "default"
    show_tooltips: bool = True
    confirm_batch_operations: bool = True


class ConfigManager:
    """Manages application configuration and user settings."""

    def __init__(self, config_file: str = "config.json"):
        """
        Initialize config manager.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = ProcessorConfig()

        # Load existing config if available
        self.load_config()

    def load_config(self) -> ProcessorConfig:
        """
        Load configuration from file.

        Returns:
            ProcessorConfig object
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_dict = json.load(f)

                # Update config from file
                for key, value in config_dict.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

                logger.info(f"Loaded configuration from {self.config_file}")

            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
                logger.info("Using default configuration")

        return self.config

    def save_config(self, config: ProcessorConfig = None) -> bool:
        """
        Save configuration to file.

        Args:
            config: ProcessorConfig to save (uses current if None)

        Returns:
            True if successful
        """
        if config:
            self.config = config

        try:
            config_dict = asdict(self.config)

            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=4)

            logger.info(f"Saved configuration to {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False

    def get_config(self) -> ProcessorConfig:
        """Get current configuration."""
        return self.config

    def update_config(self, **kwargs) -> bool:
        """
        Update configuration with new values.

        Args:
            **kwargs: Configuration parameters to update

        Returns:
            True if successful
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    logger.debug(f"Updated config: {key} = {value}")
                else:
                    logger.warning(f"Unknown config parameter: {key}")

            return self.save_config()

        except Exception as e:
            logger.error(f"Error updating config: {str(e)}")
            return False

    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values.

        Returns:
            True if successful
        """
        try:
            self.config = ProcessorConfig()
            return self.save_config()

        except Exception as e:
            logger.error(f"Error resetting config: {str(e)}")
            return False

    def export_config(self, filepath: str) -> bool:
        """
        Export configuration to a file.

        Args:
            filepath: Path to export file

        Returns:
            True if successful
        """
        try:
            config_dict = asdict(self.config)

            with open(filepath, 'w') as f:
                json.dump(config_dict, f, indent=4)

            logger.info(f"Exported configuration to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error exporting config: {str(e)}")
            return False

    def import_config(self, filepath: str) -> bool:
        """
        Import configuration from a file.

        Args:
            filepath: Path to import file

        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r') as f:
                config_dict = json.load(f)

            # Update config from imported file
            for key, value in config_dict.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            # Save the imported config
            self.save_config()

            logger.info(f"Imported configuration from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error importing config: {str(e)}")
            return False

    def get_processing_mode_settings(self, mode: str) -> Dict[str, Any]:
        """
        Get optimal settings for a processing mode.

        Args:
            mode: Processing mode (Fast, Balanced, Accurate, Thorough)

        Returns:
            Dictionary of settings for the mode
        """
        modes = {
            "Fast": {
                "processing_dpi": 100,
                "max_workers": 4,
                "template_confidence_threshold": 0.7,
                "primary_ocr_engine": "tesseract"
            },
            "Balanced": {
                "processing_dpi": 150,
                "max_workers": 2,
                "template_confidence_threshold": 0.65,
                "primary_ocr_engine": "tesseract"
            },
            "Accurate": {
                "processing_dpi": 200,
                "max_workers": 2,
                "template_confidence_threshold": 0.6,
                "primary_ocr_engine": "easyocr"
            },
            "Thorough": {
                "processing_dpi": 300,
                "max_workers": 1,
                "template_confidence_threshold": 0.5,
                "primary_ocr_engine": "easyocr"
            }
        }

        return modes.get(mode, modes["Balanced"])
