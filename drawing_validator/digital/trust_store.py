"""
Manage trusted root certificates and certificate stores.

This module provides functionality for managing trusted root certificates,
loading system certificate stores, and mapping certificates to engineering associations.
"""

import os
import logging
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from typing import List, Dict, Set, Optional

logger = logging.getLogger(__name__)


class TrustStore:
    """Manages trusted root certificates and certificate stores."""

    def __init__(self, store_path: str = None):
        """
        Initialize trust store.

        Args:
            store_path: Path to store trusted certificates (default: data/certificates/trusted_roots)
        """
        if store_path is None:
            # Get the path relative to the project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            store_path = os.path.join(project_root, 'drawing_validator', 'data', 'certificates', 'trusted_roots')

        self.store_path = store_path
        self.trusted_certificates = {}  # fingerprint -> certificate
        self.association_certificates = {}  # association -> [certificates]

        # Ensure store directory exists
        os.makedirs(self.store_path, exist_ok=True)

        self._load_trust_store()
        self._load_system_trust_store()

    def _load_trust_store(self):
        """Load trusted certificates from local store."""
        if not os.path.exists(self.store_path):
            os.makedirs(self.store_path, exist_ok=True)
            return

        # Load from PEM files
        for filename in os.listdir(self.store_path):
            if filename.endswith('.pem') or filename.endswith('.crt'):
                filepath = os.path.join(self.store_path, filename)
                try:
                    with open(filepath, 'rb') as f:
                        cert_data = f.read()
                        certificate = x509.load_pem_x509_certificate(cert_data, default_backend())

                        # Store by fingerprint
                        fingerprint = self._get_certificate_fingerprint(certificate)
                        self.trusted_certificates[fingerprint] = certificate

                except Exception as e:
                    logger.error(f"Error loading certificate {filename}: {str(e)}")

    def _load_system_trust_store(self):
        """Load system's trusted root certificates."""
        try:
            # Try to load system CA certificates using certifi
            import certifi

            # Load from certifi (cross-platform)
            with open(certifi.where(), 'rb') as f:
                cert_data = f.read()
                self._load_pem_bundle(cert_data)

        except ImportError:
            logger.warning("certifi not available, using limited trust store")
        except Exception as e:
            logger.error(f"Error loading certifi trust store: {str(e)}")

        # Also try platform-specific stores
        self._load_platform_trust_store()

    def _load_pem_bundle(self, pem_data: bytes):
        """Load multiple PEM-encoded certificates from a bundle."""
        # Split on certificate boundaries
        pem_text = pem_data.decode('utf-8', errors='ignore')
        cert_blocks = []
        current_block = []

        for line in pem_text.split('\n'):
            if '-----BEGIN CERTIFICATE-----' in line:
                current_block = [line]
            elif '-----END CERTIFICATE-----' in line:
                current_block.append(line)
                cert_blocks.append('\n'.join(current_block))
                current_block = []
            elif current_block:
                current_block.append(line)

        # Load each certificate
        for cert_pem in cert_blocks:
            try:
                cert_bytes = cert_pem.encode('utf-8')
                certificate = x509.load_pem_x509_certificate(cert_bytes, default_backend())

                fingerprint = self._get_certificate_fingerprint(certificate)
                self.trusted_certificates[fingerprint] = certificate

            except Exception as e:
                logger.debug(f"Error loading certificate from bundle: {str(e)}")

    def _load_platform_trust_store(self):
        """Load platform-specific trust stores."""
        import platform

        system = platform.system()

        if system == 'Windows':
            self._load_windows_store()
        elif system == 'Darwin':  # macOS
            self._load_macos_store()
        elif system == 'Linux':
            self._load_linux_store()

    def _load_windows_store(self):
        """Load Windows certificate store."""
        try:
            import ssl
            import certifi

            # Windows certificate stores are already handled by certifi
            # This is a placeholder for advanced Windows store access
            logger.debug("Windows trust store loaded via certifi")

        except Exception as e:
            logger.debug(f"Error loading Windows trust store: {str(e)}")

    def _load_macos_store(self):
        """Load macOS Keychain certificates."""
        try:
            # macOS certificates are already handled by certifi
            # This is a placeholder for advanced Keychain access
            logger.debug("macOS trust store loaded via certifi")

        except Exception as e:
            logger.debug(f"Error loading macOS trust store: {str(e)}")

    def _load_linux_store(self):
        """Load Linux system certificates."""
        # Common Linux certificate paths
        cert_paths = [
            '/etc/ssl/certs/ca-certificates.crt',  # Debian/Ubuntu
            '/etc/pki/tls/certs/ca-bundle.crt',    # RedHat/CentOS
            '/etc/ssl/ca-bundle.pem',               # OpenSUSE
            '/etc/ssl/cert.pem',                    # Alpine
        ]

        for cert_path in cert_paths:
            if os.path.exists(cert_path):
                try:
                    with open(cert_path, 'rb') as f:
                        cert_data = f.read()
                        self._load_pem_bundle(cert_data)
                    logger.debug(f"Loaded Linux certificates from {cert_path}")
                    break
                except Exception as e:
                    logger.debug(f"Error loading certificates from {cert_path}: {str(e)}")

    def is_trusted(self, certificate: x509.Certificate) -> bool:
        """
        Check if certificate is in trust store.

        Args:
            certificate: Certificate to check

        Returns:
            True if certificate is trusted, False otherwise
        """
        fingerprint = self._get_certificate_fingerprint(certificate)
        return fingerprint in self.trusted_certificates

    def find_issuer(self, certificate: x509.Certificate) -> Optional[x509.Certificate]:
        """
        Find issuer certificate in trust store.

        Args:
            certificate: Certificate whose issuer to find

        Returns:
            Issuer certificate if found, None otherwise
        """
        issuer_name = certificate.issuer

        for trusted_cert in self.trusted_certificates.values():
            if trusted_cert.subject == issuer_name:
                return trusted_cert

        return None

    def add_certificate(self, certificate: x509.Certificate, association: str = None) -> bool:
        """
        Add certificate to trust store.

        Args:
            certificate: Certificate to add
            association: Optional engineering association to associate with

        Returns:
            True if added successfully, False otherwise
        """
        try:
            fingerprint = self._get_certificate_fingerprint(certificate)
            self.trusted_certificates[fingerprint] = certificate

            if association:
                if association not in self.association_certificates:
                    self.association_certificates[association] = []
                self.association_certificates[association].append(certificate)

            # Save to file
            self._save_certificate_to_file(certificate)

            return True

        except Exception as e:
            logger.error(f"Error adding certificate to trust store: {str(e)}")
            return False

    def remove_certificate(self, fingerprint: str) -> bool:
        """
        Remove certificate from trust store.

        Args:
            fingerprint: SHA-256 fingerprint of certificate to remove

        Returns:
            True if removed successfully, False otherwise
        """
        if fingerprint in self.trusted_certificates:
            del self.trusted_certificates[fingerprint]

            # Remove from association mappings
            for association, certs in self.association_certificates.items():
                self.association_certificates[association] = [
                    cert for cert in certs
                    if self._get_certificate_fingerprint(cert) != fingerprint
                ]

            # Remove file
            self._remove_certificate_file(fingerprint)

            return True

        return False

    def get_association_certificates(self, association: str) -> List[x509.Certificate]:
        """
        Get certificates associated with an engineering association.

        Args:
            association: Association name (e.g., 'APEGA', 'APEGS')

        Returns:
            List of certificates for the association
        """
        return self.association_certificates.get(association, [])

    def _get_certificate_fingerprint(self, certificate: x509.Certificate) -> str:
        """
        Get SHA-256 fingerprint of certificate.

        Args:
            certificate: Certificate to fingerprint

        Returns:
            Hexadecimal fingerprint string
        """
        cert_bytes = certificate.public_bytes(encoding=serialization.Encoding.DER)
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(cert_bytes)
        fingerprint = digest.finalize().hex()
        return fingerprint

    def _save_certificate_to_file(self, certificate: x509.Certificate):
        """Save certificate to PEM file."""
        fingerprint = self._get_certificate_fingerprint(certificate)
        filename = f"{fingerprint}.pem"
        filepath = os.path.join(self.store_path, filename)

        with open(filepath, 'wb') as f:
            f.write(certificate.public_bytes(encoding=serialization.Encoding.PEM))

    def _remove_certificate_file(self, fingerprint: str):
        """Remove certificate file from trust store."""
        filename = f"{fingerprint}.pem"
        filepath = os.path.join(self.store_path, filename)

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                logger.error(f"Error removing certificate file: {str(e)}")

    def get_certificate_count(self) -> int:
        """Get total number of trusted certificates."""
        return len(self.trusted_certificates)

    def list_associations(self) -> List[str]:
        """Get list of associations with certificates."""
        return list(self.association_certificates.keys())
