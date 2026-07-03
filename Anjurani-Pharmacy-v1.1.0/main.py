"""
Local Medical Inventory & Billing System
Entry point.
"""

import sys
from PySide6.QtWidgets import QApplication

from db.schema import init_db
from ui.main_window import MainWindow
from logic.backup_manager import create_auto_backup
from PySide6.QtCore import QTimer
from ui.splash_screen import SplashScreen
def main():
    init_db()  # make sure tables/indexes exist before the UI opens
    from logic.startup import initialize_application
    initialize_application()

    app = QApplication(sys.argv)
    try:
        create_auto_backup()
    except Exception:
        pass
    
    splash = SplashScreen()

    splash.show()
    
    window = MainWindow()
    def start_application():

        window.showMaximized()

        splash.finish(window)


    QTimer.singleShot(
        2200,
        start_application
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
