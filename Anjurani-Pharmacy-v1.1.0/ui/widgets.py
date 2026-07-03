"""
Small reusable custom widgets shared across screens/dialogs.
"""

from PySide6.QtWidgets import QSpinBox, QLineEdit
from PySide6.QtCore import Qt

class SelectAllSpinBox(QSpinBox):
    """
    A QSpinBox that selects all its text when it gains keyboard focus.

    Without this, clicking into a spinbox that already shows a value and
    then typing can leave the cursor in an unexpected spot partway through
    the old text — e.g. clicking into a box showing "1" and typing "25"
    can land as "125" or "215" instead of cleanly becoming "25". Selecting
    all text on focus means the very next keystroke always starts clean.
    """

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()

class ExpiryLineEdit(QLineEdit):
    """
    Smart expiry input.

    User types:
        0328

    Automatically becomes:
        03/28
    """

    def __init__(self):
        super().__init__()

        self.setPlaceholderText("MM/YY")
        self.setMaxLength(5)

        self.textEdited.connect(self._format_text)

    def _format_text(self, text):
        digits = "".join(ch for ch in text if ch.isdigit())

        if len(digits) > 4:
            digits = digits[:4]

        if len(digits) <= 2:
            formatted = digits
        else:
            formatted = digits[:2] + "/" + digits[2:]

        self.blockSignals(True)
        self.setText(formatted)
        self.blockSignals(False)

        self.setCursorPosition(len(formatted))

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()