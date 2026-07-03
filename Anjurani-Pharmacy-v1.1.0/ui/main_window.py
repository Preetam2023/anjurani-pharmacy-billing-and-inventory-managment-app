"""
Main application window — left sidebar navigation switching between
Billing, Inventory, History, and Dashboard screens via a QStackedWidget.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel,QMessageBox,QToolButton, QMenu, QStyle,

)
from PySide6.QtCore import Qt, QSize

from ui.styles import MAIN_STYLESHEET
from ui.billing_screen import BillingScreen
from ui.inventory_screen import InventoryScreen
from ui.history_screen import HistoryScreen
from ui.dashboard_screen import DashboardScreen
from PySide6.QtGui import QAction, QPixmap, QIcon

from logic.backup_manager import backup_database
from ui.backup_manager_dialog import BackupManagerDialog
from ui.about_dialog import AboutDialog
from logic.resource_path import resource_path
# import time
from ui.print_layout_dialog import PrintLayoutDialog
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anjurani Pharmacy")
        self.setWindowIcon(QIcon(resource_path("assets/images/logo.ico")))
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(MAIN_STYLESHEET)
        # self._create_menu()
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

        logo = QLabel()

        pixmap = QPixmap(resource_path("assets/images/logo_bg.png"))

        logo.setPixmap(
        pixmap.scaled(
        70,
        70,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
)

        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(8)


        title = QLabel("""
<div align="center">
<span style="
font-size:24px;
font-weight:800;
color:white;
font-family:'Segoe UI';
letter-spacing:1px;
">
ANJURANI
</span><br>

<span style="
font-size:24px;
font-weight:800;
color:#DCE6F2;
font-family:'Segoe UI';
letter-spacing:1px;
">
PHARMACY
</span>
</div>
""")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sidebar_layout.addWidget(title)

        sidebar_layout.addSpacing(25)

        # --- Content area (screens) ---
        self.stack = QStackedWidget()
        self.stack.addWidget(BillingScreen())     # index 0
        self.stack.addWidget(InventoryScreen())   # index 1
        self.stack.addWidget(HistoryScreen())     # index 2
        self.stack.addWidget(DashboardScreen())   # index 3

        nav_items = [
    (
        "Dashboard",
        self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon),
        3,
    ),
    (
        "Billing",
        self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView),
        0,
    ),
    (
        "Inventory",
        self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon),
        1,
    ),
    (
        "History",
        self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView),
        2,
    ),
]

        self.nav_buttons = {}
        for label, icon, index in nav_items:

            btn = QPushButton(label)

            btn.setIcon(icon)

            btn.setIconSize(QSize(20,20))

            btn.setObjectName("navButton")

            btn.setCheckable(True)

            btn.clicked.connect(
                lambda checked,i=index:
                self.switch_screen(i)
            )

            sidebar_layout.addWidget(btn)

            self.nav_buttons[index] = btn

        sidebar_layout.addStretch()
        
        settings_btn = QToolButton()

        settings_btn.setText("Settings")

        settings_btn.setPopupMode(
    QToolButton.ToolButtonPopupMode.InstantPopup
)

        settings_btn.setToolButtonStyle(
    Qt.ToolButtonStyle.ToolButtonTextBesideIcon
)

        settings_btn.setIcon(
    self.style().standardIcon(
        QStyle.StandardPixmap.SP_FileDialogDetailedView
    )
)

        menu = QMenu(settings_btn)

        backup_action = menu.addAction("Backup Manager")

        backup_action.triggered.connect(
    self.open_backup_manager
)
        about_action = menu.addAction("About")
        about_action.triggered.connect(
        self.open_about_dialog
)
        layout_action = menu.addAction(
    "Print Layout"
)

        layout_action.triggered.connect(
    self.open_print_layout_dialog
)

        menu.addSeparator()

        exit_action = menu.addAction("Exit")

        exit_action.triggered.connect(
    self.close
)

        settings_btn.setMenu(menu)

        sidebar_layout.addWidget(settings_btn)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack)

        self.switch_screen(0)

    def switch_screen(self, index):
        # t0 = time.perf_counter()

        # print(f"\nSwitching to screen {index}")

        self.stack.setCurrentIndex(index)

        # t1 = time.perf_counter()

        # print(f"QStackedWidget switch: {t1 - t0:.4f} sec")

        for stack_index, button in self.nav_buttons.items():
            button.setChecked(stack_index == index)

        # t2 = time.perf_counter()

        # print(f"Buttons update: {t2 - t1:.4f} sec")
        # print(f"Total switch: {t2 - t0:.4f} sec\n")
    # def _create_menu(self):
    #     """
    #     Create application menu bar.
    #     """

    #     menu = self.menuBar()

    #     file_menu = menu.addMenu("File")

    #     backup_action = QAction("Backup Database", self)
    #     backup_action.triggered.connect(self.open_backup_manager)

    #     exit_action = QAction("Exit", self)
    #     exit_action.triggered.connect(self.close)

    #     file_menu.addAction(backup_action)
    #     file_menu.addSeparator()
    #     file_menu.addAction(exit_action)


    def open_backup_manager(self):

        dialog = BackupManagerDialog(self)

        dialog.exec()
        
    def open_about_dialog(self):

        dialog = AboutDialog(self)

        dialog.exec()
        
    def open_print_layout_dialog(self):
        PrintLayoutDialog(self).exec()