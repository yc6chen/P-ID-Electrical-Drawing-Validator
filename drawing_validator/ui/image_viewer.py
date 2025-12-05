"""Image viewer widget for displaying PDF pages and images."""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
from typing import Optional, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ImageViewer(ttk.Frame):
    """
    A widget for displaying images in the application.

    This widget provides a canvas for displaying PIL Images with proper
    scaling and positioning. Enhanced in Phase 2 to display detection bounding boxes.
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
        self.detection_regions: List = []  # Store detection regions
        self.display_detections: bool = True  # Toggle for showing detections

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

    def display_image_with_detections(
        self,
        image: Image.Image,
        detection_regions: List = None
    ) -> None:
        """
        Display an image with detection bounding boxes overlaid.

        Args:
            image: PIL Image to display
            detection_regions: List of DetectedRegion objects (optional)
        """
        if image is None:
            self.clear()
            return

        # Store detection regions
        self.detection_regions = detection_regions or []

        # Create a copy of the image to draw on
        display_image = image.copy()

        # Draw detection bounding boxes if enabled and regions exist
        if self.display_detections and self.detection_regions:
            display_image = self._draw_detection_boxes(display_image, self.detection_regions)

        # Display the image with overlays
        self.display_image(display_image)

    def _draw_detection_boxes(
        self,
        image: Image.Image,
        regions: List
    ) -> Image.Image:
        """
        Draw bounding boxes on the image for detected regions.

        Args:
            image: PIL Image to draw on
            regions: List of DetectedRegion objects

        Returns:
            Image with bounding boxes drawn
        """
        # Create a drawing context
        draw = ImageDraw.Draw(image)

        # Color scheme for different detection methods
        colors = {
            'template_matching': '#00FF00',  # Green
            'contour_detection': '#0000FF',  # Blue
            'color_detection': '#FF0000'     # Red
        }

        for region in regions:
            # Get color based on detection method
            color = colors.get(region.detection_method, '#FFFF00')

            # Draw rectangle
            x1, y1, x2, y2 = region.bbox
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

            # Prepare label
            label = f"{region.detection_method[:4]}: {region.confidence:.2f}"
            if hasattr(region, 'template_name') and region.template_name:
                label = f"{region.template_name}: {region.confidence:.2f}"
            elif hasattr(region, 'color') and region.color:
                label = f"{region.color}: {region.confidence:.2f}"

            # Draw label background and text
            try:
                # Calculate text size (approximate)
                text_bbox = draw.textbbox((x1, y1 - 20), label)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                # Draw label background
                draw.rectangle(
                    [x1, y1 - text_height - 4, x1 + text_width + 4, y1],
                    fill=color,
                    outline=color
                )

                # Draw label text
                draw.text((x1 + 2, y1 - text_height - 2), label, fill='white')
            except Exception:
                # Fallback if text drawing fails
                draw.text((x1, y1 - 20), label, fill=color)

        return image

    def toggle_detections(self) -> None:
        """Toggle the display of detection bounding boxes."""
        self.display_detections = not self.display_detections

        # Redraw current image if it exists
        if self.current_image and self.detection_regions:
            self.display_image_with_detections(self.current_image, self.detection_regions)

    def clear_detections(self) -> None:
        """Clear detection overlays from the current display."""
        self.detection_regions = []
        if self.current_image:
            self.display_image(self.current_image)

    def get_detection_count(self) -> int:
        """Get the number of detected regions currently displayed."""
        return len(self.detection_regions)
