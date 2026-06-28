"""
Sales Summary dialog — totals grouped by day, month, or year, so the
store owner can quickly see how business is trending over time.

Double-clicking a day row (while in "Day" view) closes this dialog and
tells the History screen to filter to that exact date, so the owner can
drill straight down into that day's actual invoices.
"""

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup,
    QRadioButton, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
)

from db import queries


class SalesSummaryDialog(QDialog):
    date_selected = Signal(str)  # emits 'YYYY-MM-DD'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sales Summary")
        self.setMinimumSize(480, 520)
        self.granularity = "day"

        layout = QVBoxLayout(self)

        toggle_row = QHBoxLayout()
        toggle_row.addWidget(QLabel("View by:"))

        self.button_group = QButtonGroup(self)
        for label, value in [("Day", "day"), ("Month", "month"), ("Year", "year")]:
            radio = QRadioButton(label)
            radio.setChecked(value == "day")
            radio.toggled.connect(lambda checked, v=value: self.on_granularity_changed(v, checked))
            self.button_group.addButton(radio)
            toggle_row.addWidget(radio)
        toggle_row.addStretch()
        layout.addLayout(toggle_row)

        hint = QLabel("Double-click a day row to view that day's invoices in History.")
        hint.setStyleSheet("color: #6b7785; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Period", "Bills", "Total Sales"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.doubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table)

        self.total_label = QLabel("")
        self.total_label.setStyleSheet("font-weight: 600; font-size: 13px; margin-top: 6px;")
        layout.addWidget(self.total_label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.load_summary()

    def on_granularity_changed(self, value, checked):
        if checked:
            self.granularity = value
            self.load_summary()

    def load_summary(self):
        rows = queries.get_sales_summary(self.granularity)
        self.table.setRowCount(len(rows))

        grand_total_sales = 0.0
        grand_total_bills = 0

        for row_index, row in enumerate(rows):
            period_item = QTableWidgetItem(self.format_period(row["period"]))
            period_item.setData(Qt.ItemDataRole.UserRole, row["period"])
            self.table.setItem(row_index, 0, period_item)
            self.table.setItem(row_index, 1, QTableWidgetItem(str(row["bills"])))
            self.table.setItem(row_index, 2, QTableWidgetItem(f"₹{row['total_sales']:.2f}"))

            grand_total_sales += row["total_sales"]
            grand_total_bills += row["bills"]

        self.total_label.setText(
            f"Overall: {grand_total_bills} bill(s) totalling ₹{grand_total_sales:.2f}"
        )

    def on_row_double_clicked(self, index):
        if self.granularity != "day":
            return
        row = index.row()
        raw_period = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.date_selected.emit(raw_period)
        self.accept()

    def format_period(self, raw_value):
        try:
            if self.granularity == "day":
                return datetime.strptime(raw_value, "%Y-%m-%d").strftime("%d-%b-%Y")
            elif self.granularity == "month":
                return datetime.strptime(raw_value, "%Y-%m").strftime("%b %Y")
            return raw_value
        except ValueError:
            return raw_value
