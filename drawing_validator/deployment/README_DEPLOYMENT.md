# Deployment Guide

This guide explains how to build standalone executables for the Engineering Drawing Validator application.

## Prerequisites

1. **Python 3.8+** installed
2. **All dependencies** installed from `requirements.txt`
3. **PyInstaller** installed: `pip install pyinstaller`
4. **Tesseract-OCR** installed on build machine (see main README)

## Building the Application

### Windows

```bash
cd drawing_validator/deployment
pyinstaller build_spec.py
```

The executable will be created in `dist/EngineeringDrawingValidator.exe`

### macOS

```bash
cd drawing_validator/deployment
pyinstaller build_spec.py
```

The application bundle will be created in `dist/EngineeringDrawingValidator.app`

### Linux

```bash
cd drawing_validator/deployment
pyinstaller build_spec.py
```

The executable will be created in `dist/EngineeringDrawingValidator`

## Building for Distribution

### 1. Clean Build

Before creating a distribution build, clean previous builds:

```bash
# Remove old build artifacts
rm -rf build/ dist/
```

### 2. Build with Optimizations

```bash
pyinstaller build_spec.py --clean
```

### 3. Test the Executable

Always test the built executable before distribution:

```bash
# Windows
dist/EngineeringDrawingValidator.exe

# macOS
open dist/EngineeringDrawingValidator.app

# Linux
./dist/EngineeringDrawingValidator
```

## Distribution Package Contents

When distributing the application, include:

1. **Executable**: The built application
2. **Templates**: Engineering seal templates (place in same directory)
3. **User Guide**: Documentation for end users
4. **Tesseract Installation Instructions**: Since Tesseract must be installed separately

### Example Distribution Structure

```
EngineeringDrawingValidator/
├── EngineeringDrawingValidator.exe  (or .app on macOS)
├── templates/
│   ├── apega_seal_placeholder.png
│   ├── apegs_seal_placeholder.png
│   ├── egbc_seal_placeholder.png
│   └── ...
├── UserGuide.pdf
└── README.txt
```

## Troubleshooting

### Issue: "Failed to execute script"

**Solution**: The executable is missing dependencies. Check:
- All required DLLs/libraries are included
- Tesseract is installed on the target system
- Python runtime is properly bundled

### Issue: Large executable size

**Solution**:
- Ensure `excludes` list in `build_spec.py` includes unnecessary packages
- Use UPX compression (enabled by default)
- Consider using `--onefile` mode in PyInstaller

### Issue: Slow startup time

**Solution**:
- This is normal for PyInstaller bundles
- First launch extracts files to temporary directory
- Subsequent launches should be faster

### Issue: Tesseract not found

**Solution**:
- Tesseract-OCR must be installed separately on user machines
- Provide installation instructions with distribution
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

## Platform-Specific Notes

### Windows

- **Antivirus**: Some antivirus software may flag PyInstaller executables as suspicious
- **Code Signing**: Consider code signing the executable for production distribution
- **Installer**: Use NSIS or Inno Setup to create an installer

### macOS

- **Gatekeeper**: Users may need to right-click > Open to bypass Gatekeeper
- **Code Signing**: Consider signing the app bundle for distribution
- **Notarization**: Required for distribution outside App Store (macOS 10.15+)
- **DMG Creation**: Create a DMG for easier distribution

### Linux

- **Permissions**: Make executable: `chmod +x EngineeringDrawingValidator`
- **Dependencies**: Users may need to install system libraries
- **Desktop Entry**: Create a .desktop file for menu integration

## Creating Installers (Optional)

### Windows (NSIS)

1. Install NSIS: https://nsis.sourceforge.io/
2. Create installer script (see example below)
3. Compile with NSIS

### macOS (DMG)

```bash
# Create DMG
hdiutil create -volname "Engineering Drawing Validator" \
    -srcfolder dist/EngineeringDrawingValidator.app \
    -ov -format UDZO EngineeringDrawingValidator.dmg
```

### Linux (AppImage)

Consider using AppImage for universal Linux distribution.

## Version Management

Update version numbers in:
1. `build_spec.py` - `app_version`
2. `drawing_validator/core/settings.py` - `APP_VERSION`
3. Documentation files

## Distribution Checklist

Before releasing:

- [ ] All features tested in built executable
- [ ] Version numbers updated
- [ ] Templates included
- [ ] Documentation updated
- [ ] Installation instructions verified
- [ ] Tested on clean machine (no dev environment)
- [ ] Antivirus scanned (Windows)
- [ ] Code signed (production only)
- [ ] Release notes prepared

## Support

For build issues or questions, refer to:
- PyInstaller documentation: https://pyinstaller.org/
- Project README
- Issue tracker
