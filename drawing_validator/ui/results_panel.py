"""
Tkinter panel for displaying validation results.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class ValidationResultsPanel(tk.Frame):
    """
    Panel for displaying OCR and validation results.

    Shows extracted text, associations, license numbers, and validation status.
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize the validation results panel.

        Args:
            parent: Parent widget
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        self.configure(bg='white', relief=tk.RAISED, borderwidth=1)

        self.validation_results = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        # Title
        title_label = tk.Label(
            self,
            text="Validation Results",
            font=("Arial", 14, "bold"),
            bg='white'
        )
        title_label.pack(pady=10)

        # Results container with scrollbar
        results_frame = tk.Frame(self, bg='white')
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Canvas for scrolling
        self.canvas = tk.Canvas(results_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            results_frame,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg='white')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def display_results(self, validation_results):
        """
        Display validation results in the panel.

        Args:
            validation_results: PageValidationResult object
        """
        self.validation_results = validation_results

        # Clear previous results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not validation_results or not validation_results.region_validations:
            no_results = tk.Label(
                self.scrollable_frame,
                text="No signatures detected or validated",
                font=("Arial", 10),
                bg='white',
                fg='gray'
            )
            no_results.pack(pady=20)
            return

        # Overall page status
        page_status = "VALID" if validation_results.has_valid_signature else "INVALID"
        status_color = "green" if validation_results.has_valid_signature else "red"

        status_frame = tk.Frame(self.scrollable_frame, bg='white')
        status_frame.pack(fill=tk.X, pady=(0, 10))

        status_label = tk.Label(
            status_frame,
            text=f"Page Status: {page_status}",
            font=("Arial", 12, "bold"),
            bg='white',
            fg=status_color
        )
        status_label.pack(side=tk.LEFT)

        # Display each region validation
        for i, region_validation in enumerate(validation_results.region_validations):
            self._display_region_validation(region_validation, i)

    def _display_region_validation(self, region_validation, index: int):
        """
        Display validation for a single region.

        Args:
            region_validation: RegionValidation object
            index: Region index
        """
        frame = tk.Frame(
            self.scrollable_frame,
            bg='#f5f5f5',
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.pack(fill=tk.X, pady=5, padx=5)

        # Header with region number
        header_frame = tk.Frame(frame, bg='#e0e0e0')
        header_frame.pack(fill=tk.X, padx=2, pady=2)

        header_label = tk.Label(
            header_frame,
            text=f"Region {index + 1}",
            font=("Arial", 10, "bold"),
            bg='#e0e0e0'
        )
        header_label.pack(side=tk.LEFT, padx=5)

        # Validation status
        valid = region_validation.validation_result.valid
        status_text = "VALID" if valid else "INVALID"
        status_color = "green" if valid else "red"

        status_label = tk.Label(
            header_frame,
            text=status_text,
            font=("Arial", 10, "bold"),
            bg='#e0e0e0',
            fg=status_color
        )
        status_label.pack(side=tk.RIGHT, padx=5)

        # Confidence score
        confidence = region_validation.validation_result.confidence
        confidence_label = tk.Label(
            header_frame,
            text=f"Confidence: {confidence:.2%}",
            font=("Arial", 9),
            bg='#e0e0e0'
        )
        confidence_label.pack(side=tk.RIGHT, padx=10)

        # Details section
        details_frame = tk.Frame(frame, bg='white')
        details_frame.pack(fill=tk.X, padx=10, pady=10)

        # Extracted text (truncated if long)
        extracted_text = region_validation.ocr_result.text
        if len(extracted_text) > 100:
            display_text = extracted_text[:100] + "..."
        else:
            display_text = extracted_text

        text_label = tk.Label(
            details_frame,
            text=f"Extracted Text: {display_text}",
            font=("Arial", 9),
            bg='white',
            wraplength=400,
            justify=tk.LEFT
        )
        text_label.pack(anchor=tk.W, pady=2)

        # Associations found
        if region_validation.validation_result.associations:
            assoc_text = ", ".join(region_validation.validation_result.associations)
            assoc_label = tk.Label(
                details_frame,
                text=f"Associations: {assoc_text}",
                font=("Arial", 9),
                bg='white',
                fg='blue'
            )
            assoc_label.pack(anchor=tk.W, pady=2)

        # License numbers
        if region_validation.validation_result.license_numbers:
            license_text = ", ".join(region_validation.validation_result.license_numbers)
            license_label = tk.Label(
                details_frame,
                text=f"License(s): {license_text}",
                font=("Arial", 9),
                bg='white',
                fg='darkgreen'
            )
            license_label.pack(anchor=tk.W, pady=2)

        # OCR engine info
        engine_label = tk.Label(
            details_frame,
            text=f"OCR Engine: {region_validation.ocr_result.engine_used}",
            font=("Arial", 8),
            bg='white',
            fg='gray'
        )
        engine_label.pack(anchor=tk.W, pady=2)

    def clear(self):
        """Clear the results panel."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.validation_results = None
