"""
Test script for Phase 5 digital signature validation.

This script demonstrates the digital signature validation capabilities
without requiring a full application run.
"""

import sys
import os

# Add drawing_validator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'drawing_validator'))

def test_trust_store():
    """Test trust store initialization and certificate loading."""
    print("\n" + "="*70)
    print("TEST 1: Trust Store Initialization")
    print("="*70)

    try:
        from digital.trust_store import TrustStore

        trust_store = TrustStore()
        cert_count = trust_store.get_certificate_count()

        print(f"✓ Trust store initialized successfully")
        print(f"✓ Loaded {cert_count} trusted certificates")

        associations = trust_store.list_associations()
        if associations:
            print(f"✓ Configured associations: {', '.join(associations)}")
        else:
            print("  No association-specific certificates configured yet")

        return True

    except Exception as e:
        print(f"✗ Trust store test failed: {str(e)}")
        return False


def test_signature_extractor():
    """Test signature extractor initialization."""
    print("\n" + "="*70)
    print("TEST 2: Digital Signature Extractor")
    print("="*70)

    try:
        from digital.signature_extractor import DigitalSignatureExtractor

        extractor = DigitalSignatureExtractor()

        print(f"✓ Signature extractor initialized")
        print(f"✓ Supported signature types:")
        for sig_type in extractor.supported_signature_types:
            print(f"    - {sig_type}")

        return True

    except Exception as e:
        print(f"✗ Signature extractor test failed: {str(e)}")
        return False


def test_certificate_validator():
    """Test certificate validator initialization."""
    print("\n" + "="*70)
    print("TEST 3: Certificate Validator")
    print("="*70)

    try:
        from digital.trust_store import TrustStore
        from digital.certificate_validator import CertificateValidator

        trust_store = TrustStore()
        validator = CertificateValidator(trust_store)

        print(f"✓ Certificate validator initialized")
        print(f"✓ Association mappings configured:")
        for association in validator.association_cert_mappings.keys():
            print(f"    - {association}")

        return True

    except Exception as e:
        print(f"✗ Certificate validator test failed: {str(e)}")
        return False


def test_hybrid_validator():
    """Test hybrid validator initialization."""
    print("\n" + "="*70)
    print("TEST 4: Hybrid Validator")
    print("="*70)

    try:
        from hybrid.dual_validator import HybridValidator
        from digital.trust_store import TrustStore

        trust_store = TrustStore()
        hybrid_validator = HybridValidator(trust_store=trust_store)

        print(f"✓ Hybrid validator initialized")
        print(f"✓ Compliance rules:")
        for rule, value in hybrid_validator.compliance_rules.items():
            print(f"    - {rule}: {value}")

        return True

    except Exception as e:
        print(f"✗ Hybrid validator test failed: {str(e)}")
        return False


def test_data_models():
    """Test digital signature data models."""
    print("\n" + "="*70)
    print("TEST 5: Data Models")
    print("="*70)

    try:
        from digital.digital_models import (
            DigitalSignature,
            CertificateValidationResult,
            DigitalSignatureValidationResult
        )
        import datetime

        # Create sample digital signature
        sig = DigitalSignature(
            signature_type='Adobe.PPKLite',
            signature_bytes=b'test',
            signer_name='Test Signer',
            signer_email='test@example.com',
            signing_time=datetime.datetime.now()
        )

        print(f"✓ DigitalSignature model created")
        print(f"  - Type: {sig.signature_type}")
        print(f"  - Signer: {sig.signer_name}")
        print(f"  - Email: {sig.signer_email}")

        # Test serialization
        sig_dict = sig.to_dict()
        print(f"✓ Signature serialized to dict ({len(sig_dict)} fields)")

        return True

    except Exception as e:
        print(f"✗ Data models test failed: {str(e)}")
        return False


def test_ui_components():
    """Test UI component imports."""
    print("\n" + "="*70)
    print("TEST 6: UI Components")
    print("="*70)

    try:
        from ui.digital_panel import DigitalSignaturePanel
        from ui.certificate_viewer import CertificateViewerDialog

        print(f"✓ DigitalSignaturePanel imported successfully")
        print(f"✓ CertificateViewerDialog imported successfully")

        return True

    except Exception as e:
        print(f"✗ UI components test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PHASE 5: DIGITAL SIGNATURE VALIDATION - TEST SUITE")
    print("="*70)

    tests = [
        ("Trust Store", test_trust_store),
        ("Signature Extractor", test_signature_extractor),
        ("Certificate Validator", test_certificate_validator),
        ("Hybrid Validator", test_hybrid_validator),
        ("Data Models", test_data_models),
        ("UI Components", test_ui_components),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Phase 5 implementation is ready.")
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please check the errors above.")

    print("="*70 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
