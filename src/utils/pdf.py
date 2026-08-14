"""Helpers shared by the PDF exports, rendered with reportlab."""

import io

from decimal import Decimal
from decimal import ROUND_HALF_UP

from typing import Any
from typing import List
from typing import Optional
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate

# Landscape A4 with narrow margins, the exports are wide tables
PAGE_SIZE = landscape(A4)
PAGE_MARGIN = 8 * mm
CONTENT_WIDTH = PAGE_SIZE[0] - (2 * PAGE_MARGIN)

# Excel column widths are expressed in characters, PDF widths in points
EXCEL_WIDTH_TO_POINTS = 5.5

GRID_COLOR = colors.black
# Same colors the Excel exports use for headers and subtotal rows
HEADER_BACKGROUND = colors.HexColor("#FFC000")
SUBTOTAL_BACKGROUND = colors.HexColor("#969696")

TITLE_STYLE = ParagraphStyle(
    name="pdf_title",
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=16,
    alignment=TA_CENTER,
)

SUBTITLE_STYLE = ParagraphStyle(
    name="pdf_subtitle",
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=12,
    alignment=TA_CENTER,
)

ACCENT_TITLE_STYLE = ParagraphStyle(
    name="pdf_accent_title",
    parent=TITLE_STYLE,
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#800080"),
)

CELL_STYLE = ParagraphStyle(
    name="pdf_cell",
    fontName="Helvetica",
    fontSize=6,
    leading=7,
)


def round_amount(value: Decimal) -> Decimal:
    """Round a monetary value to the unit, matching Excel's ROUND(value, 0)."""
    return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def format_number(
    value: Optional[Decimal | int | float], locale: str = "es", decimals: int = 0
) -> str:
    """Format a number the same way the Excel exports do ('#,##0' / '#,##0.00').

    Spanish uses '.' as thousands separator and ',' as decimal separator,
    English keeps the default ',' and '.'.
    """
    if value is None:
        return ""

    formatted = f"{Decimal(value):,.{decimals}f}"

    if locale == "es":
        # Swap separators using a placeholder to avoid clobbering the result
        formatted = (
            formatted.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
        )

    return formatted


def scale_widths(excel_widths: Sequence[float]) -> List[float]:
    """Convert Excel character widths into point widths that fill the page."""
    points = [width * EXCEL_WIDTH_TO_POINTS for width in excel_widths]
    total = sum(points)

    if total <= 0:
        return points

    factor = CONTENT_WIDTH / total
    return [width * factor for width in points]


CELL_STYLES = {
    "left": ParagraphStyle(name="pdf_cell_left", parent=CELL_STYLE, alignment=TA_LEFT),
    "center": ParagraphStyle(
        name="pdf_cell_center", parent=CELL_STYLE, alignment=TA_CENTER
    ),
    "right": ParagraphStyle(
        name="pdf_cell_right", parent=CELL_STYLE, alignment=TA_RIGHT
    ),
}

BOLD_CELL_STYLES = {
    align: ParagraphStyle(
        name=f"pdf_cell_{align}_bold", parent=style, fontName="Helvetica-Bold"
    )
    for align, style in CELL_STYLES.items()
}


def cell(text: Any, bold: bool = False, align: str = "left") -> Paragraph:
    """Wrap a cell value in a Paragraph so long values wrap instead of overflowing."""
    style = BOLD_CELL_STYLES[align] if bold else CELL_STYLES[align]

    return Paragraph("" if text is None else str(text), style)


def build_pdf(flowables: List[Flowable], title: str) -> bytes:
    """Render the given flowables into a landscape PDF document."""
    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=PAGE_SIZE,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
        title=title,
    )
    document.build(flowables)

    output.seek(0)
    return output.getvalue()
