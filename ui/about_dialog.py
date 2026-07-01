from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from logic.config import APP_NAME, APP_VERSION
from logic.resource_path import resource_path


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About")
        self.setFixedSize(420, 500)

        layout = QVBoxLayout(self)

        layout.setSpacing(12)

        # Logo
        logo = QLabel()

        pixmap = QPixmap(resource_path("assets/images/logo.png"))

        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    90,
                    90,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

        logo.setAlignment(Qt.AlignCenter)

        layout.addWidget(logo)

        # App Name
        title = QLabel(APP_NAME)

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            color:#1e3a8a;
        """)

        layout.addWidget(title)

        subtitle = QLabel("Medical Inventory & Billing System")

        subtitle.setAlignment(Qt.AlignCenter)

        subtitle.setStyleSheet("""
            color:gray;
            font-size:13px;
        """)

        layout.addWidget(subtitle)

        layout.addSpacing(10)

        info = QLabel(
            f"""
Version : {APP_VERSION}

Designed & Developed By

Preetam Manna (+91 9093954811)

© 2026 All Rights Reserved

"""
        )

        info.setAlignment(Qt.AlignCenter)

        info.setStyleSheet("""
            font-size:13px;
            line-height:180%;
        """)

        layout.addWidget(info)

        layout.addStretch()

        ok_btn = QPushButton("OK")

        ok_btn.clicked.connect(self.accept)

        layout.addWidget(ok_btn)