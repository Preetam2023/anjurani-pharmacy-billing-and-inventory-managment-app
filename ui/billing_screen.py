"""
Billing Counter screen — search medicines (or use quick-add for frequently
sold items), build a cart, apply a discount, capture buyer details, and
generate the invoice (saves it, reduces stock, and writes a PDF receipt).
"""

from datetime import datetime
import os
import sys
import subprocess
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QSpinBox, QDoubleSpinBox, QMessageBox, QFrame, QScrollArea, QDialog,
    QDialogButtonBox,
)

from db import queries
from db.queries import InsufficientStockError
from logic.billing import calculate_line_total, calculate_subtotal, calculate_grand_total
from reports.invoice_pdf import generate_invoice_pdf
from ui.customer_dialog import CustomerDialog

class BillSavedDialog(QDialog):
    def __init__(self, parent, invoice_no, grand_total):
        super().__init__(parent)

        self.print_clicked = False

        self.setWindowTitle("Bill Saved")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        title = QLabel("✔ Bill Saved Successfully")
        title.setStyleSheet(
            "font-size:16px;"
            "font-weight:700;"
            "color:#15803d;"
        )
        layout.addWidget(title)

        layout.addSpacing(10)

        layout.addWidget(QLabel(f"Invoice : {invoice_no}"))
        layout.addWidget(QLabel(f"Total : ₹{grand_total:.2f}"))

        layout.addSpacing(15)

        buttons = QDialogButtonBox()

        print_btn = buttons.addButton(
            "Print Receipt",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )

        close_btn = buttons.addButton(
            "Close",
            QDialogButtonBox.ButtonRole.RejectRole,
        )

        print_btn.clicked.connect(self.print_bill)
        close_btn.clicked.connect(self.reject)

        layout.addWidget(buttons)

    def print_bill(self):
        self.print_clicked = True
        self.accept()

class BillingScreen(QWidget):
    SEARCH_DEBOUNCE_MS = 250
    CART_ROW_HEIGHT = 44

    def __init__(self):
        super().__init__()
        # medicine_id -> {"name", "batch_no", "unit_price", "quantity", "stock"}
        self.cart = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        root.addLayout(self.build_search_panel(), 3)
        root.addLayout(self.build_cart_panel(), 2)

        self.refresh_quick_add()

    def showEvent(self, event):
        # Refresh quick-add rankings each time the screen becomes visible —
        # cheap query, and keeps it accurate as sales happen elsewhere.
        super().showEvent(event)
        self.refresh_quick_add()

    # ---------- Search panel ----------

    def build_search_panel(self):
        layout = QVBoxLayout()

        title = QLabel("Billing")
        title.setObjectName("screenTitle")
        layout.addWidget(title)

        quick_add_label = QLabel("Quick Add (frequently sold)")
        quick_add_label.setStyleSheet("color: #6b7785; font-size: 12px; margin-top: 4px;")
        layout.addWidget(quick_add_label)
        layout.addWidget(self.build_quick_add_panel())

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search medicine by name or batch number...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        layout.addWidget(self.search_input)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Name", "Batch No", "Exp. Date", "Price", "Stock"])
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.verticalHeader().setVisible(False)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.doubleClicked.connect(self.add_selected_to_cart)
        layout.addWidget(self.results_table)

        add_btn = QPushButton("Add to Cart")
        add_btn.clicked.connect(self.add_selected_to_cart)
        layout.addWidget(add_btn)

        return layout

    def build_quick_add_panel(self):
        self.quick_add_container = QWidget()
        self.quick_add_layout = QHBoxLayout(self.quick_add_container)
        self.quick_add_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_add_layout.setSpacing(8)
        self.quick_add_layout.addStretch()  # keeps chips left-aligned as they're added

        scroll = QScrollArea()
        scroll.setWidget(self.quick_add_container)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(48)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.quick_add_scroll = scroll
        return scroll

    def refresh_quick_add(self):
        # clear existing chips (everything except the trailing stretch)
        while self.quick_add_layout.count() > 1:
            item = self.quick_add_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        top_medicines = queries.get_most_sold_medicines(limit=8)
        self.quick_add_scroll.setVisible(len(top_medicines) > 0)

        for med in top_medicines:
            chip = QPushButton(med["name"])
            chip.setObjectName("quickAddChip")
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.clicked.connect(lambda _, mid=med["id"]: self.quick_add_click(mid))
            self.quick_add_layout.insertWidget(self.quick_add_layout.count() - 1, chip)

    def on_search_text_changed(self):
        # restart the timer on every keystroke — only the last pause fires a query
        self.search_timer.start(self.SEARCH_DEBOUNCE_MS)

    @staticmethod
    def format_expiry(iso_date):
        if not iso_date:
            return "—"
        try:
            return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d-%b-%Y")
        except ValueError:
            return iso_date

    def perform_search(self):
        query = self.search_input.text().strip()
        self.results_table.setRowCount(0)
        if not query:
            return

        results = queries.search_medicines(query)
        self.results_table.setRowCount(len(results))
        for row_index, med in enumerate(results):
            name_item = QTableWidgetItem(med["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, med["id"])
            self.results_table.setItem(row_index, 0, name_item)
            self.results_table.setItem(row_index, 1, QTableWidgetItem(med["batch_no"]))
            self.results_table.setItem(row_index, 2, QTableWidgetItem(self.format_expiry(med["expiry_date"])))
            self.results_table.setItem(row_index, 3, QTableWidgetItem(f"₹{med['price']:.2f}"))
            self.results_table.setItem(row_index, 4, QTableWidgetItem(str(med["stock"])))

    def add_selected_to_cart(self):
        row = self.results_table.currentRow()
        if row < 0:
            return
        medicine_id = self.results_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.add_medicine_to_cart(medicine_id)

    def add_medicine_to_cart(self, medicine_id):
        """Shared by both the search 'Add to Cart' button and the quick-add chips."""
        medicine = queries.get_medicine_by_id(medicine_id)
        if medicine is None:
            return

        if medicine["stock"] <= 0:
            QMessageBox.warning(self, "Out of Stock", f"'{medicine['name']}' has no stock available.")
            return

        if medicine_id in self.cart:
            line = self.cart[medicine_id]
            if line["quantity"] < medicine["stock"]:
                line["quantity"] += 1
            else:
                QMessageBox.warning(
                    self, "Stock Limit Reached",
                    f"Only {medicine['stock']} unit(s) of '{medicine['name']}' are in stock.",
                )
        else:
            self.cart[medicine_id] = {
                "name": medicine["name"],
                "batch_no": medicine["batch_no"],
                "expiry_date": medicine["expiry_date"],
                "unit_price": medicine["price"],
                "stock": medicine["stock"],
                "quantity": 1,
            }

        self.refresh_cart_table()

    def quick_add_click(self, medicine_id):
        """
        Quick-add chip clicked: show that medicine in the search/results
        panel — same columns, same single-row selection — exactly as if
        the cashier had searched for it. Does NOT add it to the cart;
        the cashier reviews stock/price and clicks "Add to Cart" (or
        double-clicks the row) themselves, same as a normal search.
        """
        medicine = queries.get_medicine_by_id(medicine_id)
        if medicine is None:
            return

        self.search_input.blockSignals(True)
        self.search_input.setText(medicine["name"])
        self.search_input.blockSignals(False)

        self.results_table.setRowCount(1)
        name_item = QTableWidgetItem(medicine["name"])
        name_item.setData(Qt.ItemDataRole.UserRole, medicine["id"])
        self.results_table.setItem(0, 0, name_item)
        self.results_table.setItem(0, 1, QTableWidgetItem(medicine["batch_no"]))
        self.results_table.setItem(0, 2, QTableWidgetItem(self.format_expiry(medicine["expiry_date"])))
        self.results_table.setItem(0, 3, QTableWidgetItem(f"₹{medicine['price']:.2f}"))
        self.results_table.setItem(0, 4, QTableWidgetItem(str(medicine["stock"])))
        self.results_table.selectRow(0)

    # ---------- Cart panel ----------

    def build_cart_panel(self):
        layout = QVBoxLayout()

        cart_label = QLabel("Cart")
        cart_label.setObjectName("screenTitle")
        layout.addWidget(cart_label)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Name", "Qty", "Price", "Total", ""])
        self.cart_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.verticalHeader().setDefaultSectionSize(self.CART_ROW_HEIGHT)
        header = self.cart_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.cart_table.setColumnWidth(4, 90)
        layout.addWidget(self.cart_table)

        totals_frame = QFrame()
        totals_layout = QVBoxLayout(totals_frame)

        subtotal_row = QHBoxLayout()
        subtotal_row.addWidget(QLabel("Subtotal"))
        subtotal_row.addStretch()
        self.subtotal_label = QLabel("₹0.00")
        subtotal_row.addWidget(self.subtotal_label)
        totals_layout.addLayout(subtotal_row)

        discount_row = QHBoxLayout()
        discount_row.addWidget(QLabel("Discount (%)"))
        discount_row.addStretch()
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setRange(0, 100)
        self.discount_input.setDecimals(1)
        self.discount_input.setMaximumWidth(90)
        self.discount_input.valueChanged.connect(self.update_totals)
        discount_row.addWidget(self.discount_input)
        totals_layout.addLayout(discount_row)

        total_row = QHBoxLayout()
        total_label = QLabel("Total")
        total_label.setStyleSheet("font-weight: 700; font-size: 16px;")
        total_row.addWidget(total_label)
        total_row.addStretch()
        self.total_label = QLabel("₹0.00")
        self.total_label.setStyleSheet("font-weight: 700; font-size: 16px;")
        total_row.addWidget(self.total_label)
        totals_layout.addLayout(total_row)

        layout.addWidget(totals_frame)

        self.generate_btn = QPushButton("Generate Bill")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.handle_generate_bill)
        layout.addWidget(self.generate_btn)

        return layout

    def refresh_cart_table(self):
        self.cart_table.setRowCount(len(self.cart))
        for row_index, (medicine_id, line) in enumerate(self.cart.items()):
            self.cart_table.setRowHeight(row_index, self.CART_ROW_HEIGHT)
            self.cart_table.setItem(row_index, 0, QTableWidgetItem(line["name"]))

            qty_spin = QSpinBox()
            qty_spin.setRange(1, max(line["stock"], 1))
            qty_spin.setValue(line["quantity"])
            qty_spin.valueChanged.connect(
                lambda value, mid=medicine_id: self.on_quantity_changed(mid, value)
            )
            self.cart_table.setCellWidget(row_index, 1, qty_spin)

            self.cart_table.setItem(row_index, 2, QTableWidgetItem(f"₹{line['unit_price']:.2f}"))
            line_total = calculate_line_total(line["unit_price"], line["quantity"])
            self.cart_table.setItem(row_index, 3, QTableWidgetItem(f"₹{line_total:.2f}"))

            remove_btn = QPushButton("Remove")
            remove_btn.setObjectName("dangerButton")
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.clicked.connect(lambda _, mid=medicine_id: self.remove_from_cart(mid))
            self.cart_table.setCellWidget(row_index, 4, remove_btn)

        self.update_totals()

    def on_quantity_changed(self, medicine_id, value):
        if medicine_id in self.cart:
            self.cart[medicine_id]["quantity"] = value
            self.refresh_cart_table()

    def remove_from_cart(self, medicine_id):
        self.cart.pop(medicine_id, None)
        self.refresh_cart_table()

    def get_subtotal(self):
        return calculate_subtotal(list(self.cart.values()))

    def update_totals(self):
        subtotal = self.get_subtotal()
        discount_percent = self.discount_input.value()
        total = calculate_grand_total(subtotal, discount_percent)

        self.subtotal_label.setText(f"₹{subtotal:.2f}")
        self.total_label.setText(f"₹{total:.2f}")
        self.generate_btn.setEnabled(len(self.cart) > 0)

    # ---------- Generate bill ----------
    def open_pdf(self, pdf_path):
        """
        Open the generated PDF using the system's default PDF viewer.
        """

        try:
            if sys.platform.startswith("win"):
                os.startfile(pdf_path)

            elif sys.platform == "darwin":
                subprocess.Popen(["open", pdf_path])

            else:
                subprocess.Popen(["xdg-open", pdf_path])

        except Exception as e:
            QMessageBox.warning(
                self,
                "Unable to Open PDF",
                str(e),
            )
            
    def handle_generate_bill(self):
        if not self.cart:
            return

        customer_dialog = CustomerDialog(self)
        if customer_dialog.exec() != CustomerDialog.DialogCode.Accepted:
            return  # cashier cancelled — don't generate anything
        customer_values = customer_dialog.get_values()

        customer_id = None
        if customer_values["phone"]:
            customer_id = queries.get_or_create_customer(
                customer_values["phone"], customer_values["name"]
            )

        subtotal = self.get_subtotal()
        discount_percent = self.discount_input.value()
        grand_total = calculate_grand_total(subtotal, discount_percent)

        db_items = [
            {
                "medicine_id": medicine_id,
                "batch_no": line["batch_no"],
                "expiry_date": line.get("expiry_date"),
                "quantity": line["quantity"],
                "unit_price": line["unit_price"],
                "total_price": calculate_line_total(line["unit_price"], line["quantity"]),
            }
            for medicine_id, line in self.cart.items()
        ]

        invoice_no = queries.generate_invoice_no()

        try:
            queries.create_invoice(
                invoice_no=invoice_no,
                subtotal=subtotal,
                discount_percent=discount_percent,
                grand_total=grand_total,
                items=db_items,
                customer_id=customer_id,
            )
        except InsufficientStockError as e:
            QMessageBox.warning(self, "Insufficient Stock", str(e))
            return

        # build the PDF using the cart's display data (name, batch_no aren't
        # needed by the db layer, but they belong on the printed invoice)
        dialog = BillSavedDialog(
            self,
            invoice_no,
            grand_total,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.print_clicked:

            pdf_items = [
                {
                    "name": line["name"],
                    "batch_no": line["batch_no"],
                    "expiry_date": self.format_expiry(line.get("expiry_date")),
                    "quantity": line["quantity"],
                    "unit_price": line["unit_price"],
                    "total_price": calculate_line_total(
                    line["unit_price"],
                    line["quantity"],
                    ),
                }
                for line in self.cart.values()
            ]

            pdf_path = generate_invoice_pdf(
                invoice_no=invoice_no,
                invoice_date=datetime.now().strftime("%d-%b-%Y %H:%M"),
                items=pdf_items,
                subtotal=subtotal,
                discount_percent=discount_percent,
                grand_total=grand_total,
                customer_name=customer_values["name"] or None,
                customer_phone=customer_values["phone"] or None,
            )

            self.open_pdf(pdf_path)

        self.cart.clear()
        self.discount_input.setValue(0)
        self.refresh_cart_table()
        self.refresh_quick_add()
        self.search_input.clear()
        self.results_table.setRowCount(0)