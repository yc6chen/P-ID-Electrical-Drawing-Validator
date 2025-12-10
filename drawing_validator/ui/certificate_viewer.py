"""
Certificate details viewer dialog.

This module provides a dialog for viewing detailed certificate information.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional


class CertificateViewerDialog(tk.Toplevel):
    """Dialog for viewing certificate details."""

    def __init__(self, parent, certificate_data: dict):
        """
        Initialize certificate viewer dialog.

        Args:
            parent: Parent window
            certificate_data: Dictionary with certificate information
        """
        super().__init__(parent)

        self.certificate_data = certificate_data

        self.title("Certificate Details")
        self.geometry("600x500")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._layout_widgets()
        self._populate_certificate_info()

        # Center dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Create dialog widgets."""
        # Title
        self.title_label = ttk.Label(
            self,
            text="X.509 Certificate Information",
            font=("Helvetica", 14, "bold")
        )

        # Notebook for tabs
        self.notebook = ttk.Notebook(self)

        # General tab
        self.general_frame = ttk.Frame(self.notebook)
        self.general_text = scrolledtext.ScrolledText(
            self.general_frame,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.general_text.config(state=tk.DISABLED)

        # Details tab
        self.details_frame = ttk.Frame(self.notebook)
        self.details_text = scrolledtext.ScrolledText(
            self.details_frame,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.details_text.config(state=tk.DISABLED)

        # Add tabs
        self.notebook.add(self.general_frame, text="General")
        self.notebook.add(self.details_frame, text="Details")

        # Close button
        self.close_button = ttk.Button(
            self,
            text="Close",
            command=self.destroy
        )

    def _layout_widgets(self):
        """Layout dialog widgets."""
        self.title_label.pack(pady=10)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.general_text.pack(fill=tk.BOTH, expand=True)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        self.close_button.pack(pady=10)

    def _populate_certificate_info(self):
        """Populate certificate information in tabs."""
        # General information
        general_info = []
        general_info.append("CERTIFICATE GENERAL INFORMATION")
        general_info.append("=" * 50)
        general_info.append("")

        if 'subject' in self.certificate_data:
            general_info.append(f"Subject: {self.certificate_data['subject']}")
        if 'issuer' in self.certificate_data:
            general_info.append(f"Issuer: {self.certificate_data['issuer']}")
        if 'valid_from' in self.certificate_data:
            general_info.append(f"Valid From: {self.certificate_data['valid_from']}")
        if 'valid_to' in self.certificate_data:
            general_info.append(f"Valid To: {self.certificate_data['valid_to']}")

        general_info.append("")
        general_info.append("VALIDATION STATUS")
        general_info.append("-" * 50)
        general_info.append(f"Chain Valid: {'Yes' if self.certificate_data.get('chain_valid', False) else 'No'}")
        general_info.append(f"Root Trusted: {'Yes' if self.certificate_data.get('root_trusted', False) else 'No'}")
        general_info.append(f"Revocation Status: {self.certificate_data.get('revocation_status', 'Unknown')}")
        general_info.append(f"Key Usage Valid: {'Yes' if self.certificate_data.get('key_usage_valid', False) else 'No'}")

        if self.certificate_data.get('association_match'):
            general_info.append("")
            general_info.append("ASSOCIATION MAPPING")
            general_info.append("-" * 50)
            general_info.append(f"Association: {self.certificate_data['association_match']}")
            general_info.append(f"Confidence: {self.certificate_data.get('association_confidence', 0):.2f}")

        self.general_text.config(state=tk.NORMAL)
        self.general_text.insert(1.0, "\n".join(general_info))
        self.general_text.config(state=tk.DISABLED)

        # Detailed information
        details_info = []
        details_info.append("CERTIFICATE DETAILED INFORMATION")
        details_info.append("=" * 50)
        details_info.append("")

        if 'chain_length' in self.certificate_data:
            details_info.append(f"Chain Length: {self.certificate_data['chain_length']}")

        if 'errors' in self.certificate_data and self.certificate_data['errors']:
            details_info.append("")
            details_info.append("ERRORS:")
            for error in self.certificate_data['errors']:
                details_info.append(f"  - {error}")

        if 'notes' in self.certificate_data and self.certificate_data['notes']:
            details_info.append("")
            details_info.append("NOTES:")
            for note in self.certificate_data['notes']:
                details_info.append(f"  - {note}")

        self.details_text.config(state=tk.NORMAL)
        self.details_text.insert(1.0, "\n".join(details_info))
        self.details_text.config(state=tk.DISABLED)
