"""
Script to create placeholder template images for seal detection.

This creates sample template images for testing the detection system.
Real templates should be extracted from actual engineering seals.
"""

import cv2
import numpy as np
from pathlib import Path


def create_circular_seal_template(size=100, color=(0, 0, 255)):
    """Create a circular seal placeholder."""
    # Create blank image
    img = np.ones((size, size, 3), dtype=np.uint8) * 255

    # Draw outer circle
    center = (size // 2, size // 2)
    cv2.circle(img, center, size // 2 - 5, color, 3)
    cv2.circle(img, center, size // 2 - 15, color, 2)

    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "P.ENG", (size // 2 - 30, size // 2), font, 0.5, color, 2)
    cv2.putText(img, "SEAL", (size // 2 - 25, size // 2 + 15), font, 0.4, color, 1)

    return img


def create_rectangular_signature_block(width=300, height=80):
    """Create a rectangular signature block placeholder."""
    # Create blank image
    img = np.ones((height, width, 3), dtype=np.uint8) * 255

    # Draw border
    cv2.rectangle(img, (5, 5), (width - 5, height - 5), (0, 0, 0), 2)

    # Add horizontal divider
    cv2.line(img, (5, height // 2), (width - 5, height // 2), (0, 0, 0), 1)

    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "Signature", (20, 30), font, 0.6, (0, 0, 0), 1)
    cv2.putText(img, "Date", (20, 65), font, 0.5, (0, 0, 0), 1)

    return img


def main():
    """Create all placeholder templates."""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)

    print("Creating placeholder template images...")

    # Create APEGA seal (Alberta - red)
    apega_seal = create_circular_seal_template(100, (0, 0, 200))
    cv2.imwrite(str(templates_dir / "apega_seal_placeholder.png"), apega_seal)
    print("  - Created: apega_seal_placeholder.png (100x100)")

    # Create EGBC seal (British Columbia - blue)
    egbc_seal = create_circular_seal_template(100, (200, 0, 0))
    cv2.imwrite(str(templates_dir / "egbc_seal_placeholder.png"), egbc_seal)
    print("  - Created: egbc_seal_placeholder.png (100x100)")

    # Create APEGS seal (Saskatchewan - red)
    apegs_seal = create_circular_seal_template(90, (0, 0, 180))
    cv2.imwrite(str(templates_dir / "apegs_seal_placeholder.png"), apegs_seal)
    print("  - Created: apegs_seal_placeholder.png (90x90)")

    # Create signature block template
    sig_block = create_rectangular_signature_block(300, 80)
    cv2.imwrite(str(templates_dir / "signature_block_placeholder.png"), sig_block)
    print("  - Created: signature_block_placeholder.png (300x80)")

    # Create smaller signature block
    sig_block_small = create_rectangular_signature_block(200, 60)
    cv2.imwrite(str(templates_dir / "signature_block_small_placeholder.png"), sig_block_small)
    print("  - Created: signature_block_small_placeholder.png (200x60)")

    print("\nPlaceholder templates created successfully!")
    print("Note: These are placeholders. For real use, extract templates from actual engineering seals.")


if __name__ == "__main__":
    main()
