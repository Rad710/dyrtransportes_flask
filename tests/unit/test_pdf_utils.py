"""Page setup and the LibreOffice conversion of utils/pdf.py.

The conversion itself is exercised for real in tests/functional, here the
subprocess is replaced so the failure paths can be checked without LibreOffice.
"""

import subprocess

import pytest

from openpyxl import Workbook

from utils import pdf as pdf_utils
from utils.pdf import PdfConversionError
from utils.pdf import excel_to_pdf
from utils.pdf import set_print_page_setup


class FakeCompletedProcess:
    def __init__(self, returncode=0, stderr=b""):
        self.returncode = returncode
        self.stderr = stderr


def test_set_print_page_setup_prepares_the_sheet_for_printing():
    sheet = Workbook().active
    set_print_page_setup(sheet, repeat_rows="1:5")

    assert sheet.page_setup.orientation == "landscape"
    assert sheet.page_setup.fitToWidth == 1
    assert sheet.page_setup.fitToHeight == 0
    assert sheet.sheet_properties.pageSetUpPr.fitToPage is True
    assert sheet.print_title_rows == "$1:$5"


def test_set_print_page_setup_without_repeated_rows():
    sheet = Workbook().active
    set_print_page_setup(sheet)

    assert sheet.page_setup.orientation == "landscape"
    assert sheet.print_title_rows is None


def test_the_workbook_is_converted_and_the_pdf_returned(monkeypatch):
    def fake_run(command, **kwargs):  # pylint: disable=unused-argument
        outdir = command[command.index("--outdir") + 1]
        with open(f"{outdir}/export.pdf", "wb") as pdf_file:
            pdf_file.write(b"%PDF-1.7 fake")
        return FakeCompletedProcess()

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert excel_to_pdf(Workbook()) == b"%PDF-1.7 fake"


def test_the_command_never_runs_through_a_shell(monkeypatch):
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["kwargs"] = kwargs
        outdir = command[command.index("--outdir") + 1]
        with open(f"{outdir}/export.pdf", "wb") as pdf_file:
            pdf_file.write(b"%PDF-")
        return FakeCompletedProcess()

    monkeypatch.setattr(subprocess, "run", fake_run)
    excel_to_pdf(Workbook())

    assert isinstance(seen["command"], list)
    assert seen["kwargs"].get("shell") is not True
    assert "--convert-to" in seen["command"]


@pytest.mark.parametrize(
    "locale, expected", [("es", "es_PY.UTF-8"), ("en", "en_US.UTF-8")]
)
def test_the_locale_of_the_request_is_passed_to_libreoffice(
    monkeypatch, locale, expected
):
    seen = {}

    def fake_run(command, **kwargs):
        seen["env"] = kwargs["env"]
        outdir = command[command.index("--outdir") + 1]
        with open(f"{outdir}/export.pdf", "wb") as pdf_file:
            pdf_file.write(b"%PDF-")
        return FakeCompletedProcess()

    monkeypatch.setattr(subprocess, "run", fake_run)
    excel_to_pdf(Workbook(), locale)

    assert seen["env"]["LC_ALL"] == expected
    assert seen["env"]["LANG"] == expected


def test_an_unknown_locale_falls_back_to_english(monkeypatch):
    seen = {}

    def fake_run(command, **kwargs):
        seen["env"] = kwargs["env"]
        outdir = command[command.index("--outdir") + 1]
        with open(f"{outdir}/export.pdf", "wb") as pdf_file:
            pdf_file.write(b"%PDF-")
        return FakeCompletedProcess()

    monkeypatch.setattr(subprocess, "run", fake_run)
    excel_to_pdf(Workbook(), "fr")

    assert seen["env"]["LC_ALL"] == "en_US.UTF-8"


def test_a_failed_conversion_raises(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: FakeCompletedProcess(returncode=1, stderr=b"boom"),
    )

    with pytest.raises(PdfConversionError, match="boom"):
        excel_to_pdf(Workbook())


def test_a_missing_libreoffice_raises(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(PdfConversionError, match="not found"):
        excel_to_pdf(Workbook())


def test_a_hung_conversion_raises(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="soffice", timeout=1)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(PdfConversionError, match="timed out"):
        excel_to_pdf(Workbook())


def test_a_conversion_that_produces_no_file_raises(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeCompletedProcess())

    with pytest.raises(PdfConversionError):
        excel_to_pdf(Workbook())


def test_the_temporary_files_are_removed(monkeypatch):
    seen = {}

    def fake_run(command, **kwargs):  # pylint: disable=unused-argument
        outdir = command[command.index("--outdir") + 1]
        seen["outdir"] = outdir
        with open(f"{outdir}/export.pdf", "wb") as pdf_file:
            pdf_file.write(b"%PDF-")
        return FakeCompletedProcess()

    monkeypatch.setattr(subprocess, "run", fake_run)
    excel_to_pdf(Workbook())

    import os

    assert not os.path.exists(seen["outdir"])


def test_only_a_few_conversions_run_at_the_same_time(monkeypatch):
    """The semaphore is released even when the conversion fails."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: FakeCompletedProcess(returncode=1, stderr=b"boom"),
    )

    for _ in range(pdf_utils.MAX_CONCURRENT_CONVERSIONS + 2):
        with pytest.raises(PdfConversionError):
            excel_to_pdf(Workbook())

    # every slot is free again
    for _ in range(pdf_utils.MAX_CONCURRENT_CONVERSIONS):
        assert pdf_utils._conversion_slots.acquire(timeout=1)
    for _ in range(pdf_utils.MAX_CONCURRENT_CONVERSIONS):
        pdf_utils._conversion_slots.release()
