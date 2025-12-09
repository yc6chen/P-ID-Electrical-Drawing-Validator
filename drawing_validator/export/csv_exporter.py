"""
Export validation results to CSV for database import or spreadsheet analysis.
"""

import os
import logging
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export validation results to CSV format."""

    def __init__(self):
        """Initialize CSV exporter with field mappings."""
        self.field_mappings = {
            'file_path': 'File Path',
            'file_name': 'File Name',
            'validation_status': 'Validation Status',
            'validation_confidence': 'Validation Confidence',
            'associations': 'Associations',
            'license_numbers': 'License Numbers',
            'processing_time': 'Processing Time (s)',
            'page_count': 'Page Count',
            'valid_pages': 'Valid Pages',
            'invalid_pages': 'Invalid Pages',
            'extracted_text': 'Extracted Text',
            'validation_timestamp': 'Validation Timestamp',
        }

    def export_to_csv(self, batch_result, output_path: str) -> str:
        """
        Export batch results to CSV format.

        Args:
            batch_result: BatchResult object with processing results
            output_path: Path where CSV file should be saved

        Returns:
            Path to created CSV file
        """
        try:
            # Prepare data rows
            rows = []

            for file_result in batch_result.results:
                # Create base row for file
                base_row = self._create_file_row(file_result)

                if hasattr(file_result, 'page_results') and file_result.page_results:
                    # Create detailed rows for each page
                    for page_num, page in enumerate(file_result.page_results):
                        page_row = base_row.copy()
                        page_row.update(self._create_page_row(page, page_num))

                        if hasattr(page, 'region_validations') and page.region_validations:
                            # Create even more detailed rows for each region
                            for region_num, region_validation in enumerate(page.region_validations):
                                region_row = page_row.copy()
                                region_row.update(
                                    self._create_region_row(region_validation, region_num)
                                )
                                rows.append(region_row)
                        else:
                            rows.append(page_row)
                else:
                    rows.append(base_row)

            # Convert to DataFrame for easy CSV export
            if not rows:
                logger.warning("No data to export")
                # Create empty DataFrame with headers
                df = pd.DataFrame(columns=list(self.field_mappings.values()))
            else:
                df = pd.DataFrame(rows)

                # Reorder columns if data exists
                preferred_order = list(self.field_mappings.values())
                existing_columns = [col for col in preferred_order if col in df.columns]
                other_columns = [col for col in df.columns if col not in existing_columns]
                df = df[existing_columns + other_columns]

            # Export to CSV
            df.to_csv(output_path, index=False, encoding='utf-8')

            logger.info(f"Exported {len(rows)} records to CSV: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise

    def _create_file_row(self, file_result) -> Dict[str, Any]:
        """
        Create row for file-level data.

        Args:
            file_result: DrawingValidationResult object

        Returns:
            Dictionary with file-level fields
        """
        row = {
            'File Path': getattr(file_result, 'filepath', ''),
            'File Name': os.path.basename(getattr(file_result, 'filepath', '')),
            'Validation Status': 'Valid' if getattr(file_result, 'overall_valid', False) else 'Invalid',
            'Processing Time (s)': f"{getattr(file_result, 'total_processing_time', 0):.2f}",
            'Page Count': len(getattr(file_result, 'page_results', [])),
            'Validation Timestamp': getattr(file_result, 'timestamp', datetime.now()).isoformat(),
        }

        # Add validation details if available
        if hasattr(file_result, 'page_results') and file_result.page_results:
            valid_pages = sum(
                1 for page in file_result.page_results
                if getattr(page, 'has_valid_signature', False)
            )
            row['Valid Pages'] = valid_pages
            row['Invalid Pages'] = len(file_result.page_results) - valid_pages

        # Add associations and license numbers
        if hasattr(file_result, 'get_all_associations'):
            row['Associations'] = '; '.join(file_result.get_all_associations())
        if hasattr(file_result, 'get_all_license_numbers'):
            row['License Numbers'] = '; '.join(file_result.get_all_license_numbers())

        return row

    def _create_page_row(self, page, page_num: int) -> Dict[str, Any]:
        """
        Create row for page-level data.

        Args:
            page: PageValidationResult object
            page_num: Page number (0-indexed)

        Returns:
            Dictionary with page-level fields
        """
        row = {
            'Page Number': page_num + 1,
            'Page Valid': 'Yes' if getattr(page, 'has_valid_signature', False) else 'No',
            'Valid Regions': getattr(page, 'valid_region_count', 0),
            'Total Regions': len(getattr(page, 'region_validations', [])),
            'Page Processing Time (s)': f"{getattr(page, 'processing_time', 0):.2f}",
        }

        # Collect unique detection methods and extracted text
        if hasattr(page, 'region_validations'):
            methods = set()
            text_snippets = []

            for rv in page.region_validations:
                if hasattr(rv, 'region') and hasattr(rv.region, 'detection_method'):
                    methods.add(rv.region.detection_method)
                if hasattr(rv, 'ocr_result') and hasattr(rv.ocr_result, 'text'):
                    text = rv.ocr_result.text.strip()
                    if text:
                        text_snippets.append(text[:50])  # First 50 chars

            row['Detection Methods Used'] = '; '.join(methods) if methods else "None"
            row['Extracted Text'] = ' | '.join(text_snippets) if text_snippets else "None"

        return row

    def _create_region_row(self, region_validation, region_num: int) -> Dict[str, Any]:
        """
        Create row for region-level data.

        Args:
            region_validation: RegionValidation object
            region_num: Region number (0-indexed)

        Returns:
            Dictionary with region-level fields
        """
        row = {
            'Region Number': region_num + 1,
        }

        # Add region details
        if hasattr(region_validation, 'region'):
            region = region_validation.region
            row['Region X'] = getattr(region, 'x', 0)
            row['Region Y'] = getattr(region, 'y', 0)
            row['Region Width'] = getattr(region, 'width', 0)
            row['Region Height'] = getattr(region, 'height', 0)
            row['Region Confidence'] = f"{getattr(region, 'confidence', 0):.3f}"
            row['Detection Method'] = getattr(region, 'detection_method', 'Unknown')

        # Add validation result
        if hasattr(region_validation, 'validation_result'):
            val_result = region_validation.validation_result
            row['Region Valid'] = 'Yes' if getattr(val_result, 'valid', False) else 'No'
            row['Validation Confidence'] = f"{getattr(val_result, 'confidence', 0):.3f}"
            row['Region Associations'] = '; '.join(getattr(val_result, 'associations', []))
            row['Region License Numbers'] = '; '.join(getattr(val_result, 'license_numbers', []))

        # Add OCR text
        if hasattr(region_validation, 'ocr_result'):
            ocr = region_validation.ocr_result
            text = getattr(ocr, 'text', '').strip()
            row['Region Text'] = text[:100] if text else "None"  # First 100 chars

        return row

    def export_summary_csv(self, batch_summary, output_path: str) -> str:
        """
        Export batch summary to CSV.

        Args:
            batch_summary: BatchSummary object
            output_path: Path where CSV file should be saved

        Returns:
            Path to created CSV file
        """
        try:
            summary_data = {
                'Metric': [
                    'Total Files',
                    'Total Pages',
                    'Valid Pages',
                    'Validation Rate',
                    'Average Processing Time (s)'
                ],
                'Value': [
                    batch_summary.total_files,
                    batch_summary.total_pages,
                    batch_summary.valid_pages,
                    f"{batch_summary.validation_rate:.1%}",
                    f"{batch_summary.average_processing_time:.2f}"
                ]
            }

            df = pd.DataFrame(summary_data)
            df.to_csv(output_path, index=False, encoding='utf-8')

            logger.info(f"Exported batch summary to CSV: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting summary to CSV: {str(e)}")
            raise
