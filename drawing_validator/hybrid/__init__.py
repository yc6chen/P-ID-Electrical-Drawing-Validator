"""
Hybrid validation module.

This module combines image-based seal validation with digital signature validation
to provide comprehensive validation of engineering drawings.
"""

from .dual_validator import HybridValidator, HybridValidationResult

__all__ = [
    'HybridValidator',
    'HybridValidationResult',
]
