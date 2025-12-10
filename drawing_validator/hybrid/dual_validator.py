"""
Combine image-based seal validation with digital signature validation.

This module provides a unified validation approach that checks both
visual seals and cryptographic digital signatures in engineering drawings.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import datetime

from digital.signature_extractor import DigitalSignatureExtractor
from digital.certificate_validator import CertificateValidator
from digital.trust_store import TrustStore

logger = logging.getLogger(__name__)


@dataclass
class HybridValidationResult:
    """Combined results from both validation methods."""

    file_path: str
    validation_time: datetime.datetime

    # Image-based validation results
    seal_validation: Optional[Dict] = None
    seal_valid: bool = False
    seal_associations: List[str] = field(default_factory=list)
    seal_confidence: float = 0.0

    # Digital signature validation results
    digital_validation: Optional[Dict] = None
    digital_signatures_found: bool = False
    digital_signatures_valid: bool = False
    digital_certificate_associations: List[str] = field(default_factory=list)
    digital_trust_status: str = "unknown"

    # Combined results
    overall_valid: bool = False
    validation_methods_used: List[str] = field(default_factory=list)
    compliance_status: str = "unknown"
    validation_notes: List[str] = field(default_factory=list)

    @property
    def has_seal_signature(self) -> bool:
        """Check if document has image-based seal."""
        return self.seal_validation is not None

    @property
    def has_digital_signature(self) -> bool:
        """Check if document has digital signature."""
        return self.digital_validation is not None

    @property
    def signature_types_found(self) -> List[str]:
        """Get list of signature types found."""
        types = []
        if self.has_seal_signature:
            types.append("image_based_seal")
        if self.has_digital_signature:
            types.append("digital_signature")
        return types

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'file_path': self.file_path,
            'validation_time': self.validation_time.isoformat(),
            'seal_validation': {
                'valid': self.seal_valid,
                'associations': self.seal_associations,
                'confidence': self.seal_confidence,
                'details': self.seal_validation
            } if self.has_seal_signature else None,
            'digital_validation': {
                'signatures_found': self.digital_signatures_found,
                'valid': self.digital_signatures_valid,
                'associations': self.digital_certificate_associations,
                'trust_status': self.digital_trust_status,
                'details': self.digital_validation
            } if self.has_digital_signature else None,
            'overall_valid': self.overall_valid,
            'compliance_status': self.compliance_status,
            'signature_types_found': self.signature_types_found,
            'validation_methods_used': self.validation_methods_used,
            'validation_notes': self.validation_notes
        }


class HybridValidator:
    """Combines image-based seal validation with digital signature validation."""

    def __init__(self, seal_processor=None, trust_store: TrustStore = None):
        """
        Initialize hybrid validator.

        Args:
            seal_processor: Existing seal validation processor (optional)
            trust_store: TrustStore for certificate validation (optional)
        """
        self.seal_processor = seal_processor

        # Initialize digital signature components
        if trust_store is None:
            trust_store = TrustStore()

        self.trust_store = trust_store
        self.signature_extractor = DigitalSignatureExtractor()
        self.certificate_validator = CertificateValidator(trust_store)

        # Compliance rules (configurable)
        self.compliance_rules = self._load_compliance_rules()

    def _load_compliance_rules(self) -> Dict:
        """Load compliance rules for validation."""
        return {
            'require_both': False,  # If True, require both seal and digital signature
            'accept_either': True,  # If True, accept either seal or digital signature
            'minimum_confidence': 0.7,  # Minimum confidence for seal validation
        }

    def validate_document(self, file_path: str, existing_seal_result=None) -> HybridValidationResult:
        """
        Perform comprehensive validation of document.

        Checks both image-based seals and digital signatures.

        Args:
            file_path: Path to PDF file
            existing_seal_result: Optional pre-computed seal validation result

        Returns:
            HybridValidationResult with combined validation details
        """
        result = HybridValidationResult(
            file_path=file_path,
            validation_time=datetime.datetime.now()
        )

        # Step 1: Validate image-based seals
        if existing_seal_result:
            # Use existing result
            seal_summary = self._extract_seal_summary(existing_seal_result)
        else:
            # Perform seal validation
            seal_summary = self._validate_seals(file_path)

        if seal_summary:
            result.seal_validation = seal_summary
            result.seal_valid = seal_summary.get('valid', False)
            result.seal_associations = seal_summary.get('associations', [])
            result.seal_confidence = seal_summary.get('confidence', 0.0)
            result.validation_methods_used.append("image_seal_validation")

        # Step 2: Validate digital signatures
        digital_summary = self._validate_digital_signatures(file_path)

        if digital_summary:
            result.digital_validation = digital_summary
            result.digital_signatures_found = digital_summary.get('signatures_found', False)
            result.digital_signatures_valid = digital_summary.get('all_signatures_valid', False)
            result.digital_certificate_associations = digital_summary.get('certificate_associations', [])
            result.digital_trust_status = digital_summary.get('trust_status', 'unknown')
            result.validation_methods_used.append("digital_signature_validation")

        # Step 3: Determine overall validation
        result.overall_valid = self._determine_overall_validity(result)

        # Step 4: Determine compliance status
        result.compliance_status = self._determine_compliance_status(result)

        # Step 5: Add validation notes
        result.validation_notes = self._generate_validation_notes(result)

        return result

    def _validate_seals(self, file_path: str) -> Optional[Dict]:
        """
        Validate image-based seals using existing system.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with seal validation summary or None
        """
        try:
            if not self.seal_processor:
                return None

            # Use existing seal validation pipeline
            seal_results = self.seal_processor.process_drawing(file_path)

            if seal_results.status != "COMPLETE":
                return None

            # Extract relevant information
            validation_summary = {
                'valid': seal_results.overall_validation.valid if seal_results.overall_validation else False,
                'associations': seal_results.overall_validation.associations if seal_results.overall_validation else [],
                'confidence': seal_results.overall_validation.confidence if seal_results.overall_validation else 0.0,
                'pages_with_seals': sum(1 for p in seal_results.pages if p.has_valid_signature),
                'total_pages': len(seal_results.pages),
                'processing_time': seal_results.processing_time
            }

            return validation_summary

        except Exception as e:
            logger.error(f"Error validating seals: {str(e)}")
            return None

    def _extract_seal_summary(self, seal_result) -> Optional[Dict]:
        """
        Extract summary from existing seal validation result.

        Args:
            seal_result: Existing seal validation result

        Returns:
            Dictionary with seal validation summary
        """
        try:
            return {
                'valid': seal_result.overall_validation.valid if hasattr(seal_result, 'overall_validation') and seal_result.overall_validation else False,
                'associations': seal_result.overall_validation.associations if hasattr(seal_result, 'overall_validation') and seal_result.overall_validation else [],
                'confidence': seal_result.overall_validation.confidence if hasattr(seal_result, 'overall_validation') and seal_result.overall_validation else 0.0,
                'pages_with_seals': sum(1 for p in seal_result.pages if p.has_valid_signature) if hasattr(seal_result, 'pages') else 0,
                'total_pages': len(seal_result.pages) if hasattr(seal_result, 'pages') else 0,
            }
        except Exception as e:
            logger.error(f"Error extracting seal summary: {str(e)}")
            return None

    def _validate_digital_signatures(self, file_path: str) -> Optional[Dict]:
        """
        Validate digital signatures.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with digital signature validation summary or None
        """
        try:
            # Extract digital signatures
            signatures = self.signature_extractor.extract_signatures(file_path)

            if not signatures:
                return {
                    'signatures_found': False,
                    'message': 'No digital signatures found'
                }

            # Validate each signature
            valid_signatures = []
            invalid_signatures = []
            certificate_associations = set()

            for signature in signatures:
                # Verify signature integrity
                integrity_results = self.signature_extractor.verify_signature_integrity(
                    file_path, signature
                )

                # Validate certificates
                if signature.certificates:
                    for cert in signature.certificates:
                        cert_results = self.certificate_validator.validate_certificate_chain(cert)

                        # Check for association match
                        association = cert_results.association_match
                        if association:
                            certificate_associations.add(association)

                        # Check if certificate chain is valid
                        if (cert_results.chain_valid and
                            cert_results.root_trusted and
                            cert_results.revocation_status == 'not_revoked'):

                            signature.signature_valid = True
                            signature.validation_details = cert_results.to_dict()

                    if signature.signature_valid:
                        valid_signatures.append(signature)
                    else:
                        invalid_signatures.append(signature)
                else:
                    # No certificates found
                    signature.signature_valid = False
                    invalid_signatures.append(signature)

            # Determine overall digital signature status
            all_valid = len(valid_signatures) > 0 and len(invalid_signatures) == 0
            trust_status = self._determine_digital_trust_status(
                valid_signatures, invalid_signatures
            )

            return {
                'signatures_found': True,
                'total_signatures': len(signatures),
                'valid_signatures': len(valid_signatures),
                'invalid_signatures': len(invalid_signatures),
                'all_signatures_valid': all_valid,
                'certificate_associations': list(certificate_associations),
                'trust_status': trust_status,
                'signatures': [sig.to_dict() for sig in signatures],
            }

        except Exception as e:
            logger.error(f"Error validating digital signatures: {str(e)}")
            return None

    def _determine_overall_validity(self, result: HybridValidationResult) -> bool:
        """
        Determine overall document validity based on both methods.

        Args:
            result: HybridValidationResult to evaluate

        Returns:
            True if document is valid, False otherwise
        """
        rules = self.compliance_rules

        # Rule: Both must be valid (strictest)
        if rules.get('require_both', False):
            return result.seal_valid and result.digital_signatures_valid

        # Rule: Either seal OR digital signature is valid
        if rules.get('accept_either', True):
            # Check seal validation
            seal_meets_requirements = (
                result.seal_valid and
                result.seal_confidence >= rules.get('minimum_confidence', 0.7)
            )

            # Check digital signature validation
            digital_meets_requirements = (
                result.digital_signatures_valid and
                result.digital_trust_status in ['fully_trusted', 'partially_trusted']
            )

            return seal_meets_requirements or digital_meets_requirements

        return False

    def _determine_compliance_status(self, result: HybridValidationResult) -> str:
        """
        Determine compliance status based on validation results.

        Args:
            result: HybridValidationResult to evaluate

        Returns:
            Compliance status string
        """
        if not result.overall_valid:
            return "NON_COMPLIANT"

        # Check if we have association matches
        associations_found = set()

        if result.seal_associations:
            associations_found.update(result.seal_associations)

        if result.digital_certificate_associations:
            associations_found.update(result.digital_certificate_associations)

        if not associations_found:
            return "COMPLIANT_NO_ASSOCIATION"

        # Check for specific compliance requirements
        return "COMPLIANT"

    def _determine_digital_trust_status(self, valid_sigs, invalid_sigs) -> str:
        """
        Determine trust status for digital signatures.

        Args:
            valid_sigs: List of valid signatures
            invalid_sigs: List of invalid signatures

        Returns:
            Trust status string
        """
        if not valid_sigs and not invalid_sigs:
            return "no_signatures"

        if valid_sigs and not invalid_sigs:
            return "fully_trusted"

        if valid_sigs and invalid_sigs:
            return "partially_trusted"

        if not valid_sigs and invalid_sigs:
            return "untrusted"

        return "unknown"

    def _generate_validation_notes(self, result: HybridValidationResult) -> List[str]:
        """
        Generate human-readable validation notes.

        Args:
            result: HybridValidationResult

        Returns:
            List of validation notes
        """
        notes = []

        # Seal validation notes
        if result.has_seal_signature:
            if result.seal_valid:
                notes.append(f"Image-based seal validation passed (confidence: {result.seal_confidence:.2f})")
                if result.seal_associations:
                    notes.append(f"Seal associations: {', '.join(result.seal_associations)}")
            else:
                notes.append("Image-based seal validation failed or no valid seals found")

        # Digital signature notes
        if result.has_digital_signature:
            if result.digital_signatures_valid:
                notes.append(f"Digital signature validation passed (trust: {result.digital_trust_status})")
                if result.digital_certificate_associations:
                    notes.append(f"Certificate associations: {', '.join(result.digital_certificate_associations)}")
            else:
                notes.append("Digital signature validation failed or signatures untrusted")

        # Overall notes
        if not result.has_seal_signature and not result.has_digital_signature:
            notes.append("No signatures found in document")

        if result.overall_valid:
            notes.append(f"Document is compliant: {result.compliance_status}")
        else:
            notes.append("Document does not meet validation requirements")

        return notes
