"""Helpers shared by the Excel exports."""

from typing import Iterable

from openpyxl.worksheet.worksheet import Worksheet


def force_text_cells(sheet: Worksheet, columns: Iterable[int]) -> None:
    """Write the given columns of the last row as text, never as a formula.

    openpyxl turns any string starting with '=' into a live formula, so a value
    typed by a user ('=WEBSERVICE(...)' in a name, a reason, a plate) would be
    stored as a formula and executed by Excel or by the PDF conversion. The
    columns holding user typed values go through here to stay plain text.
    """
    for column in columns:
        cell = sheet.cell(row=sheet.max_row, column=column)
        if cell.data_type == "f":
            cell.data_type = "s"
