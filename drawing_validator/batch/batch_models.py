"""
Data models for batch processing.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Status of a batch task."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


@dataclass
class BatchTask:
    """Represents a single file processing task in a batch."""

    file_path: str
    status: str = "PENDING"
    error_message: Optional[str] = None
    result: Optional[Any] = None  # Will store DrawingValidationResult
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def processing_time(self) -> float:
        """Get processing time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'file_path': self.file_path,
            'status': self.status,
            'error_message': self.error_message,
            'processing_time': self.processing_time,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class BatchResult:
    """Results from processing a batch of files."""

    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    processing_time: float
    results: List[Any] = field(default_factory=list)  # List of DrawingValidationResult
    cancelled: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.processed_files == 0:
            return 0.0
        return self.successful_files / self.processed_files

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'success_rate': self.success_rate,
            'processing_time': self.processing_time,
            'cancelled': self.cancelled,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class BatchSummary:
    """Summary statistics for a batch processing run."""

    total_files: int = 0
    total_pages: int = 0
    valid_pages: int = 0
    validation_rate: float = 0.0
    association_distribution: Dict[str, int] = field(default_factory=dict)
    average_processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_files': self.total_files,
            'total_pages': self.total_pages,
            'valid_pages': self.valid_pages,
            'validation_rate': self.validation_rate,
            'association_distribution': self.association_distribution,
            'average_processing_time': self.average_processing_time,
            'timestamp': self.timestamp.isoformat()
        }
