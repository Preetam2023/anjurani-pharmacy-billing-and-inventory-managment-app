"""
Dialog for adding stock to an existing medicine.

Stock is entered as Packets x Units per Packet (e.g. 15 packets of 10
tablets = 150 units) rather than one raw number — matches how stock
actually arrives and is much easier to verify against a delivery note.
Shows current stock and a live preview of what the new total will be.

Also asks which seller/distributor this particular delivery came from —
a restock doesn't always come from the same distributor as the original
stock, and this is what makes "show everything received from XYZ"
possible in Stock History.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QDialogButtonBox,
    QHBoxLayout,
    QComboBox,
    QCompleter,
    QDoubleSpinBox,
)

from db import queries
from ui.widgets import SelectAllSpinBox


class AddStockDialog(QDialog):
    def __init__(self, parent=None, medicine=None):
        super().__init__(parent)
        self.medicine = medicine
        self.setWindowTitle(f"Add Stock — {medicine['name']}")
        self.setMinimumWidth(340)

        layout = QFormLayout(self)

        self.current_label = QLabel(str(medicine["stock"]))
        layout.addRow("Current Stock", self.current_label)
        self.packet_price_input = QDoubleSpinBox()
        self.packet_price_input.setRange(0, 100000)
        self.packet_price_input.setDecimals(2)
        self.packet_price_input.setPrefix("₹ ")
        self.packet_price_input.setValue(medicine["packet_price"])
        self.packet_price_input.valueChanged.connect(self.update_preview)

        layout.addRow("Packet Price", self.packet_price_input)
        self.packets_input = SelectAllSpinBox()
        self.packets_input.setRange(1, 100_000)
        self.packets_input.setValue(1)
        self.packets_input.lineEdit().textChanged.connect(self.update_preview)

        self.units_per_packet_input = SelectAllSpinBox()
        self.units_per_packet_input.setRange(1, 100_000)
        self.units_per_packet_input.setValue(1)
        self.units_per_packet_input.lineEdit().textChanged.connect(self.update_preview)

        packets_row = QHBoxLayout()
        packets_row.addWidget(self.packets_input)
        packets_row.addWidget(QLabel("packet(s) ×"))
        packets_row.addWidget(self.units_per_packet_input)
        packets_row.addWidget(QLabel("unit(s) per packet"))
        layout.addRow("Stock Received", packets_row)

        self.seller_input = QComboBox()
        self.seller_input.setEditable(True)
        sellers = queries.get_distinct_sellers()
        self.seller_input.addItems(sellers)
        completer = QCompleter(sellers, self.seller_input)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.seller_input.setCompleter(completer)
        # Default to this medicine's current seller, since that's most
        # often who's restocking it — easy to change if this delivery
        # came from someone else.
        self.seller_input.setCurrentText(medicine["seller_name"] or "")
        layout.addRow("Supplier (Optional)", self.seller_input)

        self.received_units_label = QLabel("0")
        self.received_units_label.setStyleSheet("font-weight:600;")
        layout.addRow("Received Units", self.received_units_label)

        self.purchase_cost_label = QLabel("₹0.00")
        self.purchase_cost_label.setStyleSheet("font-weight:600;")
        layout.addRow("Purchase Cost", self.purchase_cost_label)

        self.preview_label = QLabel("0")
        self.preview_label.setStyleSheet("font-weight:600;")
        layout.addRow("Updated Stock", self.preview_label)
        self.update_preview()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def update_preview(self):
        packets_text = self.packets_input.lineEdit().text().strip()
        units_text = self.units_per_packet_input.lineEdit().text().strip()

        packets = int(packets_text) if packets_text.isdigit() else 0
        units = int(units_text) if units_text.isdigit() else 0

        received_units = packets * units

        self.received_units_label.setText(str(received_units))

        purchase_cost = packets * self.packet_price_input.value()

        self.purchase_cost_label.setText(f"₹{purchase_cost:.2f}")

        new_total = self.medicine["stock"] + received_units

        self.preview_label.setText(str(new_total))

    def get_quantity(self):
        # force-resolve any in-progress typed text before reading the final value
        self.packets_input.interpretText()
        self.units_per_packet_input.interpretText()
        return self.packets_input.value() * self.units_per_packet_input.value()

    def get_packets(self):
        self.packets_input.interpretText()
        return self.packets_input.value()

    def get_units_per_packet(self):
        self.units_per_packet_input.interpretText()
        return self.units_per_packet_input.value()

    def get_seller_name(self):
        return self.seller_input.currentText().strip()
    
    def get_packet_price(self):
        return self.packet_price_input.value()
