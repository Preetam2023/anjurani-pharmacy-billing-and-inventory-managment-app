"""
Dashboard screen — at-a-glance summary of today's business activity,
plus low-stock and expiry alerts so nothing gets missed.
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QListWidget, QListWidgetItem,
)
from PySide6.QtGui import QColor

from db import queries

LOW_STOCK_THRESHOLD = 20
EXPIRY_WARNING_DAYS = 90


class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("screenTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        self.date_label = QLabel("")
        self.date_label.setStyleSheet("color: #6b7785; font-size: 13px;")
        layout.addWidget(self.date_label)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        self.sales_card, self.sales_value_label = self.build_card("Today's Sales", "₹0.00")
        self.bills_card, self.bills_value_label = self.build_card("Bills Generated", "0")
        self.items_card, self.items_value_label = self.build_card("Items Sold Today", "0")
        self.inventory_card, self.inventory_value_label = self.build_card("Inventory Value", "₹0.00")
        self.low_stock_card, self.low_stock_value_label = self.build_card("Low Stock Items", "0")
        self.expiry_card, self.expiry_value_label = self.build_card("Expiry Alerts", "0")

        grid.addWidget(self.sales_card, 0, 0)
        grid.addWidget(self.bills_card, 0, 1)
        grid.addWidget(self.items_card, 0, 2)
        grid.addWidget(self.inventory_card, 1, 0)
        grid.addWidget(self.low_stock_card, 1, 1)
        grid.addWidget(self.expiry_card, 1, 2)

        layout.addLayout(grid)

        alerts_row = QHBoxLayout()
        alerts_row.addWidget(self.build_alert_panel("Low Stock (below 20)", "low_stock_list"))
        alerts_row.addWidget(self.build_alert_panel("Expiry Alerts (expired or within 90 days)", "expiry_list"))
        layout.addLayout(alerts_row)

        self.load_data()

    def showEvent(self, event):
        # Refresh every time the Dashboard becomes visible, so it always
        # reflects sales/stock changes made on other screens.
        super().showEvent(event)
        self.load_data()

    def build_card(self, label_text, initial_value):
        card = QFrame()
        card.setObjectName("dashboardCard")
        card.setMinimumHeight(110)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)

        label = QLabel(label_text)
        label.setObjectName("cardLabel")
        card_layout.addWidget(label)

        value = QLabel(initial_value)
        value.setObjectName("cardValue")
        card_layout.addWidget(value)

        card_layout.addStretch()
        return card, value

    def build_alert_panel(self, title_text, list_attr_name):
        panel = QFrame()
        panel.setObjectName("dashboardCard")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 14, 16, 14)

        title = QLabel(title_text)
        title.setStyleSheet("font-weight: 600; font-size: 13px; color: #1e2a38;")
        panel_layout.addWidget(title)

        list_widget = QListWidget()
        list_widget.setMinimumHeight(160)
        list_widget.setStyleSheet("border: none;")
        panel_layout.addWidget(list_widget)
        setattr(self, list_attr_name, list_widget)

        return panel

    def load_data(self):
        summary = queries.get_today_summary()

        self.sales_value_label.setText(f"₹{summary['sales_today']:.2f}")
        self.bills_value_label.setText(str(summary["bills_today"]))
        self.items_value_label.setText(str(summary["items_sold_today"]))
        self.inventory_value_label.setText(f"₹{summary['inventory_value']:.2f}")

        self.date_label.setText(datetime.now().strftime("%A, %d %B %Y"))

        self.load_low_stock_alerts()
        self.load_expiry_alerts()

    def load_low_stock_alerts(self):
        low_stock_items = queries.get_low_stock(LOW_STOCK_THRESHOLD)
        self.low_stock_value_label.setText(str(len(low_stock_items)))
        self.low_stock_value_label.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #dc2626;" if low_stock_items
            else "font-size: 28px; font-weight: 700; color: #1e2a38;"
        )

        self.low_stock_list.clear()
        if not low_stock_items:
            self.low_stock_list.addItem("No low stock items right now.")
            return
        for med in low_stock_items:
            item = QListWidgetItem(f"{med['name']}  —  {med['stock']} left")
            item.setForeground(QColor("#dc2626"))
            self.low_stock_list.addItem(item)

    def load_expiry_alerts(self):
        expired_items = queries.get_expired()
        expiring_items = queries.get_expiring_soon(EXPIRY_WARNING_DAYS)
        total_alerts = len(expired_items) + len(expiring_items)

        self.expiry_value_label.setText(str(total_alerts))
        self.expiry_value_label.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #dc2626;" if total_alerts
            else "font-size: 28px; font-weight: 700; color: #1e2a38;"
        )

        self.expiry_list.clear()
        if not total_alerts:
            self.expiry_list.addItem("No expiry alerts right now.")
            return
        for med in expired_items:
            item = QListWidgetItem(f"{med['name']}  —  expired {self.format_date(med['expiry_date'])}")
            item.setForeground(QColor("#dc2626"))
            self.expiry_list.addItem(item)
        for med in expiring_items:
            item = QListWidgetItem(f"{med['name']}  —  expires {self.format_date(med['expiry_date'])}")
            item.setForeground(QColor("#ca8a04"))
            self.expiry_list.addItem(item)

    @staticmethod
    def format_date(iso_date):
        if not iso_date:
            return "—"
        try:
            return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d-%b-%Y")
        except ValueError:
            return iso_date
