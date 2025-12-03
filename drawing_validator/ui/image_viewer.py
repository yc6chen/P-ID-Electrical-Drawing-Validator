"""Image viewer widget for displaying PDF pages and images."""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from typing import Optional


class ImageViewer(ttk.Frame):
    """
    A widget for displaying images in the application.

    This widget provides a canvas for displaying PIL Images with proper
    scaling and positioning.
    """

    def __init__(self, parent: tk.Widget):
        """
        Initialize the ImageViewer.

        Args:
            parent: Parent Tkinter widget
        """
        super().__init__(parent)

        self.current_image: Optional[Image.Image] = None
        self.photo_image: Optional[ImageTk.PhotoImage] = None

        # Create canvas for image display
        self.canvas = tk.Canvas(
            self,
            bg='#f0f0f0',
            highlightthickness=1,
            highlightbackground='#cccccc'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Add scrollbars
        self.v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Image ID on canvas
        self.image_id: Optional[int] = None

        # Placeholder text
        self.placeholder_text = self.canvas.create_text(
            0, 0,
            text="No document loaded\nUse File > Open File to load a document",
            font=("Arial", 12),
            fill='#666666',
            justify=tk.CENTER
        )
        self._center_placeholder()

        # Bind resize event
        self.canvas.bind('<Configure>', self._on_resize)

    def display_image(self, image: Image.Image) -> None:
        """
        Display an image in the viewer.

        Args:
            image: PIL Image to display
        """
        if image is None:
            self.clear()
            return

        self.current_image = image

        # Remove placeholder if it exists
        if self.placeholder_text:
            self.canvas.delete(self.placeholder_text)
            self.placeholder_text = None

        # Convert PIL Image to PhotoImage
        self.photo_image = ImageTk.PhotoImage(image)

        # Display on canvas
        if self.image_id:
            self.canvas.delete(self.image_id)

        self.image_id = self.canvas.create_image(
            0, 0,
            anchor=tk.NW,
            image=self.photo_image
        )

        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))

    def clear(self) -> None:
        """Clear the current image and show placeholder."""
        if self.image_id:
            self.canvas.delete(self.image_id)
            self.image_id = None

        self.current_image = None
        self.photo_image = None

        if not self.placeholder_text:
            self.placeholder_text = self.canvas.create_text(
                0, 0,
                text="No document loaded\nUse File > Open File to load a document",
                font=("Arial", 12),
                fill='#666666',
                justify=tk.CENTER
            )
        self._center_placeholder()

    def _center_placeholder(self) -> None:
        """Center the placeholder text in the canvas."""
        if self.placeholder_text:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Use default size if window hasn't been drawn yet
            if canvas_width <= 1:
                canvas_width = 800
            if canvas_height <= 1:
                canvas_height = 600

            self.canvas.coords(
                self.placeholder_text,
                canvas_width // 2,
                canvas_height // 2
            )

    def _on_resize(self, event) -> None:
        """Handle canvas resize events."""
        if self.placeholder_text and not self.current_image:
            self._center_placeholder()
