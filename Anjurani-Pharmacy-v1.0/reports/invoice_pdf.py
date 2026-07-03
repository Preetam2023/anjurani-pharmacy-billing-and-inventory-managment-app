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

from logic.config import REPORTS_DIR

ASSETS_DIR = resource_path("assets")
FONTS_DIR = resource_path("assets/fonts")

# Header image: see assets/images/README.md for exact size/placement spec.
HEADER_IMAGE_PATH = resource_path(
    "assets/images/anjurani.png"
)
BACKGROUND_IMAGE_PATH = resource_path(
    "assets/images/medi.png"
)
# Only needed as a fallback (if the header image is missing) and for any
# Bengali customer names a cashier might type in — not used for the main
# header anymore now that it's an image. GNU FreeFont, GPL-3+ with a
# font-embedding exception that permits bundling it with an application.
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


def generate_invoice_pdf(invoice_no, invoice_date, items, subtotal,
                          discount_percent, grand_total,
                          customer_name=None, customer_phone=None):
    """
    items: list of dicts with 'name', 'batch_no', 'quantity', 'unit_price',
           'total_price', and 'expiry_date' (a display string like
           '01-Aug-2026', or '-'/None if unknown).
    Returns the full filesystem path of the generated PDF.
    """
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

    # Draw quarter-page guide lines (middle of A4 page)
    # _draw_guide_lines(c, page_w, page_h)
    
    # Draw single receipt in top-left quadrant
    # _draw_receipt(c, 0, page_h - receipt_h, receipt_w, receipt_h, data)
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
    """Truncates text with '...' if it doesn't fit max_width, so table
    columns never overlap regardless of how long a medicine name is."""
    if c.stringWidth(text, font, size) <= max_width:
        return text
    ellipsis = "..."
    truncated = text
    while truncated and c.stringWidth(truncated + ellipsis, font, size) > max_width:
        truncated = truncated[:-1]
    return (truncated + ellipsis) if truncated else text[:1]


def _draw_guide_lines(c, page_w, page_h):
    """Draw guide lines at the middle of the page to show quarter positions"""
    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.setLineWidth(0.3)
    c.setDash(3, 3)  # Dashed line for visibility
    
    # Vertical center line
    c.line(page_w/2, 0, page_w/2, page_h)
    
    # Horizontal center line
    c.line(0, page_h/2, page_w, page_h/2)
    
    c.setDash()  # Reset dash


def _draw_header_image(c, left, right, top):
    """
    Draws the pharmacy header image, scaled to fit the header box
    (preserving aspect ratio, anchored top-center). Falls back to plain
    text if the image hasn't been added yet, so the app still works
    (just without the branded look) before the asset is supplied.
    """
    box_w = right - left
    box_h = HEADER_BOX_HEIGHT

    if os.path.exists(HEADER_IMAGE_PATH):
        img = ImageReader(HEADER_IMAGE_PATH)
        img_w, img_h = img.getSize()
        # Add small margin (2%) on sides
        margin_scale = 0.96
        scale = min((box_w * margin_scale) / img_w, box_h / img_h)
        draw_w, draw_h = img_w * scale, img_h * scale
        draw_x = left + (box_w - draw_w) / 2
        draw_y = top - draw_h
        c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h, mask="auto")
        return

    # Fallback: header image not added yet.
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(PRIMARY_BLUE)
    c.drawCentredString(left + box_w / 2, top - box_h / 2,
                         "[ add assets/images/receipt_header.png ]")


def _draw_background_image(c, left, top, width, height):
    """Draw medical background image behind the medicine list"""
    if os.path.exists(BACKGROUND_IMAGE_PATH):
        try:
            img = ImageReader(BACKGROUND_IMAGE_PATH)
            # Draw with low opacity by using mask
            c.saveState()
            c.setFillAlpha(0.08)  # Very subtle background
            c.drawImage(img, left, top - height, width=width, height=height, 
                       preserveAspectRatio=True, mask="auto")
            c.restoreState()
        except:
            pass  # Silently fail if image can't be loaded


def _draw_clean_table_border(c, left, top, width, height):
    """Draws clean table borders with proper corners"""
    # Main border
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.5)
    c.rect(left, top, width, height, fill=0, stroke=1)


def _draw_receipt(c, x0, y0, w, h, data):
    """Draws one complete receipt within the box [x0, y0, x0+w, y0+h]."""
    margin = 4 * mm
    left = x0 + margin
    right = x0 + w - margin
    top = y0 + h - margin
    content_w = right - left
    center_x = x0 + w / 2

    cursor_y = top

    # ---- Header image (pharmacy name, contact, locations) ----
    # _draw_header_image(c, left, right, cursor_y)
    cursor_y -= HEADER_BOX_HEIGHT + 3 * mm

    # ---- Clean separator line below header ----
    c.setStrokeColor(PRIMARY_BLUE)
    c.setLineWidth(0.6)
    c.line(left, cursor_y + 0.5 * mm, right, cursor_y + 0.5 * mm)
    cursor_y -= 3 * mm

    # ---- Invoice Info: Invoice No (left) | Date (right) ----
    c.setFont(FONT_BOLD, 7.5)
    c.setFillColor(PRIMARY_BLUE)
    c.drawString(left, cursor_y, f"INVOICE: {data['invoice_no']}")
    
    # Date (right aligned)
    date_only = (data["invoice_date"] or "").split(" ")[0]
    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(TEXT_MEDIUM)
    c.drawRightString(right, cursor_y, date_only)
    
    cursor_y -= 5 * mm

    # ---- Customer Info (if provided) ----
    if data.get("customer_name") or data.get("customer_phone"):
        c.setFont(FONT_REGULAR, 6.5)
        c.setFillColor(TEXT_MEDIUM)
        customer_text = ""
        if data.get("customer_name"):
            customer_text += f"Patient: {data['customer_name']}"
        if data.get("customer_phone"):
            if customer_text:
                customer_text += "  |  "
            customer_text += f"Ph: {data['customer_phone']}"
        c.drawString(left, cursor_y, customer_text)
        cursor_y -= 4.5 * mm

    # ---- Table ----
    # Column fractions: Sl No(6%), Medicine(42%), Qty(8%), Batch(14%), Rate(12%), Total(18%)
    fractions = [
    0.06,   # Sl No
    0.43,   # Medicine
    0.08,   # Qty
    0.14,   # Batch
    0.14,   # Rate
    0.15,   # Total
]
    col_x = [left]
    acc = left
    for f in fractions:
        acc += f * content_w
        col_x.append(acc)

    # Table header with clean professional look
    header_h = 6.5 * mm
    header_y = cursor_y
    
    # Draw header background
    c.setFillColor(PRIMARY_BLUE)
    c.rect(left, header_y - header_h, content_w, header_h, fill=1, stroke=0)
    
    # Header text
    c.setFont(FONT_BOLD, 7)
    c.setFillColor(WHITE)
    
    headers = ["#", "ITEM", "QTY", "BATCH", "RATE", "TOTAL"]
    alignments = ['center', 'left', 'center', 'center', 'right', 'right']
    
    for i, (header, align) in enumerate(zip(headers, alignments)):
        if align == 'left':
            c.drawString(col_x[i] + 1.5 * mm, header_y - header_h + 2 * mm, header)
        elif align == 'right':
            c.drawRightString(col_x[i+1] - 1.5 * mm, header_y - header_h + 2 * mm, header)
        else:  # center
            x_pos = col_x[i] + (col_x[i+1] - col_x[i]) / 2
            c.drawCentredString(x_pos, header_y - header_h + 2 * mm, header)
    
    cursor_y -= header_h + 2.5 * mm

    # ---- Table body ----
    # ==========================
    # Bottom Layout
    # ==========================

    footer_height = 8 * mm
    summary_height = 20 * mm

    bottom_margin = margin

    footer_top = y0 + bottom_margin + footer_height
    summary_top = footer_top + summary_height

    # Table ends exactly here
    table_bottom = summary_top

    items = data["items"]
    n_items = max(len(items), 1)
    available_h = max(cursor_y - table_bottom, 4 * mm)
    row_h = min(available_h / n_items, 6.5 * mm)
    row_h = max(4.5 * mm, row_h)
    font_size = 7 if row_h >= 5.5 * mm else 6.5

    # Draw background image behind table
    _draw_background_image(c, left, cursor_y, content_w, cursor_y - table_bottom)
    
    # Draw clean table border
    _draw_clean_table_border(c, left, table_bottom, content_w, cursor_y - table_bottom)
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.3)
    for x in col_x[1:-1]:
        c.line(
            x,
            table_bottom,
            x,
            cursor_y,
        )
    
    # Draw alternating row backgrounds for readability
    for idx in range(len(items)):
        row_top = cursor_y - idx * row_h
        row_bottom = row_top - row_h
        if row_bottom < table_bottom:
            break
        # if idx % 2 == 0:
        #     c.setFillColor(LIGHT_BLUE)
        #     c.rect(left + 0.5 * mm, row_bottom + 0.5 * mm, 
        #            content_w - 1 * mm, row_h - 1 * mm, fill=1, stroke=0)
    
    # Draw table rows
    for idx, item in enumerate(items):
        row_text_y = cursor_y - row_h + 1.6*mm
        if row_text_y < table_bottom:
            break

        # Draw horizontal separator line (subtle)
        if idx > 0:
            c.setStrokeColor(BORDER_GRAY)
            c.setLineWidth(0.3)
            c.line(left + 1 * mm, row_text_y - 0.2 * mm, 
                   right - 1 * mm, row_text_y - 0.2 * mm)

        # Sl No (centered)
        sl_x = col_x[0] + (col_x[1] - col_x[0]) / 2
        c.setFont(FONT_REGULAR, font_size)
        c.setFillColor(TEXT_DARK)
        c.drawCentredString(sl_x, row_text_y, str(idx + 1))
        
        # Medicine (left aligned, truncated)
        c.setFont(FONT_REGULAR, font_size)
        c.setFillColor(TEXT_DARK)
        med_width = (col_x[2] - col_x[1]) - 2 * mm
        med_name = _fit_text(c, item["name"], FONT_REGULAR, font_size, med_width)
        c.drawString(col_x[1] + 1.5 * mm, row_text_y, med_name)
        
        # Qty (centered)
        qty_x = col_x[2] + (col_x[3] - col_x[2]) / 2
        c.setFont(FONT_BOLD, font_size)
        c.setFillColor(PRIMARY_BLUE)
        c.drawCentredString(qty_x, row_text_y, str(item["quantity"]))
        
        # Batch (centered)
        c.setFont(FONT_REGULAR, font_size - 0.5)
        c.setFillColor(TEXT_MEDIUM)
        batch_width = (col_x[4] - col_x[3]) - 2*mm

        batch_text = _fit_text(
            c,
            item.get("batch_no", "-") or "-",
            FONT_REGULAR,
            font_size - 0.5,
            batch_width,
        )

        batch_x = col_x[3] + (col_x[4] - col_x[3]) / 2

        c.drawCentredString(
            batch_x,
            row_text_y,
            batch_text,
        )
        
        # Rate (right aligned)
        c.setFont(FONT_REGULAR, font_size)
        c.setFillColor(TEXT_MEDIUM)
        c.drawRightString(col_x[5] - 1.5 * mm, row_text_y, f"₹{item['unit_price']:.2f}")
        
        # Total Amount (right aligned)
        c.setFont(FONT_BOLD, font_size)
        c.setFillColor(PRIMARY_BLUE)
        c.drawRightString(col_x[6] - 1.5 * mm, row_text_y, f"₹{item['total_price']:.2f}")

        cursor_y -= row_h

    # -----------------------
    # Footer
    # -----------------------

    footer_y = y0 + margin + 3*mm

    # c.setStrokeColor(PRIMARY_BLUE)
    # c.setLineWidth(0.6)
    # c.line(left, footer_y + 5*mm, right, footer_y + 5*mm)

    c.setFont(FONT_REGULAR,7)
    c.setFillColor(PRIMARY_BLUE)

    c.drawString(
        left,
        footer_y,
        "❯❯   Thank you for your visit"
    )

    summary_y = footer_top + 10*mm

    label_x = right - 52*mm
    value_x = right - 2*mm

    # dotted decoration
    c.setStrokeColor(PRIMARY_BLUE)
    c.setDash(2,2)
    c.line(label_x, summary_y+6*mm, value_x, summary_y+6*mm)
    c.setDash()

    # subtotal
    c.setFont(FONT_BOLD,8)
    c.setFillColor(TEXT_DARK)
    c.drawString(label_x, summary_y, "Subtotal")

    c.drawRightString(
        value_x,
        summary_y,
        f"₹ {data['subtotal']:.2f}"
    )

    summary_y -= 5*mm

    # discount
    if data["discount_percent"] > 0:

        discount = data["subtotal"]-data["grand_total"]

        c.setFont(FONT_BOLD,8)
        c.setFillColor(TEXT_DARK)
        c.drawString(
            label_x,
            summary_y,
            f"Discount ({data['discount_percent']:.1f}%)"
        )

        c.setFillColor(RED)

        c.drawRightString(
            value_x,
            summary_y,
            f"- ₹ {discount:.2f}"
        )

        summary_y -= 6*mm

    # blue line

    c.setStrokeColor(PRIMARY_BLUE)
    c.setLineWidth(0.8)
    c.line(label_x, summary_y+2*mm, value_x, summary_y+2*mm)

    summary_y -= 4*mm

    # GRAND TOTAL

    c.setFont(FONT_BOLD,11)
    c.setFillColor(PRIMARY_BLUE)

    c.drawString(
        label_x,
        summary_y,
        "GRAND TOTAL"
    )

    c.drawRightString(
        value_x,
        summary_y,
        f"₹ {data['grand_total']:.2f}"
    )