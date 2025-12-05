# Engineering Seal Templates

This directory contains template images used for seal detection.

## Creating Templates

After installing dependencies, run:

```bash
python create_placeholder_templates.py
```

This will create placeholder template images for testing:
- `apega_seal_placeholder.png` - APEGA (Alberta) seal template
- `egbc_seal_placeholder.png` - EGBC (British Columbia) seal template
- `apegs_seal_placeholder.png` - APEGS (Saskatchewan) seal template
- `signature_block_placeholder.png` - Standard signature block template
- `signature_block_small_placeholder.png` - Small signature block template

## Using Real Templates

For production use, replace placeholders with real seal templates:

1. Extract clear images of engineering seals from sample drawings
2. Crop to show only the seal (100x100 to 150x150 pixels recommended)
3. Save as PNG files in this directory
4. Name files descriptively (e.g., `apega_seal_actual.png`)

## Template Guidelines

- **Format**: PNG with transparency preferred
- **Size**: 80-150 pixels for circular seals, variable for signature blocks
- **Quality**: High resolution, clear features
- **Background**: White or transparent background
- **Naming**: Use descriptive names (association_type_variant.png)

## Supported Formats

Template images can be:
- PNG (preferred)
- JPEG/JPG
- Other formats supported by OpenCV

The template matcher will automatically load all image files from this directory.
