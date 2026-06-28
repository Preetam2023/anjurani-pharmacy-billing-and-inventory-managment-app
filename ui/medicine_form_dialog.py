"""
Dialog used for both Add Medicine and Edit Medicine.

In edit mode, stock isn't editable here — stock changes always go through
the separate Add Stock dialog, so a stock change is always an explicit,
deliberate action rather than something that can slip through while
editing other details.

Seller/Distributor is a searchable, editable dropdown: it remembers every
seller name ever used (type to filter the list) and defaults to whichever
seller was used most recently, since the same distributor often supplies
several medicines in one delivery — the cashier can still change it.

Initial stock is entered as Packets x Units per Packet (e.g. 15 packets
of 10 tablets = 150 total) rather than one raw number, since that's how
stock actually arrives and is far less error-prone to enter or verify.
"""

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDateEdit, QDoubleSpinBox,
    QComboBox, QCompleter, QDialogButtonBox, QLabel, QMessageBox, QHBoxLayout,
)

from db import queries
from ui.widgets import SelectAllSpinBox


class MedicineFormDialog(QDialog):
    def __init__(self, parent=None, medicine=None):
        super().__init__(parent)
        self.medicine = medicine  # None => Add mode, a db row => Edit mode
        self.setWindowTitle("Edit Medicine" if medicine else "Add Medicine")
        self.setMinimumWidth(380)

        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.batch_input = QLineEdit()

        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDisplayFormat("dd-MM-yyyy")
        self.expiry_input.setDate(QDate.currentDate().addYears(1))

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 1_000_000)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("₹ ")

        self.seller_input = QComboBox()
        self.seller_input.setEditable(True)
        sellers = queries.get_distinct_sellers()
        self.seller_input.addItems(sellers)
        completer = QCompleter(sellers, self.seller_input)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.seller_input.setCompleter(completer)

        layout.addRow("Medicine Name", self.name_input)
        layout.addRow("Batch Number", self.batch_input)
        layout.addRow("Expiry Date", self.expiry_input)
        layout.addRow("Price", self.price_input)
        layout.addRow("Seller / Distributor", self.seller_input)

        if medicine is None:
            self.packets_input = SelectAllSpinBox()
            self.packets_input.setRange(0, 100_000)
            self.packets_input.setValue(1)
            self.packets_input.lineEdit().textChanged.connect(self.update_stock_preview)

            self.units_per_packet_input = SelectAllSpinBox()
            self.units_per_packet_input.setRange(0, 100_000)
            self.units_per_packet_input.setValue(1)
            self.units_per_packet_input.lineEdit().textChanged.connect(self.update_stock_preview)

            packets_row = QHBoxLayout()
            packets_row.addWidget(self.packets_input)
            packets_row.addWidget(QLabel("packet(s) ×"))
            packets_row.addWidget(self.units_per_packet_input)
            packets_row.addWidget(QLabel("unit(s) per packet"))
            layout.addRow("Stock Received", packets_row)

            self.total_stock_label = QLabel("0")
            self.total_stock_label.setStyleSheet("font-weight: 600;")
            layout.addRow("Total Stock", self.total_stock_label)
            self.update_stock_preview()

            # Default to whichever seller was used last — saves retyping
            # the same distributor name for every item in a delivery.
            self.seller_input.setCurrentText(queries.get_last_used_seller())
        else:
            self.packets_input = None
            self.units_per_packet_input = None
            stock_note = QLabel(f"{medicine['stock']}  (use \"Add Stock\" to change this)")
            layout.addRow("Current Stock", stock_note)

            self.name_input.setText(medicine["name"])
            self.batch_input.setText(medicine["batch_no"])
            self.price_input.setValue(medicine["price"])
            self.seller_input.setCurrentText(medicine["seller_name"] or "")
            if medicine["expiry_date"]:
                year, month, day = map(int, medicine["expiry_date"].split("-"))
                self.expiry_input.setDate(QDate(year, month, day))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def update_stock_preview(self):
        """
        Reads the spinboxes' literal displayed text rather than relying on
        .value() while the user is still typing. QSpinBox.value() can
        briefly report a stale/clamped number mid-edit (most noticeably
        right after a full Backspace, just before new digits are typed),
        which is exactly the kind of glitch that made the old single
        "stock" field look like it was calculating wrong. Reading the
        text directly (treating an empty/partial field as 0) means the
        preview is always honest about the current input, never stale.
        """
        packets_text = self.packets_input.lineEdit().text().strip()
        units_text = self.units_per_packet_input.lineEdit().text().strip()
        packets = int(packets_text) if packets_text.isdigit() else 0
        units = int(units_text) if units_text.isdigit() else 0
        total = packets * units
        self.total_stock_label.setText(str(total))
        return total

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Missing Name", "Please enter the medicine name.")
            return
        if not self.batch_input.text().strip():
            QMessageBox.warning(self, "Missing Batch Number", "Please enter the batch number.")
            return
        if not self.seller_input.currentText().strip():
            QMessageBox.warning(
                self, "Missing Seller",
                "Please enter or select the seller/distributor name.",
            )
            return
        self.accept()

    def get_values(self):
        values = {
            "name": self.name_input.text().strip(),
            "batch_no": self.batch_input.text().strip(),
            "expiry_date": self.expiry_input.date().toString("yyyy-MM-dd"),
            "price": self.price_input.value(),
            "seller_name": self.seller_input.currentText().strip(),
        }
        if self.packets_input is not None:
            # force-resolve any in-progress typed text before reading the final value
            self.packets_input.interpretText()
            self.units_per_packet_input.interpretText()
            packets = self.packets_input.value()
            units = self.units_per_packet_input.value()
            values["stock"] = packets * units
            values["packets"] = packets
            values["units_per_packet"] = units
        return values
