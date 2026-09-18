from .base_report import ReportData, ReportMetadata, ReportTableColumn
from .pdf_builder import build_pdf_report
from .xlsx_builder import build_xlsx_report
from .docx_builder import build_docx_report
from .generators import (
    generate_classroom_report_data,
    generate_year_performance_report_data,
    generate_questions_diagnostic_report_data,
    generate_comparison_report_data,
    generate_schools_overview_report_data,
)

__all__ = [
    "ReportData",
    "ReportMetadata",
    "ReportTableColumn",
    "build_pdf_report",
    "build_xlsx_report",
    "build_docx_report",
    "generate_classroom_report_data",
    "generate_year_performance_report_data",
    "generate_questions_diagnostic_report_data",
    "generate_comparison_report_data",
    "generate_schools_overview_report_data",
]
