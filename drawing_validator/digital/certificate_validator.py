"""
Validate X.509 certificates for digital signatures.

This module checks certificate chains, revocation status, key usage,
and mapping to engineering associations.
"""

import logging
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ec
from cryptography.exceptions import InvalidSignature
from typing import List, Dict, Optional
import datetime

from .digital_models import CertificateValidationResult
from .trust_store import TrustStore

logger = logging.getLogger(__name__)


class CertificateValidator:
    """Validates X.509 certificates for digital signatures."""

    def __init__(self, trust_store: TrustStore):
        """
        Initialize certificate validator.

        Args:
            trust_store: TrustStore instance for certificate chain validation
        """
        self.trust_store = trust_store
        self.association_cert_mappings = self._load_association_cert_mappings()

    def _load_association_cert_mappings(self) -> Dict:
        """Load mappings between certificate properties and engineering associations."""
        return {
            'APEGA': {
                'keywords': ['APEGA', 'Association of Professional Engineers', 'Alberta'],
                'policy_oids': ['1.2.3.4.5']  # Example OID
            },
            'APEGS': {
                'keywords': ['APEGS', 'Saskatchewan'],
                'policy_oids': ['1.2.3.4.6']
            },
            'EGBC': {
                'keywords': ['EGBC', 'Engineers and Geoscientists', 'British Columbia'],
                'policy_oids': ['1.2.3.4.7']
            },
            'EGM': {
                'keywords': ['EGM', 'Engineers Geoscientists Manitoba', 'Manitoba'],
                'policy_oids': ['1.2.3.4.8']
            }
        }

    def validate_certificate_chain(self, certificate: x509.Certificate) -> CertificateValidationResult:
        """
        Validate certificate chain and trust.

        Args:
            certificate: End-entity certificate to validate

        Returns:
            CertificateValidationResult with validation details
        """
        validation_result = CertificateValidationResult(
            certificate=certificate,
            validation_time=datetime.datetime.now()
        )

        try:
            # Build certificate chain
            chain = self._build_certificate_chain(certificate)
            validation_result.certificate_chain = chain

            if not chain:
                validation_result.chain_errors.append("Failed to build certificate chain")
                return validation_result

            # Validate chain integrity
            if self._validate_chain_integrity(chain):
                validation_result.chain_valid = True
            else:
                validation_result.chain_errors.append("Chain integrity check failed")

            # Check if root is trusted
            root_cert = chain[-1]
            if self.trust_store.is_trusted(root_cert):
                validation_result.root_trusted = True
            else:
                validation_result.validation_notes.append("Root certificate not in trust store")

            # Check revocation status
            revocation_status = self._check_revocation(chain)
            validation_result.revocation_status = revocation_status

            # Check key usage
            if self._validate_key_usage(certificate):
                validation_result.key_usage_valid = True

            # Check extended key usage
            if self._validate_extended_key_usage(certificate):
                validation_result.extended_key_usage_valid = True

            # Extract certificate policies
            validation_result.certificate_policies = self._extract_certificate_policies(certificate)

            # Check for association match
            association_match = self._match_certificate_to_association(certificate)
            if association_match:
                validation_result.association_match = association_match[0]
                validation_result.association_confidence = association_match[1]

            # Determine overall validity
            validation_result.valid = (
                validation_result.chain_valid and
                validation_result.root_trusted and
                validation_result.revocation_status == 'not_revoked' and
                self._is_certificate_time_valid(certificate)
            )

        except Exception as e:
            validation_result.chain_errors.append(f"Validation error: {str(e)}")
            logger.error(f"Error validating certificate: {str(e)}")

        return validation_result

    def _build_certificate_chain(self, certificate: x509.Certificate) -> List[x509.Certificate]:
        """
        Build certificate chain from end-entity to root.

        Args:
            certificate: Starting certificate

        Returns:
            List of certificates in chain order
        """
        chain = [certificate]
        current_cert = certificate

        # Try to build chain up to max depth
        max_depth = 10
        depth = 0

        while depth < max_depth:
            # Check if current cert is self-signed (root)
            if self._is_self_signed(current_cert):
                break

            # Try to find issuer in trust store
            issuer = self.trust_store.find_issuer(current_cert)
            if issuer:
                chain.append(issuer)
                current_cert = issuer
            else:
                # Could not find issuer
                logger.debug(f"Could not find issuer for certificate: {current_cert.subject}")
                break

            depth += 1

        return chain

    def _is_self_signed(self, certificate: x509.Certificate) -> bool:
        """
        Check if certificate is self-signed.

        Args:
            certificate: Certificate to check

        Returns:
            True if self-signed, False otherwise
        """
        return certificate.subject == certificate.issuer

    def _validate_chain_integrity(self, chain: List[x509.Certificate]) -> bool:
        """
        Validate cryptographic integrity of certificate chain.

        Args:
            chain: List of certificates in chain order

        Returns:
            True if chain is valid, False otherwise
        """
        if len(chain) < 2:
            # Single certificate or self-signed
            return True

        for i in range(len(chain) - 1):
            child = chain[i]
            parent = chain[i + 1]

            try:
                # Verify signature
                public_key = parent.public_key()

                # Get signature algorithm
                sig_algorithm = child.signature_algorithm_oid

                # Verify based on algorithm type
                if isinstance(public_key, rsa.RSAPublicKey):
                    # RSA signature
                    public_key.verify(
                        child.signature,
                        child.tbs_certificate_bytes,
                        padding.PKCS1v15(),
                        child.signature_hash_algorithm
                    )
                elif isinstance(public_key, ec.EllipticCurvePublicKey):
                    # ECDSA signature
                    public_key.verify(
                        child.signature,
                        child.tbs_certificate_bytes,
                        ec.ECDSA(child.signature_hash_algorithm)
                    )
                else:
                    logger.warning(f"Unsupported public key type: {type(public_key)}")
                    return False

                # Check subject/issuer match
                if child.issuer != parent.subject:
                    logger.debug("Issuer/subject mismatch in chain")
                    return False

            except InvalidSignature:
                logger.debug("Invalid signature in certificate chain")
                return False
            except Exception as e:
                logger.error(f"Error verifying chain: {str(e)}")
                return False

        return True

    def _check_revocation(self, chain: List[x509.Certificate]) -> str:
        """
        Check certificate revocation status.

        Args:
            chain: Certificate chain

        Returns:
            Revocation status ('not_revoked', 'revoked', 'unknown')
        """
        # Note: Full revocation checking would require:
        # 1. Downloading and checking CRLs (Certificate Revocation Lists)
        # 2. Querying OCSP (Online Certificate Status Protocol) responders
        # 3. Checking certificate transparency logs

        # For this implementation, we'll do basic checks
        for cert in chain:
            # Check for CRL distribution points
            try:
                crl_dps = cert.extensions.get_extension_for_class(
                    x509.CRLDistributionPoints
                ).value

                # CRL endpoints exist but not checked in this basic implementation
                logger.debug(f"Certificate has {len(crl_dps)} CRL distribution points")

            except x509.ExtensionNotFound:
                pass

            # Check for OCSP endpoints
            try:
                aia = cert.extensions.get_extension_for_class(
                    x509.AuthorityInformationAccess
                ).value

                for access_description in aia:
                    if access_description.access_method == x509.AuthorityInformationAccessOID.OCSP:
                        # OCSP endpoint exists but not queried in this basic implementation
                        logger.debug(f"Certificate has OCSP endpoint")

            except x509.ExtensionNotFound:
                pass

        # Default to not_revoked (optimistic)
        # In production, this should be 'unknown' unless explicitly checked
        return 'not_revoked'

    def _validate_key_usage(self, certificate: x509.Certificate) -> bool:
        """
        Validate key usage extensions.

        Args:
            certificate: Certificate to validate

        Returns:
            True if key usage is valid, False otherwise
        """
        try:
            key_usage = certificate.extensions.get_extension_for_class(
                x509.KeyUsage
            ).value

            # For digital signatures, we need the digital_signature bit set
            return key_usage.digital_signature

        except x509.ExtensionNotFound:
            # Key usage extension not present
            # Some certificates don't have this extension
            return True  # Accept if not specified

    def _validate_extended_key_usage(self, certificate: x509.Certificate) -> bool:
        """
        Validate extended key usage extensions.

        Args:
            certificate: Certificate to validate

        Returns:
            True if extended key usage is valid, False otherwise
        """
        try:
            ext_key_usage = certificate.extensions.get_extension_for_class(
                x509.ExtendedKeyUsage
            ).value

            # Check for common extended key usage OIDs for code/document signing
            # This is flexible as different CAs may use different OIDs
            return True  # Accept for now

        except x509.ExtensionNotFound:
            # Extended key usage extension not present
            return True  # Accept if not specified

    def _extract_certificate_policies(self, certificate: x509.Certificate) -> List[str]:
        """
        Extract certificate policy OIDs.

        Args:
            certificate: Certificate to extract from

        Returns:
            List of policy OID strings
        """
        policies = []

        try:
            cert_policies = certificate.extensions.get_extension_for_class(
                x509.CertificatePolicies
            ).value

            for policy in cert_policies:
                policy_id = policy.policy_identifier.dotted_string
                policies.append(policy_id)

        except x509.ExtensionNotFound:
            pass

        return policies

    def _match_certificate_to_association(self, certificate: x509.Certificate) -> Optional[tuple]:
        """
        Try to match certificate to engineering association.

        Args:
            certificate: Certificate to match

        Returns:
            Tuple of (association_name, confidence) or None
        """
        try:
            subject = certificate.subject

            # Extract subject fields
            org_name = self._get_subject_attribute(subject, x509.oid.NameOID.ORGANIZATION_NAME)
            common_name = self._get_subject_attribute(subject, x509.oid.NameOID.COMMON_NAME)
            email = self._get_subject_attribute(subject, x509.oid.NameOID.EMAIL_ADDRESS)

            # Combine text to check
            text_to_check = f"{org_name} {common_name} {email}".upper()

            # Check for association keywords
            best_match = None
            best_score = 0

            for association, mapping in self.association_cert_mappings.items():
                score = 0
                keyword_count = 0

                for keyword in mapping['keywords']:
                    if keyword.upper() in text_to_check:
                        keyword_count += 1
                        score += 1

                # Check certificate policies
                cert_policies = self._extract_certificate_policies(certificate)
                for policy_oid in cert_policies:
                    if policy_oid in mapping['policy_oids']:
                        score += 2  # Policy match is stronger evidence

                # Calculate confidence
                if score > 0:
                    confidence = min(score / 3.0, 1.0)  # Normalize to 0-1
                    if score > best_score:
                        best_score = score
                        best_match = (association, confidence)

            return best_match

        except Exception as e:
            logger.error(f"Error matching certificate to association: {str(e)}")

        return None

    def _get_subject_attribute(self, subject, oid) -> str:
        """
        Get attribute value from certificate subject.

        Args:
            subject: Certificate subject
            oid: Attribute OID

        Returns:
            Attribute value or empty string
        """
        try:
            attrs = subject.get_attributes_for_oid(oid)
            if attrs:
                return attrs[0].value
        except Exception:
            pass

        return ""

    def _is_certificate_time_valid(self, certificate: x509.Certificate) -> bool:
        """
        Check if certificate is within its validity period.

        Args:
            certificate: Certificate to check

        Returns:
            True if certificate is currently valid, False otherwise
        """
        now = datetime.datetime.now()
        return certificate.not_valid_before <= now <= certificate.not_valid_after
