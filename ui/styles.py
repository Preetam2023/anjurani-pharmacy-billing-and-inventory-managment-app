"""
Central stylesheet for the app. Keeping this in one file means we can
adjust the look (colors, spacing) in one place as the UI grows.
"""

MAIN_STYLESHEET = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}

#sidebar {
    background-color: #1e2a38;
}

#sidebarTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: 600;
    padding: 10px 0;
}

QStackedWidget {
    background-color: #f5f7fa;
}

QLabel#screenTitle {
    font-size: 28px;
    font-weight: 700;
    color: #1e2a38;
}

QLabel#screenNote {
    font-size: 14px;
    color: #6b7785;
    margin-top: 8px;
}

QPushButton {
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2563eb;
}

QPushButton:disabled {
    background-color: #cbd5e1;
    color: #64748b;
}

QPushButton#navButton {
    background-color: transparent;
    border-radius: 0px;
    color: #b8c2cc;
    text-align: left;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: normal;
}

QPushButton#navButton:hover {
    background-color: #2a3a4d;
    color: #ffffff;
}

QPushButton#navButton:checked {
    background-color: #3b82f6;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#dangerButton {
    background-color: #ef4444;
    color: white;
    border-radius: 4px;
    padding: 4px 10px;
    font-weight: 500;
    font-size: 12px;
}

QPushButton#dangerButton:hover {
    background-color: #dc2626;
}

QPushButton#quickAddChip {
    background-color: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton#quickAddChip:hover {
    background-color: #dbeafe;
}

QFrame#dashboardCard {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}

QLabel#cardLabel {
    color: #6b7785;
    font-size: 13px;
    font-weight: 500;
}

QLabel#cardValue {
    color: #1e2a38;
    font-size: 28px;
    font-weight: 700;
}

QTableWidget {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #eef2f6;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: 600;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background-color: #dbeafe;
    color: #1e293b;
}
"""
