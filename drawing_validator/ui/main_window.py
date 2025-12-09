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
        on_exit: Callable,
        on_batch_process: Optional[Callable] = None,
        on_export_pdf: Optional[Callable] = None,
        on_export_csv: Optional[Callable] = None,
        on_settings: Optional[Callable] = None,
        on_next_page: Optional[Callable] = None,
        on_prev_page: Optional[Callable] = None
    ):
        """
        Initialize the main window layout.

        Args:
            root: Root Tkinter window
            on_open_file: Callback for opening files
            on_process: Callback for processing current file
            on_exit: Callback for exiting application
            on_batch_process: Callback for batch processing
            on_export_pdf: Callback for PDF export
            on_export_csv: Callback for CSV export
            on_settings: Callback for settings dialog
            on_next_page: Callback for next page navigation
            on_prev_page: Callback for previous page navigation
        """
        self.root = root
        self.on_open_file = on_open_file
        self.on_process = on_process
        self.on_exit = on_exit
        self.on_batch_process = on_batch_process
        self.on_export_pdf = on_export_pdf
        self.on_export_csv = on_export_csv
        self.on_settings = on_settings
        self.on_next_page = on_next_page
        self.on_prev_page = on_prev_page

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

        # Phase 4: Batch Processing
        if self.on_batch_process:
            file_menu.add_command(label="Batch Processing...", command=self.on_batch_process, accelerator="Ctrl+B")
            file_menu.add_separator()

        # Phase 4: Export submenu
        export_menu = tk.Menu(file_menu, tearoff=0)
        if self.on_export_pdf:
            export_menu.add_command(label="Export to PDF Report...", command=self.on_export_pdf)
        if self.on_export_csv:
            export_menu.add_command(label="Export to CSV...", command=self.on_export_csv)
        if self.on_export_pdf or self.on_export_csv:
            file_menu.add_cascade(label="Export", menu=export_menu)
            file_menu.add_separator()

        file_menu.add_command(label="Exit", command=self.on_exit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)

        # Phase 4: Page Navigation
        if self.on_prev_page:
            view_menu.add_command(label="Previous Page", command=self.on_prev_page, accelerator="Ctrl+Left")
        if self.on_next_page:
            view_menu.add_command(label="Next Page", command=self.on_next_page, accelerator="Ctrl+Right")

        if self.on_prev_page or self.on_next_page:
            view_menu.add_separator()

        view_menu.add_command(label="Zoom In", command=self._stub_zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self._stub_zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Fit to Window", command=self._stub_fit_window, accelerator="Ctrl+0")
        menubar.add_cascade(label="View", menu=view_menu)

        # Phase 4: Tools Menu
        if self.on_settings:
            tools_menu = tk.Menu(menubar, tearoff=0)
            tools_menu.add_command(label="Settings...", command=self.on_settings, accelerator="Ctrl+,")
            menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.on_open_file())
        self.root.bind('<Control-q>', lambda e: self.on_exit())

        # Phase 4: Additional shortcuts
        if self.on_batch_process:
            self.root.bind('<Control-b>', lambda e: self.on_batch_process())
        if self.on_settings:
            self.root.bind('<Control-comma>', lambda e: self.on_settings())
        if self.on_prev_page:
            self.root.bind('<Control-Left>', lambda e: self.on_prev_page())
        if self.on_next_page:
            self.root.bind('<Control-Right>', lambda e: self.on_next_page())

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

        # Phase 4: Page Navigation buttons
        if self.on_prev_page:
            self.prev_page_button = ttk.Button(
                toolbar,
                text="◀ Prev",
                command=self.on_prev_page,
                state=tk.DISABLED
            )
            self.prev_page_button.pack(side=tk.LEFT, padx=2, pady=2)

        # Page info label
        self.page_info_var = tk.StringVar(value="")
        self.page_info_label = ttk.Label(
            toolbar,
            textvariable=self.page_info_var,
            width=15
        )
        self.page_info_label.pack(side=tk.LEFT, padx=5, pady=2)

        if self.on_next_page:
            self.next_page_button = ttk.Button(
                toolbar,
                text="Next ▶",
                command=self.on_next_page,
                state=tk.DISABLED
            )
            self.next_page_button.pack(side=tk.LEFT, padx=2, pady=2)

        # Separator
        if self.on_prev_page or self.on_next_page:
            ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)

        # Phase 4: Batch Processing button
        if self.on_batch_process:
            self.batch_button = ttk.Button(
                toolbar,
                text="Batch Process",
                command=self.on_batch_process
            )
            self.batch_button.pack(side=tk.LEFT, padx=2, pady=2)

        # Phase 4: Settings button
        if self.on_settings:
            self.settings_button = ttk.Button(
                toolbar,
                text="⚙ Settings",
                command=self.on_settings
            )
            self.settings_button.pack(side=tk.RIGHT, padx=2, pady=2)

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

    def display_image_with_detections(self, image, detection_regions) -> None:
        """
        Display an image with detection overlays.

        Args:
            image: PIL Image to display
            detection_regions: List of DetectedRegion objects
        """
        self.image_viewer.display_image_with_detections(image, detection_regions)

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
            "Engineering Drawing Validator - Phase 4 Complete\n\n"
            "A production-ready tool for validating P&ID and electrical drawings\n"
            "for P.Eng signatures from Canadian engineering associations.\n\n"
            "Features:\n"
            "✓ Multi-method detection engine\n"
            "✓ OCR & validation with dual engines\n"
            "✓ Batch processing with progress tracking\n"
            "✓ Multi-page PDF navigation\n"
            "✓ PDF & CSV export\n"
            "✓ Configurable settings\n\n"
            "Version 1.0.0"
        )

    def update_page_info(self, page_info: str) -> None:
        """
        Update page information display.

        Args:
            page_info: Page info string (e.g., "Page 1 of 5")
        """
        if hasattr(self, 'page_info_var'):
            self.page_info_var.set(page_info)

    def enable_page_navigation(self, has_prev: bool, has_next: bool) -> None:
        """
        Enable/disable page navigation buttons.

        Args:
            has_prev: Whether previous page is available
            has_next: Whether next page is available
        """
        if hasattr(self, 'prev_page_button'):
            self.prev_page_button.config(state=tk.NORMAL if has_prev else tk.DISABLED)
        if hasattr(self, 'next_page_button'):
            self.next_page_button.config(state=tk.NORMAL if has_next else tk.DISABLED)
