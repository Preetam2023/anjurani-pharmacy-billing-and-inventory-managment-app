"""
Captures buyer name and phone number before generating a bill.

If the phone number matches an existing customer, their name is looked
up and filled in automatically. Both fields are optional — leave them
blank and click OK for an anonymous/walk-in sale.
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QLabel, QMessageBox,
)

from db import queries


class CustomerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customer Details")
        self.setMinimumWidth(340)

        layout = QFormLayout(self)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. 9876543210")
        self.phone_input.editingFinished.connect(self.lookup_customer)
        layout.addRow("Phone Number", self.phone_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Buyer name")
        layout.addRow("Customer Name", self.name_input)

        self.status_label = QLabel(" ")
        self.status_label.setStyleSheet("color: #2563eb; font-size: 12px;")
        layout.addRow("", self.status_label)

        note = QLabel("Leave both blank to skip (walk-in sale).")
        note.setStyleSheet("color: #6b7785; font-size: 11px;")
        layout.addRow(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def lookup_customer(self):
        phone = self.phone_input.text().strip()
        if not phone:
            self.status_label.setText(" ")
            return
        customer = queries.get_customer_by_phone(phone)
        if customer:
            self.name_input.setText(customer["name"])
            self.status_label.setText("Existing customer found.")
        else:
            self.status_label.setText("New customer — name will be saved.")

    def validate_and_accept(self):
        phone = self.phone_input.text().strip()
        name = self.name_input.text().strip()
        if phone and not name:
            QMessageBox.warning(self, "Missing Name", "Please enter the customer's name.")
            return
        self.accept()

    def get_values(self):
        return {
            "phone": self.phone_input.text().strip(),
            "name": self.name_input.text().strip(),
        }
