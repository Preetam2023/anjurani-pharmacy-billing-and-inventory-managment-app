from PySide6.QtWidgets import (
    QSplashScreen,
    QLabel,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPixmap,
)

from logic.config import APP_NAME, APP_VERSION
from logic.resource_path import resource_path


class SplashScreen(QSplashScreen):

    def __init__(self):

        super().__init__()

        self.setFixedSize(500, 350)

        self.setStyleSheet("""
            QSplashScreen{
                background:white;
            }
        """)

        container = QWidget(self)
        container.setGeometry(0,0,500,350)

        layout = QVBoxLayout(container)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo

        logo = QLabel()

        pix = QPixmap(resource_path("assets/images/logo.png"))

        if not pix.isNull():

            logo.setPixmap(
                pix.scaled(
                    90,
                    90,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(logo)

        # App Name

        title = QLabel(APP_NAME)

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setFont(QFont("Segoe UI",18,QFont.Weight.Bold))

        title.setStyleSheet(
            "color:#2563eb;"
        )

        layout.addWidget(title)

        subtitle = QLabel(
            "Medical Inventory & Billing System"
        )

        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle.setStyleSheet(
            "color:#666;font-size:13px;"
        )

        layout.addWidget(subtitle)

        version = QLabel(
            f"Version {APP_VERSION}"
        )

        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version.setStyleSheet(
            "color:#888;"
        )

        layout.addWidget(version)

        layout.addSpacing(20)

        loading = QLabel(
            "Initializing Application..."
        )

        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        loading.setStyleSheet(
            "font-size:13px;color:#555;"
        )

        layout.addWidget(loading)

        layout.addStretch()

        footer = QLabel(
            "© 2026 Preetam Manna"
        )

        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        footer.setStyleSheet(
            "color:gray;font-size:11px;"
        )

        layout.addWidget(footer)

        screen = QApplication.primaryScreen()

        if screen:
            geometry = screen.geometry()
            self.move(
                geometry.center().x() - self.width() // 2,
                geometry.center().y() - self.height() // 2,
            )