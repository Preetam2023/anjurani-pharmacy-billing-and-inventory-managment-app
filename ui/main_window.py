"""
Main application window — left sidebar navigation switching between
Billing, Inventory, History, and Dashboard screens via a QStackedWidget.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel,
)
from PySide6.QtCore import Qt

from ui.styles import MAIN_STYLESHEET
from ui.billing_screen import BillingScreen
from ui.inventory_screen import InventoryScreen
from ui.history_screen import HistoryScreen
from ui.dashboard_screen import DashboardScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Medical Store Billing System")
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(MAIN_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(4)

        title = QLabel("MedStore")
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title)
        sidebar_layout.addSpacing(20)

        # --- Content area (screens) ---
        self.stack = QStackedWidget()
        self.stack.addWidget(BillingScreen())     # index 0
        self.stack.addWidget(InventoryScreen())   # index 1
        self.stack.addWidget(HistoryScreen())     # index 2
        self.stack.addWidget(DashboardScreen())   # index 3

        nav_items = [
            ("Billing", 0),
            ("Inventory", 1),
            ("History", 2),
            ("Dashboard", 3),
        ]

        self.nav_buttons = []
        for label, index in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # default arg captures the loop's current index correctly
            btn.clicked.connect(lambda checked, i=index: self.switch_screen(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack)

        self.switch_screen(0)

    def switch_screen(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
