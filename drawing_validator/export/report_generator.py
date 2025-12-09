"""
Generate professional PDF validation reports.
"""

import os
import logging
from typing import List, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image as RLImage
)
from reportlab.platypus.flowables import Flowable

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate professional PDF validation reports."""

    def __init__(self, template_dir: str = "export_templates"):
        """
        Initialize report generator.

        Args:
            template_dir: Directory containing report templates
        """
        self.template_dir = template_dir
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for report."""
        # Cover title style
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        ))

        # Cover subtitle style
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.HexColor('#34495e')
        ))

        # File header style
        self.styles.add(ParagraphStyle(
            name='FileHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        ))

    def generate_validation_report(
        self,
        batch_result,
        output_path: str
    ) -> str:
        """
        Generate comprehensive PDF report.

        Args:
            batch_result: BatchResult with processing results
            output_path: Path where PDF should be saved

        Returns:
            Path to generated PDF
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=36
            )

            # Build story (content)
            story = []

            # 1. Cover page
            story.extend(self._create_cover_page(batch_result))

            # 2. Executive summary
            story.extend(self._create_executive_summary(batch_result))

            # 3. Detailed results per file
            for i, file_result in enumerate(batch_result.results):
                story.extend(self._create_file_section(file_result, i + 1))

                # Add page break between files
                if i < len(batch_result.results) - 1:
                    story.append(PageBreak())

            # Build PDF
            doc.build(story)

            logger.info(f"Generated report: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise

    def _create_cover_page(self, batch_result) -> List[Flowable]:
        """Create professional cover page."""
        elements = []

        # Title
        elements.append(Spacer(1, 100))
        elements.append(Paragraph(
            "Engineering Drawing Validation Report",
            self.styles['CoverTitle']
        ))

        # Subtitle
        elements.append(Paragraph(
            f"Validation conducted on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['CoverSubtitle']
        ))

        elements.append(Spacer(1, 50))

        # Summary table
        summary_data = [
            ["Total Files Processed:", str(batch_result.total_files)],
            ["Successfully Validated:", str(batch_result.successful_files)],
            ["Failed Validations:", str(batch_result.failed_files)],
            ["Processing Time:", f"{batch_result.processing_time:.1f} seconds"],
            ["Overall Success Rate:",
             f"{(batch_result.successful_files/batch_result.total_files*100):.1f}%"
             if batch_result.total_files > 0 else "N/A"],
        ]

        summary_table = Table(summary_data, colWidths=[250, 150])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(summary_table)
        elements.append(PageBreak())

        return elements

    def _create_executive_summary(self, batch_result) -> List[Flowable]:
        """Create executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 12))

        # Summary text
        summary_text = f"""
        This report documents the validation of {batch_result.total_files} engineering
        drawing(s) for P.Eng signatures from Canadian engineering associations
        (APEGA, APEGS, EGBC, Engineers Geoscientists Manitoba).
        """

        elements.append(Paragraph(summary_text, self.styles['Normal']))
        elements.append(Spacer(1, 12))

        # Results overview
        results_text = f"""
        <b>Validation Results:</b><br/>
        - {batch_result.successful_files} file(s) successfully validated<br/>
        - {batch_result.failed_files} file(s) failed validation<br/>
        - Total processing time: {batch_result.processing_time:.2f} seconds
        """

        elements.append(Paragraph(results_text, self.styles['Normal']))
        elements.append(Spacer(1, 20))

        elements.append(PageBreak())

        return elements

    def _create_file_section(self, file_result, file_num: int) -> List[Flowable]:
        """Create detailed section for a single file."""
        elements = []

        # File header
        filepath = getattr(file_result, 'filepath', 'Unknown')
        elements.append(Paragraph(
            f"{file_num}. File: {os.path.basename(filepath)}",
            self.styles['FileHeader']
        ))

        elements.append(Spacer(1, 10))

        # File metadata table
        meta_data = [
            ["Path:", filepath],
            ["Validation Status:", "✓ Valid" if getattr(file_result, 'overall_valid', False) else "✗ Invalid"],
            ["Processing Time:", f"{getattr(file_result, 'total_processing_time', 0):.2f}s"],
        ]

        # Add page count if available
        if hasattr(file_result, 'page_results'):
            meta_data.append(["Pages:", str(len(file_result.page_results))])

        # Add associations if available
        if hasattr(file_result, 'get_all_associations'):
            associations = file_result.get_all_associations()
            meta_data.append(["Associations:", ", ".join(associations) if associations else "None"])

        # Add license numbers if available
        if hasattr(file_result, 'get_all_license_numbers'):
            licenses = file_result.get_all_license_numbers()
            meta_data.append(["License Numbers:", ", ".join(licenses) if licenses else "None"])

        meta_table = Table(meta_data, colWidths=[120, 350])
        meta_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(meta_table)
        elements.append(Spacer(1, 15))

        # Page-by-page results
        if hasattr(file_result, 'page_results') and file_result.page_results:
            elements.append(Paragraph("Page Results:", self.styles['Heading4']))
            elements.append(Spacer(1, 8))

            # Create page summary table
            page_data = [["Page", "Valid", "Regions", "Associations"]]

            for page_num, page in enumerate(file_result.page_results):
                valid_status = "✓" if getattr(page, 'has_valid_signature', False) else "✗"
                total_regions = len(getattr(page, 'region_validations', []))

                # Get associations for this page
                page_associations = set()
                if hasattr(page, 'region_validations'):
                    for rv in page.region_validations:
                        if hasattr(rv, 'validation_result'):
                            page_associations.update(
                                getattr(rv.validation_result, 'associations', [])
                            )

                page_data.append([
                    str(page_num + 1),
                    valid_status,
                    str(total_regions),
                    ", ".join(page_associations) if page_associations else "-"
                ])

            page_table = Table(page_data, colWidths=[60, 60, 80, 250])
            page_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            elements.append(page_table)
            elements.append(Spacer(1, 15))

        return elements

    def generate_simple_report(
        self,
        validation_result,
        output_path: str
    ) -> str:
        """
        Generate a simple report for a single file.

        Args:
            validation_result: DrawingValidationResult object
            output_path: Path where PDF should be saved

        Returns:
            Path to generated PDF
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=36
            )

            story = []

            # Title
            story.append(Paragraph(
                "Engineering Drawing Validation Report",
                self.styles['CoverTitle']
            ))

            story.append(Spacer(1, 30))

            # File info
            filepath = getattr(validation_result, 'filepath', 'Unknown')
            file_data = [
                ["File:", os.path.basename(filepath)],
                ["Path:", filepath],
                ["Validated:", datetime.now().strftime('%Y-%m-%d %H:%M')],
                ["Status:", "✓ Valid" if getattr(validation_result, 'overall_valid', False) else "✗ Invalid"],
            ]

            file_table = Table(file_data, colWidths=[100, 350])
            file_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            story.append(file_table)
            story.append(Spacer(1, 20))

            # Page results
            if hasattr(validation_result, 'page_results'):
                for page in validation_result.page_results:
                    story.extend(self._create_page_details(page))

            doc.build(story)

            logger.info(f"Generated simple report: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating simple report: {str(e)}")
            raise

    def _create_page_details(self, page) -> List[Flowable]:
        """Create details for a single page."""
        elements = []

        page_num = getattr(page, 'page_number', 0)
        elements.append(Paragraph(f"Page {page_num + 1}", self.styles['Heading3']))

        # Page summary
        valid = "Valid" if getattr(page, 'has_valid_signature', False) else "Invalid"
        regions = len(getattr(page, 'region_validations', []))

        summary = f"Status: {valid} | Regions detected: {regions}"
        elements.append(Paragraph(summary, self.styles['Normal']))
        elements.append(Spacer(1, 10))

        return elements
