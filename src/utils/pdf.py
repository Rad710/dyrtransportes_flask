"""Convert the Excel exports to PDF, the same way 'print as PDF' does in Excel."""

import os
import shutil
import subprocess
import tempfile

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

# LibreOffice binary used for the conversion, overridable per environment
SOFFICE_PATH = os.getenv("SOFFICE_PATH", "soffice")

# A conversion of a big payroll takes a few seconds, kill it if it hangs
CONVERSION_TIMEOUT_SECONDS = 120

# LibreOffice formats the numbers of the printout with the locale it runs in
CONVERSION_LOCALES = {"es": "es_PY.UTF-8", "en": "en_US.UTF-8"}


class PdfConversionError(Exception):
    """Raised when the Excel file could not be converted to PDF."""


def set_print_page_setup(sheet: Worksheet, repeat_rows: str = "") -> None:
    """Set the page setup so the printout fits the page, as done before printing.

    The exports are wide tables, so they are printed in landscape scaled down to
    the page width. 'repeat_rows' repeats the header rows on every page, for
    example '1:5'.
    """
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True

    sheet.page_margins.left = 0.25
    sheet.page_margins.right = 0.25
    sheet.page_margins.top = 0.35
    sheet.page_margins.bottom = 0.35

    if repeat_rows:
        sheet.print_title_rows = repeat_rows


def excel_to_pdf(workbook: Workbook, locale: str = "es") -> bytes:
    """Convert an openpyxl workbook to PDF with LibreOffice.

    The workbook is printed as is, so the PDF keeps the Excel layout,
    LibreOffice calculates the formulas the export leaves in the cells and
    formats the numbers with the client's locale.
    """
    with tempfile.TemporaryDirectory() as work_dir:
        excel_path = os.path.join(work_dir, "export.xlsx")
        pdf_path = os.path.join(work_dir, "export.pdf")

        workbook.save(excel_path)

        # Each conversion gets its own profile so concurrent requests do not
        # fight over a shared LibreOffice user directory
        profile_dir = os.path.join(work_dir, "profile")

        command = [
            SOFFICE_PATH,
            "--headless",
            "--norestore",
            "--nolockcheck",
            f"-env:UserInstallation=file://{profile_dir}",
            "--convert-to",
            "pdf:calc_pdf_Export",
            "--outdir",
            work_dir,
            excel_path,
        ]

        conversion_locale = CONVERSION_LOCALES.get(locale, CONVERSION_LOCALES["en"])
        environment = {
            **os.environ,
            "LANG": conversion_locale,
            "LC_ALL": conversion_locale,
            "HOME": work_dir,
        }

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=False,
                env=environment,
                timeout=CONVERSION_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as e:
            raise PdfConversionError(f"{SOFFICE_PATH} not found") from e
        except subprocess.TimeoutExpired as e:
            raise PdfConversionError("PDF conversion timed out") from e

        if result.returncode != 0 or not os.path.exists(pdf_path):
            raise PdfConversionError(
                f"PDF conversion failed: {result.stderr.decode(errors='replace')}"
            )

        with open(pdf_path, "rb") as pdf_file:
            return pdf_file.read()


def is_pdf_conversion_available() -> bool:
    """Check whether LibreOffice is installed and can be used for conversions."""
    return shutil.which(SOFFICE_PATH) is not None
