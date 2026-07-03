"""
Inventory Management screen — add, edit, add stock, and delete medicines.
"""

from datetime import datetime, date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from db import queries
from ui.medicine_form_dialog import MedicineFormDialog
from ui.add_stock_dialog import AddStockDialog
from ui.stock_history_dialog import StockHistoryDialog


class NumericTableWidgetItem(QTableWidgetItem):
    """
    A table item that sorts by a numeric/comparable value stored in
    UserRole instead of comparing the displayed text. Without this,
    sorting "Stock" or "Price" would compare strings like "12" vs "8"
    alphabetically, which gives the wrong order.
    """

    def __lt__(self, other):
        self_value = self.data(Qt.ItemDataRole.UserRole)
        other_value = other.data(Qt.ItemDataRole.UserRole)
        if self_value is None or other_value is None:
            return super().__lt__(other)
        return self_value < other_value


class InventoryScreen(QWidget):
    COLUMNS = ["Name", "Batch No", "Expiry Date", "Price", "Stock", "Seller"]
    SEARCH_DEBOUNCE_MS = 250
    LOW_STOCK_THRESHOLD = 20
    EXPIRY_WARNING_DAYS = 90

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Inventory")
        title.setObjectName("screenTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self.add_btn = QPushButton("Add Medicine")
        self.add_btn.clicked.connect(self.handle_add)
        header_row.addWidget(self.add_btn)

        self.add_stock_btn = QPushButton("Add Stock")
        self.add_stock_btn.clicked.connect(self.handle_add_stock)
        header_row.addWidget(self.add_stock_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.handle_edit)
        header_row.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.handle_delete)
        header_row.addWidget(self.delete_btn)

        self.history_btn = QPushButton("Stock History")
        self.history_btn.clicked.connect(self.handle_stock_history)
        header_row.addWidget(self.history_btn)

        layout.addLayout(header_row)

        legend = QLabel(
    "<span style='color:#dc2626; font-size:16px;'>●</span> <span style='font-size:15px;'>Expired</span>"
    "&nbsp;&nbsp;&nbsp;&nbsp;"
    "<span style='color:#f59e0b; font-size:16px;'>●</span> <span style='font-size:15px;'>Expiring within 90 days</span>"
    "&nbsp;&nbsp;&nbsp;&nbsp;"
    "<span style='color:#dc2626; font-size:15px;'>Stock value in red = Low Stock (&lt;20)</span>"
)

        legend.setStyleSheet("""
QLabel{
    color:#4b5563;
    padding:4px 0px;
}
""")
        layout.addWidget(legend)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by medicine name or batch number...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        layout.addWidget(self.search_input)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.load_data)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.itemSelectionChanged.connect(self.update_button_states)

        layout.addWidget(self.table)

        self.update_button_states()
        self.load_data()

    def showEvent(self, event):
        """Refresh data every time this screen becomes visible — otherwise
        stock changes made elsewhere (e.g. a sale on the Billing screen)
        wouldn't show up here until some other action forced a reload."""
        super().showEvent(event)
        self.load_data()

    def on_search_text_changed(self):
        # restart the timer on every keystroke — only the last pause fires a reload
        self.search_timer.start(self.SEARCH_DEBOUNCE_MS)

    # ---------- Data loading ----------

    def load_data(self):
        self.table.setSortingEnabled(False)
        query = self.search_input.text().strip()
        medicines = queries.search_medicines(query) if query else queries.get_all_medicines()
        self.table.setRowCount(len(medicines))

        for row_index, med in enumerate(medicines):
            name_item = QTableWidgetItem(med["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, med["id"])
            self.table.setItem(row_index, 0, name_item)

            self.table.setItem(row_index, 1, QTableWidgetItem(med["batch_no"]))

            expiry_item = NumericTableWidgetItem(self.format_date(med["expiry_date"]))
            expiry_item.setData(Qt.ItemDataRole.UserRole, med["expiry_date"] or "")
            self.table.setItem(row_index, 2, expiry_item)

            price_item = NumericTableWidgetItem(f"₹{med['price']:.2f}")
            price_item.setData(Qt.ItemDataRole.UserRole, med["price"])
            self.table.setItem(row_index, 3, price_item)

            stock_item = NumericTableWidgetItem(str(med["stock"]))
            stock_item.setData(Qt.ItemDataRole.UserRole, med["stock"])
            if med["stock"] < self.LOW_STOCK_THRESHOLD:
                stock_item.setForeground(QColor("#dc2626"))
                font = stock_item.font()
                font.setBold(True)
                stock_item.setFont(font)
            self.table.setItem(row_index, 4, stock_item)

            self.table.setItem(row_index, 5, QTableWidgetItem(med["seller_name"] or "—"))

            # Row-level expiry highlight: expired = red tint, expiring
            # soon = yellow tint, otherwise leave the default background.
            row_color = self.get_expiry_row_color(med["expiry_date"])
            if row_color is not None:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row_index, col)
                    if item is not None:
                        item.setBackground(row_color)

        self.table.setSortingEnabled(True)
        self.update_button_states()

    def get_expiry_row_color(self, iso_expiry_date):
        if not iso_expiry_date:
            return None
        try:
            expiry = datetime.strptime(iso_expiry_date, "%Y-%m-%d").date()
        except ValueError:
            return None
        days_left = (expiry - date.today()).days
        if days_left < 0:
            return QColor("#fee2e2")  # expired — light red
        if days_left <= self.EXPIRY_WARNING_DAYS:
            return QColor("#fef9c3")  # expiring soon — light yellow
        return None

    @staticmethod
    def format_date(iso_date):
        if not iso_date:
            return "—"
        try:
            return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%b-%Y")
        except ValueError:
            return iso_date

    # ---------- Selection helpers ----------

    def get_selected_medicine(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        medicine_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return queries.get_medicine_by_id(medicine_id)

    def update_button_states(self):
        medicine = self.get_selected_medicine()
        has_selection = medicine is not None
        self.edit_btn.setEnabled(has_selection)
        self.add_stock_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    # ---------- Actions ----------

    def handle_add(self):
        dialog = MedicineFormDialog(self)
        if dialog.exec():
            values = dialog.get_values()
            queries.add_medicine(
                values["name"], values["batch_no"], values["expiry_date"],
                values["packet_price"], values["stock"], values["seller_name"],
                packets=values.get("packets"), units_per_packet=values.get("units_per_packet"),
            )
            self.load_data()

    def handle_edit(self):
        medicine = self.get_selected_medicine()
        if medicine is None:
            return
        dialog = MedicineFormDialog(self, medicine=medicine)
        if dialog.exec():
            values = dialog.get_values()
            queries.update_medicine(
                medicine["id"], name=values["name"], batch_no=values["batch_no"],
                expiry_date=values["expiry_date"], packet_price=values["packet_price"],stock=values["stock"],
                seller_name=values["seller_name"],
            )
            self.load_data()

    def handle_add_stock(self):
        medicine = self.get_selected_medicine()
        if medicine is None:
            return
        dialog = AddStockDialog(self, medicine=medicine)
        if dialog.exec():
            queries.add_stock(
    medicine["id"],
    dialog.get_quantity(),
    packet_price=dialog.get_packet_price(),
    seller_name=dialog.get_seller_name(),
    batch_no=medicine["batch_no"],
    packets=dialog.get_packets(),
    units_per_packet=dialog.get_units_per_packet(),
)
            self.load_data()

    def handle_stock_history(self):
        dialog = StockHistoryDialog(self)
        dialog.exec()

    def handle_delete(self):
        medicine = self.get_selected_medicine()
        if medicine is None:
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{medicine['name']}' (batch {medicine['batch_no']})?\nThis cannot be undone.",
        )
        if confirm == QMessageBox.StandardButton.Yes:
            deleted = queries.delete_medicine(medicine["id"])

            if deleted:
                self.load_data()
            else:
                QMessageBox.warning(
                    self,
        "Cannot Delete",
        "This medicine has already been used in invoices or stock history.\n\n"
        "For audit purposes it cannot be deleted."
        "Only medicines that have never been sold can be removed."

    )
