"""Main window layout and UI components."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from .image_viewer import ImageViewer


class MainWindow:
    """
    Builds and manages the main application window layout.

    Creates the menu bar, toolbar, side panel, main content area,
    and status bar.
    """

    def __init__(
        self,
        root: tk.Tk,
        on_open_file: Callable,
        on_process: Callable,
        on_exit: Callable
    ):
        """
        Initialize the main window layout.

        Args:
            root: Root Tkinter window
            on_open_file: Callback for opening files
            on_process: Callback for processing current file
            on_exit: Callback for exiting application
        """
        self.root = root
        self.on_open_file = on_open_file
        self.on_process = on_process
        self.on_exit = on_exit

        # Create components
        self._create_menu_bar()
        self._create_toolbar()
        self._create_main_layout()
        self._create_status_bar()

    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open File...", command=self.on_open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        # View Menu (stubs for Phase 2)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self._stub_zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self._stub_zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Fit to Window", command=self._stub_fit_window, accelerator="Ctrl+0")
        menubar.add_cascade(label="View", menu=view_menu)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.on_open_file())
        self.root.bind('<Control-q>', lambda e: self.on_exit())

    def _create_toolbar(self) -> None:
        """Create the toolbar with action buttons."""
        toolbar = ttk.Frame(self.root, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # Open File button
        self.open_button = ttk.Button(
            toolbar,
            text="Open File",
            command=self.on_open_file
        )
        self.open_button.pack(side=tk.LEFT, padx=2, pady=2)

        # Process button
        self.process_button = ttk.Button(
            toolbar,
            text="Process",
            command=self.on_process,
            state=tk.DISABLED
        )
        self.process_button.pack(side=tk.LEFT, padx=2, pady=2)

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)

    def _create_main_layout(self) -> None:
        """Create the main content layout with side panel and viewer."""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left side panel
        self._create_side_panel(main_container)

        # Right main viewer area
        self.image_viewer = ImageViewer(main_container)
        main_container.add(self.image_viewer, weight=3)

    def _create_side_panel(self, parent: ttk.PanedWindow) -> None:
        """
        Create the left side panel.

        Args:
            parent: Parent widget for the side panel
        """
        side_panel = ttk.Frame(parent, width=200)

        # Label
        label = ttk.Label(side_panel, text="Document Pages", font=("Arial", 10, "bold"))
        label.pack(side=tk.TOP, pady=5)

        # Listbox for pages (will be populated in Phase 2)
        self.pages_listbox = tk.Listbox(
            side_panel,
            height=20,
            selectmode=tk.SINGLE
        )
        self.pages_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(side_panel, orient=tk.VERTICAL, command=self.pages_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pages_listbox.config(yscrollcommand=scrollbar.set)

        # Add placeholder text
        self.pages_listbox.insert(tk.END, "No document loaded")
        self.pages_listbox.config(state=tk.DISABLED)

        parent.add(side_panel, weight=1)

    def _create_status_bar(self) -> None:
        """Create the status bar at the bottom of the window."""
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message: str) -> None:
        """
        Update the status bar text.

        Args:
            message: Message to display in status bar
        """
        self.status_bar.config(text=message)
        self.root.update_idletasks()

    def enable_process_button(self, enabled: bool = True) -> None:
        """
        Enable or disable the process button.

        Args:
            enabled: Whether to enable the button
        """
        self.process_button.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def display_image(self, image) -> None:
        """
        Display an image in the viewer.

        Args:
            image: PIL Image to display
        """
        self.image_viewer.display_image(image)

    def clear_image(self) -> None:
        """Clear the current image from the viewer."""
        self.image_viewer.clear()

    # Stub methods for Phase 2 features
    def _stub_zoom_in(self) -> None:
        """Stub for zoom in functionality."""
        messagebox.showinfo("Phase 2 Feature", "Zoom In will be implemented in Phase 2")

    def _stub_zoom_out(self) -> None:
        """Stub for zoom out functionality."""
        messagebox.showinfo("Phase 2 Feature", "Zoom Out will be implemented in Phase 2")

    def _stub_fit_window(self) -> None:
        """Stub for fit to window functionality."""
        messagebox.showinfo("Phase 2 Feature", "Fit to Window will be implemented in Phase 2")

    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Engineering Drawing Validator - Phase 1\n\n"
            "A tool for validating P&ID and electrical drawings\n"
            "for P.Eng signatures from Canadian engineering associations.\n\n"
            "Phase 1: Foundation & Basic UI"
        )
