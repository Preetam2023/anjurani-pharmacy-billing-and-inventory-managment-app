from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QRadioButton,
    QPushButton,
    QMessageBox,
)

from logic.app_settings import (
    get_invoice_layout,
    set_invoice_layout,
)


class PrintLayoutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Print Layout")
        self.setFixedSize(450, 300)

        layout = QVBoxLayout(self)

        title = QLabel("Invoice Print Layout")

        title.setStyleSheet("""
            font-size:20px;
            font-weight:bold;
        """)

        layout.addWidget(title)

        subtitle = QLabel(
            "Choose which invoice format should be used while printing."
        )

        subtitle.setStyleSheet("""
            color:gray;
        """)

        layout.addWidget(subtitle)

        layout.addSpacing(20)

        self.modern_radio = QRadioButton(
            "Modern Layout"
        )

        self.preprinted_radio = QRadioButton(
            "Pre-Printed Paper Layout"
        )

        layout.addWidget(self.modern_radio)
        layout.addWidget(self.preprinted_radio)

        layout.addStretch()

        self.save_btn = QPushButton("Save")
        layout.addWidget(self.save_btn)

        current = get_invoice_layout()

        if current == "preprinted":
            self.preprinted_radio.setChecked(True)
        else:
            self.modern_radio.setChecked(True)

        self.save_btn.clicked.connect(self.save_layout)

    def save_layout(self):

        if self.modern_radio.isChecked():
            set_invoice_layout("modern")
        else:
            set_invoice_layout("preprinted")

        QMessageBox.information(
            self,
            "Saved",
            "Print layout updated successfully."
        )

        self.accept()