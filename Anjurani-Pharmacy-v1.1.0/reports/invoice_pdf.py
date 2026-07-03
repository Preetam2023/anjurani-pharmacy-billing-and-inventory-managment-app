"""
Generates the printable invoice as a PDF: a single professional pharmacy
cash memo occupying the top-left quarter of an A4 page.
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

HEADER_IMAGE_PATH = resource_path(
    "assets/images/anjurani.png"
)
BACKGROUND_IMAGE_PATH = resource_path(
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

def _draw_header_image(c, x_start, x_end, top_y):
    box_w = x_end - x_start
    if os.path.exists(HEADER_IMAGE_PATH):
        img = ImageReader(HEADER_IMAGE_PATH)
        img_w, img_h = img.getSize()
        scale = box_w / img_w
        draw_w, draw_h = box_w, img_h * scale
        c.drawImage(img, x_start, top_y - draw_h, width=draw_w, height=draw_h, mask="auto")
        return draw_h
    
    # Fallback
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(PRIMARY_BLUE)
    c.drawCentredString(x_start + box_w / 2, top_y - HEADER_BOX_HEIGHT / 2,
                         "[ add assets/images/receipt_header.png ]")
    return HEADER_BOX_HEIGHT

def _draw_background_image(c, left, top, width, height):
    if os.path.exists(BACKGROUND_IMAGE_PATH):
        try:
            img = ImageReader(BACKGROUND_IMAGE_PATH)
            c.saveState()
            c.setFillAlpha(0.08) 
            c.drawImage(img, left, top - height, width=width, height=height, 
                       preserveAspectRatio=True, mask="auto")
            c.restoreState()
        except:
            pass 

def _draw_clean_table_border(c, left, top, width, height):
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.5)
    c.rect(left, top, width, height, fill=0, stroke=1)

def _draw_receipt(c, x0, y0, w, h, data):
    margin = 4 * mm
    left = x0 + margin
    right = x0 + w - margin
    content_w = right - left

    # Start from the absolute top to eliminate outside margin for the header
    cursor_y = y0 + h

    # ---- Header image (pharmacy name, contact, locations) ----
    header_h_actual = _draw_header_image(c, x0, x0 + w, cursor_y)
    cursor_y -= header_h_actual + 2 * mm

    # ---- Clean separator line below header ----
    c.setStrokeColor(PRIMARY_BLUE)
    c.setLineWidth(0.6)
    c.line(left, cursor_y, right, cursor_y)
    cursor_y -= 3 * mm

    # ---- Invoice Info: Invoice No (left) | Date (right) ----
    c.setFont(FONT_BOLD, 9)
    c.setFillColor(PRIMARY_BLUE)
    c.drawString(left, cursor_y, f"INVOICE: {data['invoice_no']}")
    
    date_only = (data["invoice_date"] or "").split(" ")[0]
    c.setFont(FONT_REGULAR, 9)
    c.setFillColor(TEXT_MEDIUM)
    c.drawRightString(right, cursor_y, date_only)
    
    cursor_y -= 5 * mm

    # ---- Customer Info (if provided) ----
    if data.get("customer_name") or data.get("customer_phone"):
        c.setFont(FONT_REGULAR, 8)
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
    fractions = [0.06, 0.43, 0.08, 0.14, 0.14, 0.15]
    col_x = [left]
    acc = left
    for f in fractions:
        acc += f * content_w
        col_x.append(acc)

    header_h = 7.5 * mm
    table_top = cursor_y
    
    # Clean Header text without fill
    c.setFont(FONT_BOLD, 9)
    c.setFillColor(TEXT_DARK)
    
    headers = ["#", "ITEM", "QTY", "BATCH", "RATE", "TOTAL"]
    alignments = ['center', 'left', 'center', 'center', 'right', 'right']
    
    for i, (header, align) in enumerate(zip(headers, alignments)):
        if align == 'left':
            c.drawString(col_x[i] + 1.5 * mm, table_top - header_h + 2.5 * mm, header)
        elif align == 'right':
            c.drawRightString(col_x[i+1] - 1.5 * mm, table_top - header_h + 2.5 * mm, header)
        else: 
            x_pos = col_x[i] + (col_x[i+1] - col_x[i]) / 2
            c.drawCentredString(x_pos, table_top - header_h + 2.5 * mm, header)
    
    cursor_y -= header_h

    # Draw separator line below table header
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.5)
    c.line(left, cursor_y, right, cursor_y)

    # ==========================
    # Bottom Layout
    # ==========================
    footer_height = 8 * mm
    summary_height = 20 * mm
    bottom_margin = margin

    footer_top = y0 + bottom_margin + footer_height
    summary_top = footer_top + summary_height
    table_bottom = summary_top

    items = data["items"]
    n_items = max(len(items), 1)
    available_h = max(cursor_y - table_bottom, 4 * mm)
    row_h = min(available_h / n_items, 7.5 * mm)
    row_h = max(5.5 * mm, row_h)
    
    font_size = 9 # Increased base font size for the table

    # Draw background image behind table
    _draw_background_image(c, left, cursor_y, content_w, cursor_y - table_bottom)
    
    # Draw clean table border outlining the entire table (including header)
    _draw_clean_table_border(c, left, table_bottom, content_w, table_top - table_bottom)
    
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.3)
    for x in col_x[1:-1]:
        c.line(x, table_bottom, x, table_top)
    
    # Draw table rows
    for idx, item in enumerate(items):
        row_text_y = cursor_y - row_h + 2.0 * mm
        if row_text_y < table_bottom:
            break

        if idx > 0:
            c.setStrokeColor(BORDER_GRAY)
            c.setLineWidth(0.3)
            c.line(left + 1 * mm, row_text_y - 0.2 * mm, 
                   right - 1 * mm, row_text_y - 0.2 * mm)

        # Sl No 
        sl_x = col_x[0] + (col_x[1] - col_x[0]) / 2
        c.setFont(FONT_REGULAR, font_size)
        c.setFillColor(TEXT_DARK)
        c.drawCentredString(sl_x, row_text_y, str(idx + 1))
        
        # Medicine 
        c.setFont(FONT_REGULAR, font_size)
        c.setFillColor(TEXT_DARK)
        med_width = (col_x[2] - col_x[1]) - 2 * mm
        med_name = _fit_text(c, item["name"], FONT_REGULAR, font_size, med_width)
        c.drawString(col_x[1] + 1.5 * mm, row_text_y, med_name)
        
        # Qty 
        qty_x = col_x[2] + (col_x[3] - col_x[2]) / 2
        c.setFont(FONT_BOLD, font_size)
        c.setFillColor(PRIMARY_BLUE)
        c.drawCentredString(qty_x, row_text_y, str(item["quantity"]))
        
        # Batch 
        c.setFont(FONT_REGULAR, font_size - 0.5)
        c.setFillColor(TEXT_MEDIUM)
        batch_width = (col_x[4] - col_x[3]) - 2*mm
        batch_text = _fit_text(
            c, item.get("batch_no", "-") or "-", FONT_REGULAR,
            font_size - 0.5, batch_width,
        )
        batch_x = col_x[3] + (col_x[4] - col_x[3]) / 2
        c.drawCentredString(batch_x, row_text_y, batch_text)
        
        # Rate 
        c.setFont(FONT_REGULAR, font_size)
        c.setFillColor(TEXT_MEDIUM)
        c.drawRightString(col_x[5] - 1.5 * mm, row_text_y, f"₹{item['unit_price']:.2f}")
        
        # Total Amount 
        c.setFont(FONT_BOLD, font_size)
        c.setFillColor(PRIMARY_BLUE)
        c.drawRightString(col_x[6] - 1.5 * mm, row_text_y, f"₹{item['total_price']:.2f}")

        cursor_y -= row_h

    # -----------------------
    # Footer
    # -----------------------
    footer_y = y0 + margin + 3*mm

    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(PRIMARY_BLUE)
    c.drawString(left, footer_y, "❯❯   Thank you for your visit")

    summary_y = footer_top + 10*mm
    label_x = right - 52*mm
    value_x = right - 2*mm

    c.setStrokeColor(PRIMARY_BLUE)
    c.setDash(2,2)
    c.line(label_x, summary_y+6*mm, value_x, summary_y+6*mm)
    c.setDash()

    c.setFont(FONT_BOLD, 9)
    c.setFillColor(TEXT_DARK)
    c.drawString(label_x, summary_y, "Subtotal")
    c.drawRightString(value_x, summary_y, f"₹ {data['subtotal']:.2f}")

    summary_y -= 5*mm

    if data["discount_percent"] > 0:
        discount = data["subtotal"]-data["grand_total"]
        c.setFont(FONT_BOLD, 9)
        c.setFillColor(TEXT_DARK)
        c.drawString(label_x, summary_y, f"Discount ({data['discount_percent']:.1f}%)")
        c.setFillColor(RED)
        c.drawRightString(value_x, summary_y, f"- ₹ {discount:.2f}")
        summary_y -= 6*mm

    c.setStrokeColor(PRIMARY_BLUE)
    c.setLineWidth(0.8)
    c.line(label_x, summary_y+2*mm, value_x, summary_y+2*mm)

    summary_y -= 4*mm

    c.setFont(FONT_BOLD, 11)
    c.setFillColor(PRIMARY_BLUE)
    c.drawString(label_x, summary_y, "GRAND TOTAL")
    c.drawRightString(value_x, summary_y, f"₹ {data['grand_total']:.2f}")

    return