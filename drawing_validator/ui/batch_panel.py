"""
Tkinter panel for batch processing operations.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import logging

logger = logging.getLogger(__name__)


class BatchProcessingPanel(tk.Frame):
    """Panel for batch processing multiple files."""

    def __init__(self, parent, batch_processor, processor_func, **kwargs):
        """
        Initialize batch processing panel.

        Args:
            parent: Parent widget
            batch_processor: BatchProcessor instance
            processor_func: Function to process individual files
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)

        self.batch_processor = batch_processor
        self.processor_func = processor_func
        self.current_batch = None
        self.processing_thread = None

        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        """Setup the user interface."""

        # Title
        title_label = tk.Label(
            self,
            text="Batch Processing",
            font=("Arial", 12, "bold")
        )
        title_label.pack(side=tk.TOP, pady=10)

        # Controls frame
        controls_frame = tk.Frame(self)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)

        # Add files button
        self.add_files_btn = ttk.Button(
            controls_frame,
            text="Add Files...",
            command=self._add_files,
            width=15
        )
        self.add_files_btn.pack(side=tk.LEFT, padx=5)

        # Add folder button
        self.add_folder_btn = ttk.Button(
            controls_frame,
            text="Add Folder...",
            command=self._add_folder,
            width=15
        )
        self.add_folder_btn.pack(side=tk.LEFT, padx=5)

        # Clear list button
        self.clear_btn = ttk.Button(
            controls_frame,
            text="Clear List",
            command=self._clear_list,
            width=15
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Process batch button
        self.process_btn = ttk.Button(
            controls_frame,
            text="Process Batch",
            command=self._process_batch,
            width=15
        )
        self.process_btn.pack(side=tk.RIGHT, padx=5)

        # Cancel button (initially hidden)
        self.cancel_btn = ttk.Button(
            controls_frame,
            text="Cancel",
            command=self._cancel_batch,
            width=15
        )

        # File list frame
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Listbox for files
        self.file_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode=tk.EXTENDED,
            height=15
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y.config(command=self.file_listbox.yview)
        scrollbar_x.config(command=self.file_listbox.xview)

        # Progress frame
        progress_frame = tk.Frame(self)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

        # Status label
        self.status_var = tk.StringVar(value="Ready. Add files to begin.")
        status_label = tk.Label(
            progress_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#f0f0f0"
        )
        status_label.pack(fill=tk.X)

    def _bind_events(self):
        """Bind keyboard and mouse events."""
        # Allow delete key to remove selected files
        self.file_listbox.bind('<Delete>', lambda e: self._remove_selected())

    def _add_files(self):
        """Open file dialog to add multiple files."""
        filetypes = [
            ("PDF files", "*.pdf"),
            ("Image files", "*.png *.jpg *.jpeg *.tiff *.bmp"),
            ("All files", "*.*")
        ]

        files = filedialog.askopenfilenames(
            title="Select drawings to validate",
            filetypes=filetypes
        )

        if files:
            added_files = self.batch_processor.add_files(list(files))

            for file in added_files:
                self.file_listbox.insert(tk.END, os.path.basename(file))

            self.status_var.set(f"Added {len(added_files)} file(s) to batch")

    def _add_folder(self):
        """Open folder dialog to add all supported files from a folder."""
        folder = filedialog.askdirectory(
            title="Select folder containing drawings"
        )

        if folder:
            try:
                # Supported extensions
                supported_exts = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp')

                # Find all supported files
                files = []
                for filename in os.listdir(folder):
                    if filename.lower().endswith(supported_exts):
                        files.append(os.path.join(folder, filename))

                if files:
                    added_files = self.batch_processor.add_files(files)

                    for file in added_files:
                        self.file_listbox.insert(tk.END, os.path.basename(file))

                    self.status_var.set(f"Added {len(added_files)} file(s) from folder")
                else:
                    messagebox.showinfo(
                        "No Files Found",
                        "No supported files found in the selected folder."
                    )
            except Exception as e:
                logger.error(f"Error reading folder: {str(e)}")
                messagebox.showerror(
                    "Error",
                    f"Failed to read folder:\n{str(e)}"
                )

    def _clear_list(self):
        """Clear all files from the batch list."""
        if self.batch_processor.is_processing:
            messagebox.showwarning(
                "Processing in Progress",
                "Cannot clear list while processing."
            )
            return

        if self.file_listbox.size() > 0:
            if messagebox.askyesno("Confirm", "Clear all files from batch?"):
                self.file_listbox.delete(0, tk.END)
                self.batch_processor.clear_tasks()
                self.status_var.set("Batch list cleared")

    def _remove_selected(self):
        """Remove selected files from the list."""
        if self.batch_processor.is_processing:
            messagebox.showwarning(
                "Processing in Progress",
                "Cannot remove files while processing."
            )
            return

        selection = self.file_listbox.curselection()
        if selection:
            # Remove in reverse order to maintain indices
            for index in reversed(selection):
                self.file_listbox.delete(index)
                # Also remove from batch processor tasks
                if index < len(self.batch_processor.tasks):
                    del self.batch_processor.tasks[index]

            self.batch_processor.total_tasks = len(self.batch_processor.tasks)
            self.status_var.set(f"Removed {len(selection)} file(s)")

    def _process_batch(self):
        """Process the entire batch."""
        if self.batch_processor.total_tasks == 0:
            messagebox.showwarning("No Files", "Please add files to process.")
            return

        # Disable process button, show cancel button
        self.process_btn.pack_forget()
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

        # Disable add/clear buttons
        self.add_files_btn.config(state=tk.DISABLED)
        self.add_folder_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)

        # Start batch processing in separate thread
        self.processing_thread = threading.Thread(
            target=self._run_batch_processing,
            daemon=True
        )
        self.processing_thread.start()

    def _run_batch_processing(self):
        """Run batch processing in background thread."""
        try:
            # Process batch with progress callback
            batch_result = self.batch_processor.process_batch(
                processor_func=self.processor_func,
                callback=self._update_progress
            )

            # Update UI on main thread
            self.after(0, self._batch_complete, batch_result)

        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            self.after(0, self._batch_error, str(e))

    def _update_progress(self, current: int, total: int, filename: str):
        """Update progress bar and status."""
        progress_percent = (current / total) * 100

        # Update on main thread
        self.after(0, lambda: self.progress_var.set(progress_percent))
        self.after(0, lambda: self.status_var.set(
            f"Processing: {current}/{total} - {filename}"
        ))

    def _batch_complete(self, batch_result):
        """Handle batch processing completion."""
        # Re-enable buttons
        self.cancel_btn.pack_forget()
        self.process_btn.pack(side=tk.RIGHT, padx=5)
        self.add_files_btn.config(state=tk.NORMAL)
        self.add_folder_btn.config(state=tk.NORMAL)
        self.clear_btn.config(state=tk.NORMAL)

        # Update status
        self.status_var.set(
            f"Complete: {batch_result.successful_files}/{batch_result.total_files} successful"
        )

        # Show completion dialog
        if not batch_result.cancelled:
            messagebox.showinfo(
                "Batch Complete",
                f"Processing complete!\n\n"
                f"Total files: {batch_result.total_files}\n"
                f"Successful: {batch_result.successful_files}\n"
                f"Failed: {batch_result.failed_files}\n"
                f"Time: {batch_result.processing_time:.1f}s\n\n"
                f"Results can be exported from the Export menu."
            )

    def _batch_error(self, error_message: str):
        """Handle batch processing error."""
        # Re-enable buttons
        self.cancel_btn.pack_forget()
        self.process_btn.pack(side=tk.RIGHT, padx=5)
        self.add_files_btn.config(state=tk.NORMAL)
        self.add_folder_btn.config(state=tk.NORMAL)
        self.clear_btn.config(state=tk.NORMAL)

        self.status_var.set("Batch processing failed")

        messagebox.showerror(
            "Batch Error",
            f"An error occurred during batch processing:\n{error_message}"
        )

    def _cancel_batch(self):
        """Cancel batch processing."""
        if messagebox.askyesno("Confirm", "Cancel batch processing?"):
            self.batch_processor.cancel_batch()
            self.status_var.set("Cancelling batch...")

    def get_batch_result(self):
        """Get the current batch result."""
        return self.current_batch
