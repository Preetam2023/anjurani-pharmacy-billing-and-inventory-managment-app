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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
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

        self.expiry_input = QLineEdit()
        self.expiry_input.setInputMask("99/99")
        self.expiry_input.setPlaceholderText("MM/YY")
        self.expiry_input.setMaxLength(5)

        self.packet_price_input = QDoubleSpinBox()
        self.packet_price_input.setRange(0, 100000)
        self.packet_price_input.setDecimals(2)
        self.packet_price_input.setPrefix("₹ ")

        self.packet_price_input.valueChanged.connect(self.update_stock_preview)

        self.seller_input = QComboBox()
        self.seller_input.setEditable(True)
        sellers = queries.get_distinct_sellers()
        self.seller_input.addItems(sellers)
        completer = QCompleter(sellers, self.seller_input)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.seller_input.setCompleter(completer)

        layout.addRow("Medicine Name", self.name_input)
        layout.addRow("Batch Number (Optional)", self.batch_input)
        layout.addRow("Expiry (MM/YY) (Optional)", self.expiry_input)
        layout.addRow("Packet Price", self.packet_price_input)
        layout.addRow("Seller / Distributor (Optional)", self.seller_input)

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
            
            
            self.unit_price_label = QLabel("₹0.00")
            self.unit_price_label.setStyleSheet("font-weight:600;")

            layout.addRow("Unit Price", self.unit_price_label)

            self.inventory_cost_label = QLabel("₹0.00")
            self.inventory_cost_label.setStyleSheet("font-weight:600;")

            layout.addRow("Inventory Cost", self.inventory_cost_label)
            self.update_stock_preview()

            # Default to whichever seller was used last — saves retyping
            # the same distributor name for every item in a delivery.
            self.seller_input.setCurrentText(queries.get_last_used_seller())
        else:
            self.stock_input = SelectAllSpinBox()
            self.stock_input.setRange(0, 1000000)
            self.stock_input.setValue(medicine["stock"])

            layout.addRow("Current Stock", self.stock_input)

            self.packets_input = None
            self.units_per_packet_input = None

            self.name_input.setText(medicine["name"])
            self.batch_input.setText(medicine["batch_no"] or "")
            self.packet_price_input.setValue(medicine["packet_price"])
            self.seller_input.setCurrentText(medicine["seller_name"] or "")
            if medicine["expiry_date"]:
                year, month, _ = medicine["expiry_date"].split("-")
                self.expiry_input.setText(f"{month}/{year[2:]}")
            else:
                self.expiry_input.setText("")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def update_stock_preview(self):
        if self.packets_input is None:
            return
        packets_text = self.packets_input.lineEdit().text().strip()
        units_text = self.units_per_packet_input.lineEdit().text().strip()

        packets = int(packets_text) if packets_text.isdigit() else 0
        units = int(units_text) if units_text.isdigit() else 0

        total_units = packets * units

        self.total_stock_label.setText(str(total_units))

        packet_price = self.packet_price_input.value()

        if units > 0:
            unit_price = packet_price / units
        else:
            unit_price = 0

        inventory_cost = packet_price * packets

        self.unit_price_label.setText(f"₹{unit_price:.2f}")

        self.inventory_cost_label.setText(
            f"₹{inventory_cost:.2f}"
        )

        return total_units

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Missing Name", "Please enter the medicine name.")
            return
        expiry = self.expiry_input.text().strip()
        if expiry.replace("/", "").strip() == "":
            expiry = ""

        if expiry:

            try:

                month, year = expiry.split("/")

                month = int(month)

                year = int(year)

                if month < 1 or month > 12:

                    raise ValueError
                if year < 0 or year > 99:
                    raise ValueError

            except:

                QMessageBox.warning(
                    self,
                    "Invalid Expiry",
                    "Use MM/YY format.\nExample: 06/27"
                )
                return
        self.accept()

    def get_values(self):
        expiry = self.expiry_input.text().strip()
        if expiry.replace("/", "").strip() == "":
            expiry = ""
        expiry_date = None

        if expiry:
            month, year = expiry.split("/")
            expiry_date = f"20{year}-{month}-01"
            
        values = {
            "name": self.name_input.text().strip(),
            "batch_no": self.batch_input.text().strip() or None,
            "expiry_date": expiry_date,
            "packet_price": self.packet_price_input.value(),
            "seller_name": self.seller_input.currentText().strip() or None,
        }
        if self.medicine is not None:
            self.stock_input.interpretText()
            values["stock"] = self.stock_input.value()
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
