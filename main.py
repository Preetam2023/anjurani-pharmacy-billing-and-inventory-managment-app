"""
Local Medical Inventory & Billing System
Entry point.
"""

import sys
from PySide6.QtWidgets import QApplication

from db.schema import init_db
from ui.main_window import MainWindow


def main():
    init_db()  # make sure tables/indexes exist before the UI opens

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
