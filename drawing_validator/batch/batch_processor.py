"""
Batch processing system for multiple files with progress tracking.
"""

import os
import time
import logging
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Optional
from datetime import datetime
from collections import defaultdict

from .batch_models import BatchTask, BatchResult, BatchSummary, TaskStatus

# Setup logging
logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Batch processor for handling multiple file validations.

    Supports parallel processing, progress tracking, and cancellation.
    """

    def __init__(self, max_workers: int = 2):
        """
        Initialize batch processor.

        Args:
            max_workers: Maximum number of parallel worker threads
        """
        self.max_workers = max_workers
        self.task_queue = Queue()
        self.results = []
        self.is_processing = False
        self.current_progress = 0
        self.total_tasks = 0
        self.cancel_requested = False
        self.tasks: List[BatchTask] = []

    def add_files(self, file_paths: List[str]) -> List[str]:
        """
        Add multiple files to batch queue.

        Args:
            file_paths: List of file paths to process

        Returns:
            List of valid file paths that were added
        """
        valid_files = []

        for file_path in file_paths:
            if self._validate_file(file_path):
                task = BatchTask(file_path=file_path, status=TaskStatus.PENDING.value)
                self.tasks.append(task)
                valid_files.append(file_path)

        self.total_tasks = len(valid_files)
        logger.info(f"Added {self.total_tasks} files to batch queue")

        return valid_files

    def _validate_file(self, file_path: str) -> bool:
        """
        Validate that file exists and has supported extension.

        Args:
            file_path: Path to file

        Returns:
            True if file is valid
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return False

        # Check for supported extensions
        supported_extensions = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp')
        if not file_path.lower().endswith(supported_extensions):
            logger.warning(f"Unsupported file type: {file_path}")
            return False

        return True

    def process_batch(
        self,
        processor_func: Callable,
        callback: Optional[Callable] = None
    ) -> BatchResult:
        """
        Process entire batch with progress reporting.

        Args:
            processor_func: Function to process each file (takes filepath, returns result)
            callback: Optional progress callback (current, total, filename)

        Returns:
            BatchResult with processing statistics
        """
        start_time = time.time()
        self.is_processing = True
        self.cancel_requested = False
        self.results = []
        self.current_progress = 0

        # Process tasks with thread pool
        successful = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._process_single_file, task, processor_func): task
                for task in self.tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]

                if self.cancel_requested:
                    future.cancel()
                    task.status = TaskStatus.CANCELLED.value
                    continue

                try:
                    result = future.result()
                    task.result = result
                    self.results.append(result)

                    if result and hasattr(result, 'overall_valid'):
                        successful += 1
                    else:
                        failed += 1

                    self.current_progress += 1

                    # Update progress callback
                    if callback:
                        callback(
                            self.current_progress,
                            self.total_tasks,
                            os.path.basename(task.file_path)
                        )

                except Exception as e:
                    logger.error(f"Error processing {task.file_path}: {str(e)}")
                    task.status = TaskStatus.ERROR.value
                    task.error_message = str(e)
                    failed += 1
                    self.current_progress += 1

                    if callback:
                        callback(self.current_progress, self.total_tasks, "Error")

        processing_time = time.time() - start_time

        batch_result = BatchResult(
            total_files=self.total_tasks,
            processed_files=self.current_progress,
            successful_files=successful,
            failed_files=failed,
            processing_time=processing_time,
            results=self.results,
            cancelled=self.cancel_requested
        )

        self.is_processing = False
        logger.info(f"Batch processing complete: {successful}/{self.total_tasks} successful")

        return batch_result

    def _process_single_file(self, task: BatchTask, processor_func: Callable):
        """
        Process a single file.

        Args:
            task: Batch task to process
            processor_func: Processing function

        Returns:
            Processing result
        """
        task.status = TaskStatus.PROCESSING.value
        task.started_at = datetime.now()

        try:
            logger.info(f"Processing: {task.file_path}")
            result = processor_func(task.file_path)

            task.status = TaskStatus.COMPLETE.value
            task.completed_at = datetime.now()

            return result

        except Exception as e:
            logger.error(f"Error processing {task.file_path}: {str(e)}")
            task.status = TaskStatus.ERROR.value
            task.error_message = str(e)
            task.completed_at = datetime.now()
            raise

    def cancel_batch(self):
        """Request cancellation of batch processing."""
        self.cancel_requested = True
        logger.info("Batch cancellation requested")

    def clear_tasks(self):
        """Clear all tasks from the batch queue."""
        self.tasks.clear()
        self.results.clear()
        self.total_tasks = 0
        self.current_progress = 0
        logger.info("Batch queue cleared")

    def generate_batch_summary(self) -> BatchSummary:
        """
        Generate comprehensive batch summary.

        Returns:
            BatchSummary with statistics
        """
        if not self.results:
            return BatchSummary()

        summary = BatchSummary()

        # Calculate statistics from results
        total_pages = 0
        valid_pages = 0
        association_counts = defaultdict(int)
        processing_times = []

        for result in self.results:
            if hasattr(result, 'page_results'):
                total_pages += len(result.page_results)
                valid_pages += sum(
                    1 for page in result.page_results
                    if page.has_valid_signature
                )

                # Count associations
                associations = result.get_all_associations() if hasattr(result, 'get_all_associations') else []
                for assoc in associations:
                    association_counts[assoc] += 1

                # Track processing time
                if hasattr(result, 'total_processing_time'):
                    processing_times.append(result.total_processing_time)

        summary.total_files = len(self.results)
        summary.total_pages = total_pages
        summary.valid_pages = valid_pages
        summary.validation_rate = valid_pages / total_pages if total_pages > 0 else 0.0
        summary.association_distribution = dict(association_counts)
        summary.average_processing_time = (
            sum(processing_times) / len(processing_times)
            if processing_times else 0.0
        )

        return summary
