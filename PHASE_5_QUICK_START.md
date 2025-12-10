# Phase 5: Digital Signature Validation - Quick Start Guide

## 🚀 Installation Complete!

All Phase 5 dependencies have been successfully installed:
- ✅ cryptography
- ✅ pyOpenSSL
- ✅ asn1crypto
- ✅ certvalidator
- ✅ requests
- ✅ certifi

**Trust Store Status**: 146 system root certificates loaded automatically

## 🎯 What's New

Your Drawing Validator can now validate:
1. **Image-based seals** (existing functionality from Phases 1-4)
2. **Digital signatures** (NEW in Phase 5)
3. **Both types simultaneously** with unified reporting

## 📖 How to Use

### Running the Application

```bash
# Start the application
python3 drawing_validator/main.py
```

### What Happens Automatically

When you load a PDF file, the application will:
1. ✓ Detect image-based seals (color, template, contour detection)
2. ✓ Extract text with OCR and validate associations
3. ✓ **NEW**: Detect digital signatures in the PDF
4. ✓ **NEW**: Validate certificate chains
5. ✓ **NEW**: Map certificates to engineering associations
6. ✓ **NEW**: Combine results from both methods

### Viewing Results

The application will show:
- **Seal validation results** (existing panel)
- **Digital signature results** (new panel):
  - Number of signatures found
  - Validation status (valid/invalid)
  - Trust status (fully trusted, partially trusted, untrusted)
  - Certificate associations (APEGA, APEGS, EGBC, EGM)
  - Signer information

### Exporting Results

When you export to PDF or CSV:
- **PDF Reports** include a "Digital Signature Validation" section
- **CSV Exports** include new columns:
  - `Digital Signatures Found`
  - `Total Digital Signatures`
  - `Valid Digital Signatures`
  - `Digital Trust Status`
  - `Certificate Associations`

## 🔧 Configuration

### Compliance Rules

Default behavior (configurable in `hybrid/dual_validator.py`):
- ✅ Accept **either** image seal OR digital signature
- ❌ Does NOT require both (but can be configured to require both)
- Minimum seal confidence: 0.7

### Trust Store

**System Certificates**: Automatically loaded (146 certificates)

**Adding Custom Certificates**:
1. Place certificate files in: `drawing_validator/data/certificates/trusted_roots/`
2. Supported formats: `.pem` or `.crt`
3. Restart application to reload

**Association-Specific Certificates**:
1. Place in: `drawing_validator/data/certificates/association_certs/`
2. Certificates will be mapped to specific associations

## 🧪 Testing

### Verify Installation
```bash
python3 test_digital_signatures.py
```

Expected output: `✓ All tests passed! Phase 5 implementation is ready.`

### Test with Sample Files

**Documents with digital signatures:**
- Adobe Acrobat signed PDFs
- DocuSign signed PDFs
- Government/official documents with digital signatures

**Documents with image seals:**
- Traditional P&ID drawings with stamped seals
- Scanned engineering documents

**Documents with both:**
- Modern engineering drawings with both stamp and digital signature

## 📊 Understanding Results

### Validation Status

**Overall Valid**: Document meets compliance requirements
- Has valid image seal AND/OR valid digital signature
- Meets configured compliance rules
- Confidence above minimum threshold (for seals)

**Compliance Status**:
- `COMPLIANT`: Valid with association match
- `COMPLIANT_NO_ASSOCIATION`: Valid but no association identified
- `NON_COMPLIANT`: Does not meet requirements

### Trust Status (Digital Signatures)

- `fully_trusted`: All signatures valid, all certificates trusted
- `partially_trusted`: Some signatures valid
- `untrusted`: No valid signatures
- `no_signatures`: No digital signatures found

## 🔍 Digital Signature Details

### Supported Formats
- Adobe PDF signatures (Adobe.PPKLite)
- PAdES (European standard)
- PKCS#7 (Cryptographic Message Syntax)
- CMS signatures

### Certificate Validation
- ✅ Chain validation to trusted roots
- ✅ Validity period checking
- ✅ Key usage validation
- ✅ Association mapping (keyword and policy-based)
- 🔄 Revocation checking (infrastructure ready, requires configuration)

### Association Mapping

Certificates are mapped to associations based on:
1. **Subject fields**: Organization name, common name, email domain
2. **Certificate policies**: OID-based mapping
3. **Keywords**: Association-specific terms

Supported associations:
- **APEGA**: Association of Professional Engineers and Geoscientists of Alberta
- **APEGS**: Association of Professional Engineers and Geoscientists of Saskatchewan
- **EGBC**: Engineers and Geoscientists British Columbia
- **EGM**: Engineers Geoscientists Manitoba

## 💡 Tips

### For Best Results

1. **Use both signature types** when possible:
   - Image seal for traditional compliance
   - Digital signature for authenticity and integrity

2. **Configure trust anchors** for your organization:
   - Add association CA certificates to trust store
   - Improves association mapping accuracy

3. **Check certificate validity**:
   - Ensure signing certificates are not expired
   - Verify certificate chain is complete

### Troubleshooting

**No digital signatures detected:**
- File may not have embedded digital signatures
- Try opening in Adobe Acrobat to verify signatures exist

**Signatures detected but untrusted:**
- Certificate chain may be incomplete
- Root CA may not be in trust store
- Certificate may be expired or revoked

**Association not matched:**
- Certificate may not contain association identifiers
- Add association-specific certificates to trust store
- Check certificate subject/issuer fields

## 📚 Further Reading

- `PHASE_5_IMPLEMENTATION.md` - Detailed implementation documentation
- `drawing_validator/digital/` - Digital signature module source code
- `drawing_validator/hybrid/` - Hybrid validation module source code

## 🎉 Ready to Go!

Your Drawing Validator now supports comprehensive validation of both traditional image-based seals and modern cryptographic digital signatures. The system automatically detects and validates both types, providing unified compliance checking for all engineering document formats.

**Start validating**: `python3 drawing_validator/main.py`
