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

#sidebarSubtitle{

color:#b7c5d4;

font-size:13px;

padding-bottom:20px;

}

#sidebarTitle
{
    color: white;
    font-size: 24px;
    font-weight: 800;
    font-family: "Segoe UI";
    letter-spacing: 1px;
}

#sidebarSubtitle
{
    color: #DCE6F2;
    font-size: 24px;
    font-weight: 800;
    font-family: "Segoe UI";
    letter-spacing: 1px;
    margin-top: -8px;
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

QPushButton#navButton{

background:transparent;

border-radius:10px;

margin:4px 10px;

padding:12px 16px;

text-align:left;

font-size:14px;

font-weight:600;

color:#cbd5e1;

}

QPushButton#navButton:hover{

background:#31455c;

color:white;

}

QPushButton#navButton:checked{

background:#2563eb;

color:white;

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

QToolButton{

background:transparent;

color:#cbd5e1;

padding:12px;

border-radius:10px;

margin:10px;

text-align:left;

font-size:14px;

font-weight:600;

}

QToolButton:hover{

background:#31455c;

color:white;

}
"""
