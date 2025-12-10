"""
Data models for digital signatures and certificates.

This module defines the data structures used for representing digital signatures,
certificates, and their validation results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from cryptography import x509
import datetime


@dataclass
class DigitalSignature:
    """Represents a digital signature extracted from a PDF."""

    signature_type: str  # 'Adobe.PPKLite', 'PKCS#7', 'CMS', etc.
    signature_bytes: bytes
    certificates: List[x509.Certificate] = field(default_factory=list)

    # Signature metadata
    signing_time: Optional[datetime.datetime] = None
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    location: Optional[str] = None
    reason: Optional[str] = None

    # PDF-specific fields
    page_number: Optional[int] = None
    field_name: Optional[str] = None
    bounding_box: Optional[tuple] = None  # (x0, y0, x1, y1)

    # Validation results
    signature_valid: bool = False
    validation_details: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_certificates(self) -> bool:
        """Check if signature has associated certificates."""
        return len(self.certificates) > 0

    @property
    def signing_certificate(self) -> Optional[x509.Certificate]:
        """Get the signing certificate (usually the first one)."""
        return self.certificates[0] if self.certificates else None

    def get_certificate_subject(self) -> Optional[str]:
        """Get subject name from signing certificate."""
        if self.signing_certificate:
            return self.signing_certificate.subject.rfc4514_string()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'signature_type': self.signature_type,
            'signing_time': self.signing_time.isoformat() if self.signing_time else None,
            'signer_name': self.signer_name,
            'signer_email': self.signer_email,
            'location': self.location,
            'reason': self.reason,
            'page_number': self.page_number,
            'field_name': self.field_name,
            'has_certificates': self.has_certificates,
            'certificate_subject': self.get_certificate_subject(),
            'signature_valid': self.signature_valid,
            'validation_details': self.validation_details
        }


@dataclass
class CertificateValidationResult:
    """Results of certificate validation."""

    certificate: x509.Certificate
    validation_time: datetime.datetime

    # Chain validation
    chain_valid: bool = False
    root_trusted: bool = False
    certificate_chain: List[x509.Certificate] = field(default_factory=list)
    chain_errors: List[str] = field(default_factory=list)

    # Revocation status
    revocation_status: str = "unknown"  # 'not_revoked', 'revoked', 'unknown'
    revocation_check_time: Optional[datetime.datetime] = None
    revocation_errors: List[str] = field(default_factory=list)

    # Certificate properties
    key_usage_valid: bool = False
    extended_key_usage_valid: bool = False
    certificate_policies: List[str] = field(default_factory=list)

    # Association mapping
    association_match: Optional[str] = None
    association_confidence: float = 0.0

    # Overall status
    valid: bool = False
    validation_notes: List[str] = field(default_factory=list)

    def get_certificate_subject(self) -> str:
        """Get certificate subject as string."""
        return self.certificate.subject.rfc4514_string()

    def get_certificate_issuer(self) -> str:
        """Get certificate issuer as string."""
        return self.certificate.issuer.rfc4514_string()

    def get_validity_period(self) -> tuple:
        """Get certificate validity period."""
        return (self.certificate.not_valid_before, self.certificate.not_valid_after)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        not_before, not_after = self.get_validity_period()
        return {
            'subject': self.get_certificate_subject(),
            'issuer': self.get_certificate_issuer(),
            'valid_from': not_before.isoformat(),
            'valid_to': not_after.isoformat(),
            'chain_valid': self.chain_valid,
            'root_trusted': self.root_trusted,
            'chain_length': len(self.certificate_chain),
            'revocation_status': self.revocation_status,
            'key_usage_valid': self.key_usage_valid,
            'association_match': self.association_match,
            'association_confidence': self.association_confidence,
            'valid': self.valid,
            'errors': self.chain_errors + self.revocation_errors,
            'notes': self.validation_notes
        }


@dataclass
class DigitalSignatureValidationResult:
    """Results of digital signature validation for a document."""

    file_path: str
    validation_time: datetime.datetime

    # Signature extraction
    signatures_found: bool = False
    signatures: List[DigitalSignature] = field(default_factory=list)
    extraction_errors: List[str] = field(default_factory=list)

    # Validation results
    valid_signatures: List[DigitalSignature] = field(default_factory=list)
    invalid_signatures: List[DigitalSignature] = field(default_factory=list)

    # Trust assessment
    trust_status: str = "unknown"  # 'fully_trusted', 'partially_trusted', 'untrusted'
    trusted_associations: List[str] = field(default_factory=list)

    # Certificate information
    unique_certificates: List[x509.Certificate] = field(default_factory=list)
    certificate_validation_results: List[CertificateValidationResult] = field(default_factory=list)

    # Overall assessment
    all_signatures_valid: bool = False
    validation_summary: Dict[str, Any] = field(default_factory=dict)

    @property
    def signature_count(self) -> int:
        """Get total number of signatures."""
        return len(self.signatures)

    @property
    def valid_signature_count(self) -> int:
        """Get number of valid signatures."""
        return len(self.valid_signatures)

    @property
    def invalid_signature_count(self) -> int:
        """Get number of invalid signatures."""
        return len(self.invalid_signatures)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'file_path': self.file_path,
            'validation_time': self.validation_time.isoformat(),
            'signatures_found': self.signatures_found,
            'signature_count': self.signature_count,
            'valid_signature_count': self.valid_signature_count,
            'invalid_signature_count': self.invalid_signature_count,
            'trust_status': self.trust_status,
            'trusted_associations': self.trusted_associations,
            'all_signatures_valid': self.all_signatures_valid,
            'extraction_errors': self.extraction_errors,
            'signatures': [sig.to_dict() for sig in self.signatures],
            'certificate_validations': [cert.to_dict() for cert in self.certificate_validation_results],
            'validation_summary': self.validation_summary
        }
