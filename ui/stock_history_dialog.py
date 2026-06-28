"""
Stock History dialog — a complete log of every stock receipt (new
medicines added and restocks), filterable by medicine/batch, seller, and
date range. This is what answers "what did we receive from XYZ Medical
Shop?" or "when was this last restocked?".
"""

from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView,
)

from db import queries


class StockHistoryDialog(QDialog):
    SEARCH_DEBOUNCE_MS = 250

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stock History")
        self.setMinimumSize(820, 560)
        self.date_filter_enabled = False

        layout = QVBoxLayout(self)

        layout.addLayout(self.build_filter_row())

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Received On", "Medicine", "Batch No", "Seller", "Packets", "Units/Packet", "Total Qty"]
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: 600; font-size: 13px; margin-top: 6px;")
        layout.addWidget(self.summary_label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.load_history()

    # ---------- Filters ----------

    def build_filter_row(self):
        row = QHBoxLayout()

        self.medicine_input = QLineEdit()
        self.medicine_input.setPlaceholderText("Search by medicine name or batch number...")
        self.medicine_input.textChanged.connect(self.on_filter_text_changed)
        row.addWidget(self.medicine_input, 2)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.load_history)

        self.seller_filter = QComboBox()
        self.seller_filter.addItem("All Sellers", None)
        for seller in queries.get_distinct_sellers():
            self.seller_filter.addItem(seller, seller)
        self.seller_filter.currentIndexChanged.connect(self.load_history)
        row.addWidget(self.seller_filter)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd-MM-yyyy")
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.dateChanged.connect(self.load_history)
        row.addWidget(QLabel("From"))
        row.addWidget(self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd-MM-yyyy")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.load_history)
        row.addWidget(QLabel("To"))
        row.addWidget(self.date_to)

        self.date_toggle_btn = QPushButton("Filter by Date")
        self.date_toggle_btn.setCheckable(True)
        self.date_toggle_btn.toggled.connect(self.on_date_toggle)
        row.addWidget(self.date_toggle_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_filters)
        row.addWidget(clear_btn)

        return row

    def on_filter_text_changed(self):
        self.search_timer.start(self.SEARCH_DEBOUNCE_MS)

    def on_date_toggle(self, checked):
        self.date_filter_enabled = checked
        self.date_toggle_btn.setText("Date Filter: ON" if checked else "Filter by Date")
        self.load_history()

    def clear_filters(self):
        self.medicine_input.blockSignals(True)
        self.medicine_input.clear()
        self.medicine_input.blockSignals(False)
        self.seller_filter.setCurrentIndex(0)
        self.date_toggle_btn.setChecked(False)  # triggers on_date_toggle -> load_history

    # ---------- Data loading ----------

    def load_history(self):
        medicine_query = self.medicine_input.text().strip() or None
        seller_name = self.seller_filter.currentData()
        date_from = self.date_from.date().toString("yyyy-MM-dd") if self.date_filter_enabled else None
        date_to = self.date_to.date().toString("yyyy-MM-dd") if self.date_filter_enabled else None

        rows = queries.get_stock_history(
            medicine_query=medicine_query, seller_name=seller_name,
            date_from=date_from, date_to=date_to,
        )

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        total_qty = 0

        for row_index, entry in enumerate(rows):
            self.table.setItem(row_index, 0, QTableWidgetItem(self.format_datetime(entry["received_at"])))
            self.table.setItem(row_index, 1, QTableWidgetItem(entry["medicine_name"]))
            self.table.setItem(row_index, 2, QTableWidgetItem(entry["batch_no"] or "—"))
            self.table.setItem(row_index, 3, QTableWidgetItem(entry["seller_name"] or "—"))
            self.table.setItem(row_index, 4, QTableWidgetItem(str(entry["packets"]) if entry["packets"] else "—"))
            self.table.setItem(row_index, 5, QTableWidgetItem(str(entry["units_per_packet"]) if entry["units_per_packet"] else "—"))
            self.table.setItem(row_index, 6, QTableWidgetItem(str(entry["quantity_added"])))
            total_qty += entry["quantity_added"]

        self.table.setSortingEnabled(True)
        self.summary_label.setText(f"{len(rows)} receipt(s) — {total_qty} total unit(s) received")

    @staticmethod
    def format_datetime(value):
        if not value:
            return "-"
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d-%b-%Y %H:%M")
        except ValueError:
            return value
