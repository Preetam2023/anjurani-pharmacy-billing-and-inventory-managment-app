"""
Generates the printable invoice as a PDF: a single professional pharmacy
cash memo occupying the top-left quarter of an A4 page.

The pharmacy header (name, contact numbers, locations) is a pre-made
PNG image rather than rendered text — Bengali text needs proper complex
script shaping (matra reordering, conjuncts) that ReportLab's basic text
drawing doesn't do correctly, so a designed image avoids that entirely
and looks exactly like the pharmacy's existing paper receipt.
"""

import os
from logic.resource_path import resource_path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from datetime import datetime

from logic.config import REPORTS_DIR
ASSETS_DIR = resource_path("assets")
FONTS_DIR = resource_path("assets/fonts")

# Header image: see assets/images/README.md for exact size/placement spec.
HEADER_IMAGE_PATH = resource_path(
    "assets/images/anjurani.png"
)
BACKGROUND_IMAGE_PATH = resource_path(
    "assets/images/preprinted_invoice.jpeg"
)
WATERMARK_IMAGE_PATH = resource_path(
    "assets/images/medi.png"
)

FONT_REGULAR = "ReceiptFont"
FONT_BOLD = "ReceiptFont-Bold"
_fonts_ready = False

# Premium color palette
PRIMARY_BLUE = colors.HexColor("#1a3a6b")
DARK_BLUE = colors.HexColor("#0d2647")
LIGHT_BLUE = colors.HexColor("#e8eef6")
SOFT_GRAY = colors.HexColor("#f5f7fa")
BORDER_GRAY = colors.HexColor("#d1d9e6")
TEXT_DARK = colors.HexColor("#1a202c")
TEXT_MEDIUM = colors.HexColor("#4a5568")
TEXT_LIGHT = colors.HexColor("#8a9bb5")
WHITE = colors.HexColor("#ffffff")
RED = colors.HexColor("#e53e3e")
GREEN = colors.HexColor("#2f855a")
GOLD = colors.HexColor("#d69e2e")

# Header image box (top of each quarter-page receipt), in mm.
HEADER_BOX_HEIGHT = 26 * mm

def _ensure_fonts():
    global _fonts_ready
    if _fonts_ready:
        return
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, os.path.join(FONTS_DIR, "FreeSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, os.path.join(FONTS_DIR, "FreeSansBold.ttf")))
    _fonts_ready = True

def generate_invoice_preprinted(invoice_no, invoice_date, items, subtotal,
                          discount_percent, grand_total,
                          customer_name=None, customer_phone=None):
    _ensure_fonts()
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filepath = os.path.join(REPORTS_DIR, f"{invoice_no}.pdf")

    receipt_w = A4[0] / 2
    receipt_h = A4[1] / 2

    c = pdfcanvas.Canvas(
        filepath,
        pagesize=(receipt_w, receipt_h),
    )

    data = {
        "invoice_no": invoice_no,
        "invoice_date": invoice_date,
        "items": items,
        "subtotal": subtotal,
        "discount_percent": discount_percent,
        "grand_total": grand_total,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
    }

    _draw_receipt(
        c,
        0,
        0,
        receipt_w,
        receipt_h,
        data,
    )

    c.showPage()
    c.save()
    return filepath


# ---------- Drawing helpers ----------

def _fit_text(c, text, font, size, max_width):
    if c.stringWidth(text, font, size) <= max_width:
        return text
    ellipsis = "..."
    truncated = text
    while truncated and c.stringWidth(truncated + ellipsis, font, size) > max_width:
        truncated = truncated[:-1]
    return (truncated + ellipsis) if truncated else text[:1]


def _draw_background_image(c, left, top, width, height):
    if not os.path.exists(BACKGROUND_IMAGE_PATH):
        return
    try:
        c.drawImage(
            BACKGROUND_IMAGE_PATH,
            0,
            0,
            width=A4[0] / 2,
            height=A4[1] / 2,
            preserveAspectRatio=False,
            mask=None,
        )
    except Exception:
        pass

def _draw_watermark(c, x, y, width, height):
    """Draw medical background watermark behind the medicine list"""
    if os.path.exists(WATERMARK_IMAGE_PATH):
        try:
            img = ImageReader(WATERMARK_IMAGE_PATH)
            c.saveState()
            c.setFillAlpha(0.08)  # Very subtle background[cite: 2]
            c.drawImage(img, x, y, width=width, height=height, 
                       preserveAspectRatio=True, mask="auto")[cite: 2]
            c.restoreState()[cite: 2]
        except Exception:
            pass
        
def _draw_receipt(c, x0, y0, w, h, data):
    # Page
    # _draw_background_image(c, x0, y0, w, h)
    _draw_watermark(c, 40, 70, w - 80, h - 200)
    _ensure_fonts()

    # ---------------------------------------------------
    # PERFECTED COORDINATES
    # ---------------------------------------------------
    
    NAME_X = 58  
    NAME_Y = h - 94  # Lowered to drop back onto the dotted line

    DATE_X = 235  
    DATE_Y = h - 94  # Lowered to drop back onto the dotted line

    TABLE_START_Y = h - 140  
    ROW_HEIGHT = 16 

    QTY_X = 22 
    NAME_X_TABLE = 48 
    MRP_X = 205  # Pulled left so it centers inside the MRP column
    EXP_X = 215  # Shifted very slightly left
    TOTAL_X = 280 

    TOTAL_AMOUNT_X = 290 
    TOTAL_AMOUNT_Y = 34  # Raised up from 18 so it fits inside the bottom box

    # ---------------------------------------------------
    # Date
    # ---------------------------------------------------

    try:
            invoice_date = datetime.strptime(
        (data["invoice_date"] or "").split()[0],
        "%Y-%m-%d"
    ).strftime("%d/%m/%Y")
    except Exception:
        invoice_date = (data["invoice_date"] or "").split()[0]
    c.setFillColor(colors.black)
    c.setFont(FONT_REGULAR, 10)
    c.drawString(DATE_X, DATE_Y, invoice_date)

    # ---------------------------------------------------
    # Customer Name
    # ---------------------------------------------------
    if data.get("customer_name"):
        c.setFillColor(colors.black)
        c.setFont(FONT_REGULAR, 10)
        c.drawString(NAME_X, NAME_Y, data["customer_name"])

    # ---------------------------------------------------
    # Medicine Rows
    # ---------------------------------------------------
    y = TABLE_START_Y
    c.setFillColor(colors.black)

    for item in data["items"]:
        if y < 70:
            break

        # Qty
        c.setFont(FONT_BOLD, 10)
        c.drawCentredString(QTY_X, y, str(item["quantity"]))

        # Medicine Name
        c.setFont(FONT_REGULAR, 11)
        
        medicine = _fit_text(
            c,
            item["name"],
            FONT_REGULAR,
            10,
            125, 
        )
        c.drawString(NAME_X_TABLE, y, medicine)

        # MRP
        c.drawRightString(MRP_X, y, f"{item['unit_price']:.2f}")

        # Expiry
        c.setFont(FONT_REGULAR, 9) 
        expiry = item.get("expiry_date") or ""
        if expiry and expiry != "-":
            try:
                parts = expiry.split("-")
                expiry = f"{parts[1][:3]}/{parts[2][-2:]}"
            except Exception:
                pass
        c.drawString(EXP_X, y, expiry)

        # Amount
        c.setFont(FONT_BOLD, 10) 
        c.drawRightString(TOTAL_X, y, f"{item['total_price']:.2f}")

        y -= ROW_HEIGHT
        
    # ---------------------------------------------------
    # TOTAL
    # ---------------------------------------------------
    c.setFillColor(colors.black)
    c.setFont(FONT_BOLD, 13)
    c.drawRightString(TOTAL_AMOUNT_X, TOTAL_AMOUNT_Y, f"{data['grand_total']:.2f}")

    return