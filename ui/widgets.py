"""
Small reusable custom widgets shared across screens/dialogs.
"""

from PySide6.QtWidgets import QSpinBox


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
