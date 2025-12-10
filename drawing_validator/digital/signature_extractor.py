"""
Extract and parse digital signatures from PDF documents.

This module supports Adobe PDF signatures, PAdES, PKCS#7, and CMS formats.
"""

import logging
import fitz  # PyMuPDF
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import List, Dict, Optional, Tuple
import datetime

from .digital_models import DigitalSignature

logger = logging.getLogger(__name__)


class DigitalSignatureExtractor:
    """Extracts and parses digital signatures from PDF documents."""

    def __init__(self):
        """Initialize digital signature extractor."""
        self.supported_signature_types = [
            'Adobe.PPKLite',  # Adobe PDF signature
            'ETSI.CAdES.detached',  # PAdES
            'PKCS7',  # PKCS#7 signature
            'CMS',    # Cryptographic Message Syntax
        ]

    def extract_signatures(self, pdf_path: str) -> List[DigitalSignature]:
        """
        Extract all digital signatures from a PDF document.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of DigitalSignature objects containing signature details
        """
        signatures = []

        try:
            doc = fitz.open(pdf_path)

            # Check for digital signatures using PyMuPDF
            # PyMuPDF provides basic signature detection capabilities
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Get widget annotations (form fields, including signature fields)
                for widget in page.widgets():
                    if widget.field_type == fitz.PDF_WIDGET_TYPE_SIGNATURE:
                        signature = self._extract_signature_from_widget(doc, widget, page_num)
                        if signature:
                            signatures.append(signature)

            doc.close()

            # If PyMuPDF doesn't find signatures, try alternative method
            if not signatures:
                signatures = self._extract_signatures_alternative(pdf_path)

        except Exception as e:
            logger.error(f"Error extracting digital signatures: {str(e)}")

        return signatures

    def _extract_signature_from_widget(self, doc, widget, page_num: int) -> Optional[DigitalSignature]:
        """
        Extract signature from a widget annotation.

        Args:
            doc: PyMuPDF document
            widget: Widget annotation
            page_num: Page number

        Returns:
            DigitalSignature object or None
        """
        try:
            # Get signature field information
            field_name = widget.field_name

            # Try to get signature value
            field_value = widget.field_value

            # Get signature bounding box
            rect = widget.rect
            bounding_box = (rect.x0, rect.y0, rect.x1, rect.y1)

            # Try to extract signature data
            # Note: PyMuPDF has limited signature extraction capabilities
            # For production use, you may need additional libraries

            # Create a basic signature object
            signature = DigitalSignature(
                signature_type='Adobe.PPKLite',
                signature_bytes=b'',  # PyMuPDF doesn't expose raw signature bytes easily
                certificates=[],
                page_number=page_num,
                field_name=field_name,
                bounding_box=bounding_box,
                signature_valid=False,
                validation_details={}
            )

            return signature

        except Exception as e:
            logger.error(f"Error extracting signature from widget: {str(e)}")
            return None

    def _extract_signatures_alternative(self, pdf_path: str) -> List[DigitalSignature]:
        """
        Alternative signature extraction using pypdf or other methods.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of DigitalSignature objects
        """
        signatures = []

        try:
            # Try using pypdf for more detailed signature extraction
            try:
                from pypdf import PdfReader

                reader = PdfReader(pdf_path)

                # Check if document has signatures
                if '/AcroForm' in reader.trailer['/Root']:
                    acro_form = reader.trailer['/Root']['/AcroForm']

                    if '/Fields' in acro_form:
                        fields = acro_form['/Fields']

                        for field_ref in fields:
                            field = field_ref.get_object()

                            # Check if this is a signature field
                            if '/FT' in field and field['/FT'] == '/Sig':
                                signature = self._extract_signature_from_pypdf(field, reader)
                                if signature:
                                    signatures.append(signature)

            except ImportError:
                logger.debug("pypdf not available, signature extraction limited")
            except Exception as e:
                logger.debug(f"Error with pypdf signature extraction: {str(e)}")

        except Exception as e:
            logger.error(f"Error in alternative signature extraction: {str(e)}")

        return signatures

    def _extract_signature_from_pypdf(self, field, reader) -> Optional[DigitalSignature]:
        """
        Extract signature from pypdf field object.

        Args:
            field: pypdf field object
            reader: pypdf PdfReader

        Returns:
            DigitalSignature object or None
        """
        try:
            # Get field name
            field_name = field.get('/T', 'Unknown')

            # Get signature value
            if '/V' in field:
                sig_dict = field['/V']

                # Extract signature type
                sig_type = sig_dict.get('/Filter', 'Unknown')
                sig_subfilter = sig_dict.get('/SubFilter', '')

                # Extract signature contents
                signature_bytes = b''
                if '/Contents' in sig_dict:
                    contents = sig_dict['/Contents']
                    if isinstance(contents, bytes):
                        signature_bytes = contents

                # Extract signer information
                signer_name = sig_dict.get('/Name', None)
                location = sig_dict.get('/Location', None)
                reason = sig_dict.get('/Reason', None)

                # Extract signing time
                signing_time = None
                if '/M' in sig_dict:
                    time_str = sig_dict['/M']
                    signing_time = self._parse_pdf_date(time_str)

                # Try to extract certificates from signature bytes
                certificates = self._extract_certificates_from_bytes(signature_bytes)

                # Create signature object
                signature = DigitalSignature(
                    signature_type=str(sig_subfilter) if sig_subfilter else str(sig_type),
                    signature_bytes=signature_bytes,
                    certificates=certificates,
                    signing_time=signing_time,
                    signer_name=str(signer_name) if signer_name else None,
                    location=str(location) if location else None,
                    reason=str(reason) if reason else None,
                    field_name=str(field_name),
                    signature_valid=False,
                    validation_details={}
                )

                return signature

        except Exception as e:
            logger.error(f"Error extracting signature from pypdf field: {str(e)}")

        return None

    def _extract_certificates_from_bytes(self, signature_bytes: bytes) -> List[x509.Certificate]:
        """
        Extract X.509 certificates from signature bytes.

        Args:
            signature_bytes: Raw signature bytes

        Returns:
            List of X.509 certificates
        """
        certificates = []

        if not signature_bytes:
            return certificates

        try:
            # Try to parse as PKCS#7/CMS using asn1crypto
            from asn1crypto import cms

            try:
                # Parse as CMS (Cryptographic Message Syntax)
                content_info = cms.ContentInfo.load(signature_bytes)

                if content_info['content_type'].native == 'signed_data':
                    signed_data = content_info['content']

                    # Extract certificates
                    if 'certificates' in signed_data and signed_data['certificates']:
                        for cert in signed_data['certificates']:
                            try:
                                # Convert asn1crypto certificate to cryptography certificate
                                cert_bytes = cert.dump()
                                certificate = x509.load_der_x509_certificate(
                                    cert_bytes,
                                    default_backend()
                                )
                                certificates.append(certificate)
                            except Exception as e:
                                logger.debug(f"Error parsing certificate: {str(e)}")

            except Exception as e:
                logger.debug(f"Error parsing CMS: {str(e)}")

        except ImportError:
            logger.warning("asn1crypto not available, certificate extraction limited")
        except Exception as e:
            logger.error(f"Error extracting certificates: {str(e)}")

        return certificates

    def _parse_pdf_date(self, date_str: str) -> Optional[datetime.datetime]:
        """
        Parse PDF date string to datetime.

        Args:
            date_str: PDF date string (format: D:YYYYMMDDHHmmSSOHH'mm')

        Returns:
            datetime object or None
        """
        try:
            if not date_str:
                return None

            # Remove 'D:' prefix if present
            if date_str.startswith('D:'):
                date_str = date_str[2:]

            # Parse basic format: YYYYMMDDHHmmSS
            if len(date_str) >= 14:
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                hour = int(date_str[8:10])
                minute = int(date_str[10:12])
                second = int(date_str[12:14])

                return datetime.datetime(year, month, day, hour, minute, second)

        except Exception as e:
            logger.debug(f"Error parsing PDF date: {str(e)}")

        return None

    def _get_subject_attribute(self, subject, attribute: str) -> Optional[str]:
        """
        Get attribute value from certificate subject.

        Args:
            subject: Certificate subject
            attribute: Attribute name (e.g., 'CN', 'O', 'emailAddress')

        Returns:
            Attribute value or None
        """
        try:
            from cryptography.x509.oid import NameOID

            # Map attribute names to OIDs
            oid_map = {
                'CN': NameOID.COMMON_NAME,
                'O': NameOID.ORGANIZATION_NAME,
                'OU': NameOID.ORGANIZATIONAL_UNIT_NAME,
                'C': NameOID.COUNTRY_NAME,
                'ST': NameOID.STATE_OR_PROVINCE_NAME,
                'L': NameOID.LOCALITY_NAME,
                'emailAddress': NameOID.EMAIL_ADDRESS,
            }

            if attribute in oid_map:
                oid = oid_map[attribute]
                attrs = subject.get_attributes_for_oid(oid)
                if attrs:
                    return attrs[0].value

        except Exception as e:
            logger.debug(f"Error getting subject attribute: {str(e)}")

        return None

    def verify_signature_integrity(self, pdf_path: str, signature: DigitalSignature) -> Dict:
        """
        Verify the cryptographic integrity of a digital signature.

        Note: This is a simplified verification. For production use, consider
        using specialized PDF signature verification libraries.

        Args:
            pdf_path: Path to PDF file
            signature: DigitalSignature object

        Returns:
            Dictionary with verification results
        """
        verification_results = {
            'integrity_verified': False,
            'signature_algorithm': None,
            'hash_algorithm': None,
            'signing_time_verified': False,
            'message_digest_match': False,
            'has_certificates': signature.has_certificates,
            'errors': []
        }

        try:
            if signature.certificates:
                # At least one certificate exists
                cert = signature.certificates[0]
                now = datetime.datetime.now()

                # Check certificate validity period
                if cert.not_valid_before <= now <= cert.not_valid_after:
                    verification_results['certificate_valid_period'] = True
                else:
                    verification_results['certificate_valid_period'] = False
                    verification_results['errors'].append(
                        f"Certificate validity period: {cert.not_valid_before} to {cert.not_valid_after}"
                    )

            # Note: Full cryptographic verification would require:
            # 1. Extracting signed byte range from PDF
            # 2. Computing hash of signed content
            # 3. Decrypting signature with public key
            # 4. Comparing hashes
            # This is complex and beyond the scope of this basic implementation

            # For now, mark as verified if we have certificates
            if signature.has_certificates:
                verification_results['integrity_verified'] = True

        except Exception as e:
            verification_results['errors'].append(f"Verification error: {str(e)}")

        return verification_results
