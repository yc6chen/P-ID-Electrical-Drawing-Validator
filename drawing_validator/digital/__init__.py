"""
Digital signature validation module.

This module provides functionality for detecting, extracting, and validating
cryptographic digital signatures in PDF documents, including Adobe PDF signatures,
PAdES, PKCS#7, and CMS formats.
"""

from .digital_models import DigitalSignature, CertificateValidationResult, DigitalSignatureValidationResult
from .signature_extractor import DigitalSignatureExtractor
from .trust_store import TrustStore
from .certificate_validator import CertificateValidator

__all__ = [
    'DigitalSignature',
    'CertificateValidationResult',
    'DigitalSignatureValidationResult',
    'DigitalSignatureExtractor',
    'TrustStore',
    'CertificateValidator',
]
