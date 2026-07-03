"""
Sales History screen — browse past invoices, search by invoice number or
date, view item-level detail, and reprint (re-open / regenerate) the PDF.
"""

import os
import sys
from datetime import datetime

from PySide6.QtCore import Qt, QUrl, QDate
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QDateEdit, QMessageBox, QFrame,
)

from db import queries
from reports.invoice_pdf import generate_invoice_pdf, REPORTS_DIR
from ui.sales_summary_dialog import SalesSummaryDialog


class HistoryScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_invoice_id = None
        self.date_filter_enabled = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Sales History")
        title.setObjectName("screenTitle")
        layout.addWidget(title)

        layout.addLayout(self.build_filter_row())

        body = QHBoxLayout()
        body.addWidget(self.build_invoice_table(), 3)
        body.addWidget(self.build_detail_panel(), 2)
        layout.addLayout(body)

        self.load_invoices()

    def showEvent(self, event):
        # Refresh every time this screen becomes visible, so a sale just
        # made on the Billing screen shows up here immediately.
        super().showEvent(event)
        self.load_invoices()

    # ---------- Filters ----------

    def build_filter_row(self):
        row = QHBoxLayout()

        self.invoice_no_input = QLineEdit()
        self.invoice_no_input.setPlaceholderText("Search by invoice number...")
        self.invoice_no_input.textChanged.connect(self.load_invoices)
        row.addWidget(self.invoice_no_input, 2)

        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDisplayFormat("dd-MM-yyyy")
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.dateChanged.connect(self.load_invoices)
        row.addWidget(self.date_filter)

        self.date_toggle_btn = QPushButton("Filter by Date")
        self.date_toggle_btn.setCheckable(True)
        self.date_toggle_btn.toggled.connect(self.on_date_toggle)
        row.addWidget(self.date_toggle_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_filters)
        row.addWidget(clear_btn)

        summary_btn = QPushButton("Sales Summary")
        summary_btn.clicked.connect(self.open_sales_summary)
        row.addWidget(summary_btn)

        row.addStretch()
        return row

    def open_sales_summary(self):
        dialog = SalesSummaryDialog(self)
        dialog.date_selected.connect(self.apply_date_from_summary)
        dialog.exec()

    def apply_date_from_summary(self, iso_date):
        """Called when a day row is double-clicked in the Sales Summary
        dialog — jumps History's date filter straight to that day."""
        year, month, day = map(int, iso_date.split("-"))
        self.date_filter.setDate(QDate(year, month, day))
        self.date_toggle_btn.setChecked(True)  # triggers on_date_toggle -> load_invoices

    def on_date_toggle(self, checked):
        self.date_filter_enabled = checked
        self.date_toggle_btn.setText("Date Filter: ON" if checked else "Filter by Date")
        self.load_invoices()

    def clear_filters(self):
        self.invoice_no_input.blockSignals(True)
        self.invoice_no_input.clear()
        self.invoice_no_input.blockSignals(False)
        self.date_toggle_btn.setChecked(False)  # triggers on_date_toggle -> load_invoices

    # ---------- Invoice table ----------

    def build_invoice_table(self):
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(4)
        self.invoices_table.setHorizontalHeaderLabels(["Invoice No", "Date", "Customer", "Total"])
        self.invoices_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.invoices_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.invoices_table.verticalHeader().setVisible(False)
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.invoices_table.itemSelectionChanged.connect(self.on_invoice_selected)
        return self.invoices_table

    def load_invoices(self):
        invoice_no_query = self.invoice_no_input.text().strip() or None
        date_query = self.date_filter.date().toString("yyyy-MM-dd") if self.date_filter_enabled else None

        invoices = queries.search_invoices(invoice_no=invoice_no_query, target_date=date_query)
        self.invoices_table.setRowCount(len(invoices))
        for row_index, inv in enumerate(invoices):
            no_item = QTableWidgetItem(inv["invoice_no"])
            no_item.setData(Qt.ItemDataRole.UserRole, inv["id"])
            self.invoices_table.setItem(row_index, 0, no_item)
            self.invoices_table.setItem(row_index, 1, QTableWidgetItem(self.format_datetime(inv["invoice_date"])))
            self.invoices_table.setItem(row_index, 2, QTableWidgetItem(inv["customer_name"] or "Walk-in"))
            self.invoices_table.setItem(row_index, 3, QTableWidgetItem(f"₹{inv['grand_total']:.2f}"))

        self.clear_detail_panel()

    # ---------- Detail panel ----------

    def build_detail_panel(self):
        container = QFrame()
        layout = QVBoxLayout(container)

        self.detail_title = QLabel("Select an invoice to view details")
        self.detail_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        self.detail_title.setWordWrap(True)
        layout.addWidget(self.detail_title)

        self.detail_meta = QLabel("")
        self.detail_meta.setStyleSheet("color: #6b7785; font-size: 12px;")
        self.detail_meta.setWordWrap(True)
        layout.addWidget(self.detail_meta)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Medicine", "Qty", "Price", "Total"])
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items_table.verticalHeader().setVisible(False)
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.items_table)

        self.detail_totals = QLabel("")
        self.detail_totals.setStyleSheet("font-size: 13px; margin-top: 6px;")
        layout.addWidget(self.detail_totals)

        self.reprint_btn = QPushButton("Reprint Invoice")
        self.reprint_btn.setEnabled(False)
        self.reprint_btn.clicked.connect(self.handle_reprint)
        layout.addWidget(self.reprint_btn)

        return container

    def on_invoice_selected(self):
        row = self.invoices_table.currentRow()
        if row < 0:
            self.clear_detail_panel()
            return
        invoice_id = self.invoices_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.selected_invoice_id = invoice_id
        self.show_invoice_detail(invoice_id)

    def show_invoice_detail(self, invoice_id):
        invoice = queries.get_invoice_by_id(invoice_id)
        if invoice is None:
            return
        items = queries.get_invoice_items(invoice_id)

        self.detail_title.setText(f"Invoice {invoice['invoice_no']}")
        customer_line = invoice["customer_name"] or "Walk-in customer"
        if invoice["customer_phone"]:
            customer_line += f"  ·  {invoice['customer_phone']}"
        self.detail_meta.setText(f"{self.format_datetime(invoice['invoice_date'])}\n{customer_line}")

        self.items_table.setRowCount(len(items))
        for row_index, item in enumerate(items):
            self.items_table.setItem(row_index, 0, QTableWidgetItem(item["medicine_name"]))
            self.items_table.setItem(row_index, 1, QTableWidgetItem(str(item["quantity"])))
            self.items_table.setItem(row_index, 2, QTableWidgetItem(f"₹{item['unit_price']:.2f}"))
            self.items_table.setItem(row_index, 3, QTableWidgetItem(f"₹{item['total_price']:.2f}"))

        discount_amount = invoice["subtotal"] - invoice["grand_total"]
        self.detail_totals.setText(
            f"Subtotal: ₹{invoice['subtotal']:.2f}\n"
            f"Discount ({invoice['discount_percent']:.1f}%): -₹{discount_amount:.2f}\n"
            f"Grand Total: ₹{invoice['grand_total']:.2f}"
        )

        self.reprint_btn.setEnabled(True)

    def clear_detail_panel(self):
        self.selected_invoice_id = None
        self.detail_title.setText("Select an invoice to view details")
        self.detail_meta.setText("")
        self.items_table.setRowCount(0)
        self.detail_totals.setText("")
        self.reprint_btn.setEnabled(False)

    # ---------- Reprint ----------

    def handle_reprint(self):
        if self.selected_invoice_id is None:
            return

        invoice = queries.get_invoice_by_id(self.selected_invoice_id)
        items = queries.get_invoice_items(self.selected_invoice_id)

        pdf_path = os.path.join(REPORTS_DIR, f"{invoice['invoice_no']}.pdf")
        if not os.path.exists(pdf_path):
            # File was moved/deleted, or this invoice predates PDF generation
            # being added — regenerate it from the stored invoice data.
            pdf_items = [
                {
                    "name": item["medicine_name"],
                    "batch_no": item["batch_no"] or "-",
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "total_price": item["total_price"],
                }
                for item in items
            ]
            pdf_path = generate_invoice_pdf(
                invoice_no=invoice["invoice_no"],
                invoice_date=self.format_datetime(invoice["invoice_date"]),
                items=pdf_items,
                subtotal=invoice["subtotal"],
                discount_percent=invoice["discount_percent"],
                grand_total=invoice["grand_total"],
                customer_name=invoice["customer_name"],
                customer_phone=invoice["customer_phone"],
            )

        try:
            if sys.platform == "win32":
                os.startfile(pdf_path)
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
        except Exception as e:
            QMessageBox.warning(
                self, "Couldn't Open PDF Automatically",
                f"The PDF is saved at:\n{pdf_path}\n\nbut couldn't be opened automatically: {e}",
            )

    # ---------- Helpers ----------

    @staticmethod
    def format_datetime(value):
        if not value:
            return "-"
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d-%b-%Y %H:%M")
        except ValueError:
            return value
