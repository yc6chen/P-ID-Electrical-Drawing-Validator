"""
Caching system for improved performance with repeated operations.
"""

import hashlib
import logging
from collections import OrderedDict
from typing import Any, Optional
import time

logger = logging.getLogger(__name__)


class ProcessingCache:
    """
    LRU (Least Recently Used) cache for processing results.

    Caches results based on file content hash to speed up repeated operations.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize processing cache.

        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _generate_key(self, filepath: str, operation: str = "process") -> str:
        """
        Generate cache key based on file content.

        Args:
            filepath: Path to file
            operation: Operation type identifier

        Returns:
            Cache key string
        """
        try:
            # Read file and compute hash
            with open(filepath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            # Combine with operation type
            cache_key = f"{operation}:{file_hash}"
            return cache_key

        except Exception as e:
            logger.warning(f"Error generating cache key: {str(e)}")
            # Fallback to filepath-based key
            return f"{operation}:{filepath}"

    def get(self, filepath: str, operation: str = "process") -> Optional[Any]:
        """
        Get cached result if available.

        Args:
            filepath: Path to file
            operation: Operation type

        Returns:
            Cached result or None
        """
        cache_key = self._generate_key(filepath, operation)

        if cache_key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(cache_key)
            self.hits += 1

            cached_data = self.cache[cache_key]
            logger.debug(f"Cache hit for {filepath} ({operation})")

            return cached_data['result']
        else:
            self.misses += 1
            logger.debug(f"Cache miss for {filepath} ({operation})")
            return None

    def put(
        self,
        filepath: str,
        result: Any,
        operation: str = "process"
    ) -> None:
        """
        Store result in cache.

        Args:
            filepath: Path to file
            result: Result to cache
            operation: Operation type
        """
        cache_key = self._generate_key(filepath, operation)

        # Remove oldest item if at capacity
        if len(self.cache) >= self.max_size and cache_key not in self.cache:
            oldest_key = next(iter(self.cache))
            removed = self.cache.pop(oldest_key)
            logger.debug(f"Cache full, removed oldest entry")

        # Store result with metadata
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time(),
            'filepath': filepath,
            'operation': operation
        }

        # Move to end (most recently used)
        self.cache.move_to_end(cache_key)

        logger.debug(f"Cached result for {filepath} ({operation})")

    def invalidate(self, filepath: str, operation: str = None) -> int:
        """
        Invalidate cache entries for a file.

        Args:
            filepath: Path to file
            operation: Specific operation to invalidate (None for all)

        Returns:
            Number of entries invalidated
        """
        count = 0
        keys_to_remove = []

        for key, data in self.cache.items():
            if data['filepath'] == filepath:
                if operation is None or data['operation'] == operation:
                    keys_to_remove.append(key)
                    count += 1

        for key in keys_to_remove:
            del self.cache[key]

        if count > 0:
            logger.debug(f"Invalidated {count} cache entries for {filepath}")

        return count

    def clear(self) -> None:
        """Clear all cache entries."""
        size = len(self.cache)
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info(f"Cleared cache ({size} entries)")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

    def resize(self, new_max_size: int) -> None:
        """
        Resize cache maximum size.

        Args:
            new_max_size: New maximum size
        """
        self.max_size = new_max_size

        # Remove oldest entries if over new limit
        while len(self.cache) > new_max_size:
            oldest_key = next(iter(self.cache))
            self.cache.pop(oldest_key)

        logger.info(f"Resized cache to {new_max_size} entries")
