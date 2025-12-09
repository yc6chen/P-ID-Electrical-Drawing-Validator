"""
Configuration settings dialog for user preferences.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)


class SettingsDialog(tk.Toplevel):
    """Settings dialog for configuring application preferences."""

    def __init__(self, parent, config_manager):
        """
        Initialize settings dialog.

        Args:
            parent: Parent window
            config_manager: ConfigManager instance
        """
        super().__init__(parent)

        self.config_manager = config_manager
        self.current_config = config_manager.get_config()
        self.config_changed = False

        self.title("Settings")
        self.geometry("600x500")
        self.resizable(False, False)

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self._setup_ui()
        self._load_current_settings()

        # Center on parent
        self._center_on_parent(parent)

    def _center_on_parent(self, parent):
        """Center dialog on parent window."""
        self.update_idletasks()

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        """Setup the user interface."""

        # Create notebook for tabbed interface
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Processing tab
        processing_frame = ttk.Frame(notebook, padding=10)
        self._setup_processing_tab(processing_frame)
        notebook.add(processing_frame, text="Processing")

        # OCR tab
        ocr_frame = ttk.Frame(notebook, padding=10)
        self._setup_ocr_tab(ocr_frame)
        notebook.add(ocr_frame, text="OCR")

        # Performance tab
        performance_frame = ttk.Frame(notebook, padding=10)
        self._setup_performance_tab(performance_frame)
        notebook.add(performance_frame, text="Performance")

        # Export tab
        export_frame = ttk.Frame(notebook, padding=10)
        self._setup_export_tab(export_frame)
        notebook.add(export_frame, text="Export")

        # Button frame
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Save button
        save_btn = tk.Button(
            button_frame,
            text="Save Settings",
            command=self._save_settings,
            width=15,
            bg="#4CAF50",
            fg="white"
        )
        save_btn.pack(side=tk.RIGHT, padx=5)

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=15
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        # Reset button
        reset_btn = tk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
            width=15
        )
        reset_btn.pack(side=tk.LEFT, padx=5)

    def _setup_processing_tab(self, parent):
        """Setup processing settings tab."""

        # Processing mode
        ttk.Label(parent, text="Processing Mode:").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.processing_mode = tk.StringVar()
        mode_combo = ttk.Combobox(
            parent,
            textvariable=self.processing_mode,
            values=["Fast", "Balanced", "Accurate", "Thorough"],
            state="readonly",
            width=20
        )
        mode_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)

        # Help text for modes
        help_text = tk.Label(
            parent,
            text="Fast: Quick processing, lower accuracy\n"
                 "Balanced: Good trade-off (recommended)\n"
                 "Accurate: Slower, better accuracy\n"
                 "Thorough: Slowest, highest accuracy",
            justify=tk.LEFT,
            fg="#666",
            font=("Arial", 8)
        )
        help_text.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=30)

        # Parallel processing
        self.parallel_var = tk.BooleanVar()
        parallel_check = ttk.Checkbutton(
            parent,
            text="Enable parallel processing",
            variable=self.parallel_var
        )
        parallel_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)

        # Worker threads
        ttk.Label(parent, text="Max worker threads:").grid(
            row=3, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.threads_var = tk.IntVar()
        threads_spin = ttk.Spinbox(
            parent,
            from_=1,
            to=16,
            textvariable=self.threads_var,
            width=10
        )
        threads_spin.grid(row=3, column=1, sticky=tk.W, padx=10, pady=10)

        # Processing DPI
        ttk.Label(parent, text="Processing DPI:").grid(
            row=4, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.dpi_var = tk.IntVar()
        dpi_combo = ttk.Combobox(
            parent,
            textvariable=self.dpi_var,
            values=[100, 150, 200, 300],
            state="readonly",
            width=10
        )
        dpi_combo.grid(row=4, column=1, sticky=tk.W, padx=10, pady=10)

    def _setup_ocr_tab(self, parent):
        """Setup OCR settings tab."""

        # Primary OCR engine
        ttk.Label(parent, text="Primary OCR Engine:").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.ocr_engine_var = tk.StringVar()
        ocr_combo = ttk.Combobox(
            parent,
            textvariable=self.ocr_engine_var,
            values=["tesseract", "easyocr"],
            state="readonly",
            width=20
        )
        ocr_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)

        # Help text
        help_text = tk.Label(
            parent,
            text="Tesseract: Faster, good for typed text\n"
                 "EasyOCR: Slower, better for handwriting",
            justify=tk.LEFT,
            fg="#666",
            font=("Arial", 8)
        )
        help_text.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=30)

        # Language
        ttk.Label(parent, text="OCR Language:").grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.ocr_lang_var = tk.StringVar()
        lang_entry = ttk.Entry(
            parent,
            textvariable=self.ocr_lang_var,
            width=10
        )
        lang_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)

    def _setup_performance_tab(self, parent):
        """Setup performance settings tab."""

        # Cache settings
        self.cache_var = tk.BooleanVar()
        cache_check = ttk.Checkbutton(
            parent,
            text="Enable processing cache",
            variable=self.cache_var
        )
        cache_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)

        ttk.Label(parent, text="Cache size (items):").grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.cache_size_var = tk.IntVar()
        cache_spin = ttk.Spinbox(
            parent,
            from_=10,
            to=1000,
            textvariable=self.cache_size_var,
            width=10
        )
        cache_spin.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)

        # Batch settings
        ttk.Label(parent, text="Batch max workers:").grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.batch_workers_var = tk.IntVar()
        batch_spin = ttk.Spinbox(
            parent,
            from_=1,
            to=8,
            textvariable=self.batch_workers_var,
            width=10
        )
        batch_spin.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)

    def _setup_export_tab(self, parent):
        """Setup export settings tab."""

        # Export format
        ttk.Label(parent, text="Default Export Format:").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.export_format_var = tk.StringVar()
        format_combo = ttk.Combobox(
            parent,
            textvariable=self.export_format_var,
            values=["pdf", "csv", "both"],
            state="readonly",
            width=20
        )
        format_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)

        # Auto-open reports
        self.auto_open_var = tk.BooleanVar()
        auto_open_check = ttk.Checkbutton(
            parent,
            text="Auto-open reports after generation",
            variable=self.auto_open_var
        )
        auto_open_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)

        # Batch auto-save
        self.batch_auto_save_var = tk.BooleanVar()
        auto_save_check = ttk.Checkbutton(
            parent,
            text="Auto-save batch results",
            variable=self.batch_auto_save_var
        )
        auto_save_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)

    def _load_current_settings(self):
        """Load current settings into UI controls."""

        self.processing_mode.set(self.current_config.processing_mode)
        self.parallel_var.set(self.current_config.parallel_processing)
        self.threads_var.set(self.current_config.max_workers)
        self.dpi_var.set(self.current_config.processing_dpi)

        self.ocr_engine_var.set(self.current_config.primary_ocr_engine)
        self.ocr_lang_var.set(self.current_config.ocr_language)

        self.cache_var.set(self.current_config.enable_cache)
        self.cache_size_var.set(self.current_config.cache_size)
        self.batch_workers_var.set(self.current_config.batch_max_workers)

        self.export_format_var.set(self.current_config.export_format)
        self.auto_open_var.set(self.current_config.auto_open_reports)
        self.batch_auto_save_var.set(self.current_config.batch_auto_save)

    def _save_settings(self):
        """Save settings to config."""

        try:
            # Update config with UI values
            self.config_manager.update_config(
                processing_mode=self.processing_mode.get(),
                parallel_processing=self.parallel_var.get(),
                max_workers=self.threads_var.get(),
                processing_dpi=self.dpi_var.get(),
                primary_ocr_engine=self.ocr_engine_var.get(),
                ocr_language=self.ocr_lang_var.get(),
                enable_cache=self.cache_var.get(),
                cache_size=self.cache_size_var.get(),
                batch_max_workers=self.batch_workers_var.get(),
                export_format=self.export_format_var.get(),
                auto_open_reports=self.auto_open_var.get(),
                batch_auto_save=self.batch_auto_save_var.get()
            )

            self.config_changed = True

            messagebox.showinfo(
                "Settings Saved",
                "Settings have been saved successfully.\n\n"
                "Some changes may require restarting the application."
            )

            self.destroy()

        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to save settings:\n{str(e)}"
            )

    def _reset_defaults(self):
        """Reset all settings to defaults."""

        if messagebox.askyesno(
            "Confirm Reset",
            "Reset all settings to default values?"
        ):
            self.config_manager.reset_to_defaults()
            self.current_config = self.config_manager.get_config()
            self._load_current_settings()

            messagebox.showinfo(
                "Settings Reset",
                "All settings have been reset to defaults."
            )
