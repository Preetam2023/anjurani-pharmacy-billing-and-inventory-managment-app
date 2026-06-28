"""
Generates a professional PDF invoice for a completed sale.
Saved into the project's reports/ folder, named after the invoice number.
"""

import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from logic.config import STORE_NAME, STORE_ADDRESS, STORE_PHONE, STORE_GSTIN

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")


def generate_invoice_pdf(invoice_no, invoice_date, items, subtotal,
                          discount_percent, grand_total,
                          customer_name=None, customer_phone=None):
    """
    items: list of dicts with 'name', 'batch_no', 'quantity', 'unit_price', 'total_price'
    Returns the full filesystem path of the generated PDF.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filepath = os.path.join(REPORTS_DIR, f"{invoice_no}.pdf")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "StoreTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=18,
    )
    sub_style = ParagraphStyle(
        "StoreSub", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9,
        textColor=colors.grey,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10,
        textColor=colors.grey,
    )

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
    )

    elements = []
    elements.append(Paragraph(STORE_NAME, title_style))

    address_line = STORE_ADDRESS
    if STORE_PHONE:
        address_line += f" &nbsp;|&nbsp; Phone: {STORE_PHONE}"
    if STORE_GSTIN:
        address_line += f" &nbsp;|&nbsp; GSTIN: {STORE_GSTIN}"
    elements.append(Paragraph(address_line, sub_style))
    elements.append(Spacer(1, 10 * mm))

    meta_data = [[f"Invoice No: {invoice_no}", f"Date: {invoice_date}"]]
    if customer_name or customer_phone:
        meta_data.append([
            f"Customer: {customer_name or '-'}",
            f"Phone: {customer_phone or '-'}",
        ])
    meta_table = Table(meta_data, colWidths=[90 * mm, 80 * mm])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 6 * mm))

    table_data = [["#", "Medicine", "Batch No", "Qty", "Unit Price", "Total"]]
    for i, item in enumerate(items, start=1):
        table_data.append([
            str(i),
            item["name"],
            item.get("batch_no", "-"),
            str(item["quantity"]),
            f"Rs. {item['unit_price']:.2f}",
            f"Rs. {item['total_price']:.2f}",
        ])

    items_table = Table(
        table_data,
        colWidths=[10 * mm, 55 * mm, 30 * mm, 15 * mm, 30 * mm, 30 * mm],
        repeatRows=1,
    )
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e2a38")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 6 * mm))

    discount_amount = subtotal - grand_total
    totals_data = [
        ["", "Subtotal:", f"Rs. {subtotal:.2f}"],
        ["", f"Discount ({discount_percent:.1f}%):", f"- Rs. {discount_amount:.2f}"],
        ["", "Grand Total:", f"Rs. {grand_total:.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[80 * mm, 40 * mm, 40 * mm])
    totals_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (1, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (1, 2), (-1, 2), 12),
        ("LINEABOVE", (1, 2), (-1, 2), 0.8, colors.HexColor("#1e2a38")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 14 * mm))

    elements.append(Paragraph("Thank you for your purchase. Visit again!", footer_style))

    doc.build(elements)
    return filepath
