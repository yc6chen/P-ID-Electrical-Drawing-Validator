"""
PyInstaller specification file for creating standalone executable.

To build the application:
1. Install PyInstaller: pip install pyinstaller
2. Run: pyinstaller build_spec.py

This will create a dist/ directory with the executable.
"""

import os
import sys

# Application info
app_name = "EngineeringDrawingValidator"
app_version = "1.0.0"
app_description = "P&ID/Electrical Drawing Validator"

# Determine platform
if sys.platform == 'win32':
    icon_file = 'deployment/icon.ico'
    separator = ';'
elif sys.platform == 'darwin':
    icon_file = 'deployment/icon.icns'
    separator = ':'
else:  # Linux
    icon_file = None
    separator = ':'

# Base directory (project root)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data files to include
datas = [
    # (source, destination_in_bundle)
]

# Check if templates directory exists and add it
templates_dir = os.path.join(base_dir, '..', 'templates')
if os.path.exists(templates_dir):
    datas.append((templates_dir, 'templates'))

# Hidden imports (PyInstaller often misses these)
hiddenimports = [
    'pytesseract',
    'easyocr',
    'fitz',  # PyMuPDF
    'PyMuPDF',
    'cv2',
    'numpy',
    'PIL',
    'PIL._imaging',
    'PIL.Image',
    'reportlab',
    'reportlab.graphics',
    'reportlab.lib',
    'reportlab.platypus',
    'pandas',
    'pandas._libs',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
]

# Exclude unnecessary packages to reduce size
excludes = [
    'tkinter.test',
    'test',
    'unittest',
    'pytest',
    'scipy',
    'matplotlib',
    'sklearn',
    'torch',
    'tensorflow',
]

# Analysis
a = Analysis(
    ['../main.py'],
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ (Python Zip)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX (if available)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if icon_file and os.path.exists(icon_file) else None,
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name=f'{app_name}.app',
        icon=icon_file,
        bundle_identifier=f'com.engineeringvalidator.{app_name.lower()}',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleName': app_name,
            'CFBundleDisplayName': app_description,
            'CFBundleVersion': app_version,
            'CFBundleShortVersionString': app_version,
        },
    )
