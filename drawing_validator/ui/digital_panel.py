"""
Digital signature results display panel.

This module provides UI components for displaying digital signature
validation results.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Dict


class DigitalSignaturePanel(ttk.Frame):
    """Panel for displaying digital signature validation results."""

    def __init__(self, parent):
        """
        Initialize digital signature panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._create_widgets()
        self._layout_widgets()

    def _create_widgets(self):
        """Create panel widgets."""
        # Title
        self.title_label = ttk.Label(
            self,
            text="Digital Signature Validation",
            font=("Helvetica", 12, "bold")
        )

        # Results frame
        self.results_frame = ttk.LabelFrame(self, text="Validation Results", padding=10)

        # Status labels
        self.status_label = ttk.Label(
            self.results_frame,
            text="No digital signatures checked",
            font=("Helvetica", 10)
        )

        # Signature count
        self.sig_count_label = ttk.Label(
            self.results_frame,
            text="Signatures found: 0"
        )

        # Trust status
        self.trust_status_label = ttk.Label(
            self.results_frame,
            text="Trust status: Unknown"
        )

        # Associations
        self.associations_label = ttk.Label(
            self.results_frame,
            text="Associations: None"
        )

        # Details text area
        self.details_text = scrolledtext.ScrolledText(
            self.results_frame,
            height=10,
            width=50,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.details_text.config(state=tk.DISABLED)

    def _layout_widgets(self):
        """Layout panel widgets."""
        self.title_label.pack(pady=5)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status_label.pack(anchor=tk.W, pady=2)
        self.sig_count_label.pack(anchor=tk.W, pady=2)
        self.trust_status_label.pack(anchor=tk.W, pady=2)
        self.associations_label.pack(anchor=tk.W, pady=2)

        ttk.Separator(self.results_frame, orient=tk.HORIZONTAL).pack(
            fill=tk.X, pady=5
        )

        ttk.Label(self.results_frame, text="Details:").pack(anchor=tk.W)
        self.details_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def display_results(self, digital_validation: Optional[Dict]):
        """
        Display digital signature validation results.

        Args:
            digital_validation: Dictionary with digital signature validation results
        """
        if not digital_validation:
            self._clear_results()
            return

        # Update status
        if digital_validation.get('signatures_found', False):
            total = digital_validation.get('total_signatures', 0)
            valid = digital_validation.get('valid_signatures', 0)
            invalid = digital_validation.get('invalid_signatures', 0)

            status_text = f"Found {total} digital signature{'s' if total != 1 else ''}"
            if digital_validation.get('all_signatures_valid', False):
                status_text += " (All valid)"
                self.status_label.config(foreground="green")
            elif valid > 0:
                status_text += f" ({valid} valid, {invalid} invalid)"
                self.status_label.config(foreground="orange")
            else:
                status_text += " (None valid)"
                self.status_label.config(foreground="red")

            self.status_label.config(text=status_text)

            # Signature count
            self.sig_count_label.config(
                text=f"Signatures found: {total} (Valid: {valid}, Invalid: {invalid})"
            )

            # Trust status
            trust_status = digital_validation.get('trust_status', 'unknown')
            trust_text = f"Trust status: {trust_status.replace('_', ' ').title()}"

            trust_color = {
                'fully_trusted': 'green',
                'partially_trusted': 'orange',
                'untrusted': 'red',
                'no_signatures': 'gray',
                'unknown': 'gray'
            }.get(trust_status, 'black')

            self.trust_status_label.config(text=trust_text, foreground=trust_color)

            # Associations
            associations = digital_validation.get('certificate_associations', [])
            if associations:
                assoc_text = f"Associations: {', '.join(associations)}"
                self.associations_label.config(text=assoc_text, foreground="blue")
            else:
                self.associations_label.config(
                    text="Associations: None found",
                    foreground="gray"
                )

            # Details
            self._display_details(digital_validation)

        else:
            self.status_label.config(
                text="No digital signatures found",
                foreground="gray"
            )
            self.sig_count_label.config(text="Signatures found: 0")
            self.trust_status_label.config(
                text="Trust status: No signatures",
                foreground="gray"
            )
            self.associations_label.config(text="Associations: N/A", foreground="gray")
            self._clear_details()

    def _display_details(self, digital_validation: Dict):
        """
        Display detailed signature information.

        Args:
            digital_validation: Digital signature validation results
        """
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)

        details = []
        details.append("=" * 50)
        details.append("DIGITAL SIGNATURE DETAILS")
        details.append("=" * 50)
        details.append("")

        signatures = digital_validation.get('signatures', [])

        for i, sig in enumerate(signatures, 1):
            details.append(f"Signature #{i}")
            details.append("-" * 30)
            details.append(f"  Type: {sig.get('signature_type', 'Unknown')}")

            if sig.get('signer_name'):
                details.append(f"  Signer: {sig['signer_name']}")

            if sig.get('signer_email'):
                details.append(f"  Email: {sig['signer_email']}")

            if sig.get('signing_time'):
                details.append(f"  Signed: {sig['signing_time']}")

            if sig.get('location'):
                details.append(f"  Location: {sig['location']}")

            if sig.get('reason'):
                details.append(f"  Reason: {sig['reason']}")

            details.append(f"  Valid: {'Yes' if sig.get('signature_valid', False) else 'No'}")

            if sig.get('certificate_subject'):
                details.append(f"  Certificate: {sig['certificate_subject']}")

            details.append("")

        self.details_text.insert(1.0, "\n".join(details))
        self.details_text.config(state=tk.DISABLED)

    def _clear_results(self):
        """Clear all results."""
        self.status_label.config(
            text="No digital signatures checked",
            foreground="black"
        )
        self.sig_count_label.config(text="Signatures found: 0")
        self.trust_status_label.config(
            text="Trust status: Unknown",
            foreground="black"
        )
        self.associations_label.config(
            text="Associations: None",
            foreground="black"
        )
        self._clear_details()

    def _clear_details(self):
        """Clear details text."""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.config(state=tk.DISABLED)
