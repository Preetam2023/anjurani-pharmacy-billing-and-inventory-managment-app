from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QMessageBox,
)

from logic.backup_manager import (
    backup_database,
    get_available_backups,
    open_backup_folder,
    restore_database,
    delete_backup,

)
from logic.backup_metadata import read_backup_metadata
from PySide6.QtWidgets import QListWidgetItem
class BackupManagerDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Backup Manager")
        self.resize(980, 650)

        self.setup_ui()

        self.load_backups()

    # -------------------------------------------------

    def setup_ui(self):

        layout = QVBoxLayout(self)

        title = QLabel("Database Backup Manager")
        title.setStyleSheet("""
            font-size:20px;
            font-weight:bold;
        """)

        layout.addWidget(title)

        subtitle = QLabel(
            "Manage database backups safely."
        )

        subtitle.setStyleSheet("color:gray;")

        layout.addWidget(subtitle)

        layout.addSpacing(15)

        button_layout = QHBoxLayout()

        self.backup_btn = QPushButton("Backup Now")
        self.restore_btn = QPushButton("Restore Backup")
        self.open_btn = QPushButton("Open Backup Folder")
        self.delete_btn = QPushButton("Delete Backup")

        button_layout.addWidget(self.backup_btn)
        button_layout.addWidget(self.restore_btn)
        button_layout.addWidget(self.open_btn)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)

        layout.addSpacing(20)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(8)
        content_layout = QHBoxLayout()

        content_layout.addWidget(self.list_widget, 2)

        self.details_label = QLabel()

        self.details_label.setStyleSheet("""
        QLabel{
    border:1px solid lightgray;
    border-radius:8px;
    padding:12px;
    background:white;
}
""")

        self.details_label.setMinimumWidth(260)
        self.details_label.setWordWrap(True)

        content_layout.addWidget(self.details_label,1)

        layout.addLayout(content_layout)

        layout.addSpacing(15)

        self.info_label = QLabel()

        layout.addWidget(self.info_label)

        layout.addStretch()

        self.close_btn = QPushButton("Close")

        layout.addWidget(self.close_btn)

        # Signals

        self.close_btn.clicked.connect(self.close)
        self.backup_btn.clicked.connect(self.create_backup)
        self.open_btn.clicked.connect(open_backup_folder)
        self.restore_btn.clicked.connect(self.restore_selected_backup)
        self.delete_btn.clicked.connect(self.delete_selected_backup)
        self.restore_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        self.list_widget.itemSelectionChanged.connect(
            self.update_button_state
        )
        self.list_widget.itemSelectionChanged.connect(
            self.show_backup_details
)
    # -------------------------------------------------

    def load_backups(self):

        self.list_widget.clear()
        self.details_label.setText(
            "Select a backup to view details."
        )

        backups = get_available_backups()

        if not backups:

            self.info_label.setText("No backups available.")

            return

        for backup in backups:

            date = backup["created"].strftime("%d %b %Y")
            time = backup["created"].strftime("%I:%M %p")

            size = backup["size"] / 1024

            name = backup["name"]

            if name.startswith("MANUAL_"):
                icon = "🟢"
                title = "Manual Backup"

            elif name.startswith("AUTO_"):
                icon = "🔵"
                title = "Automatic Backup"

            else:
                icon = "🔴"
                title = "Emergency Backup"

            text = (
            f"{icon} {title}\n\n"
    f"{date}      {time}       {size:.1f} KB\n\n"
    f"{name}"
)

            item = QListWidgetItem(text)

            self.list_widget.addItem(item)
        self.info_label.setText(
            f"Total Backups : {len(backups)}"
        )

    # -------------------------------------------------

    def update_button_state(self):
        """
    Enable Restore/Delete only when a backup is selected.
    """

        selected = self.list_widget.currentRow() >= 0

        self.restore_btn.setEnabled(selected)
        self.delete_btn.setEnabled(selected)
    
    def create_backup(self):

        try:

            backup_database()

            QMessageBox.information(
                self,
                "Success",
                "Database backup created successfully."
            )

            self.load_backups()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )
    
    def restore_selected_backup(self):

        current = self.list_widget.currentRow()

        if current < 0:

            QMessageBox.warning(
            self,
            "Restore Backup",
            "Please select a backup."
            )

            return

        backups = get_available_backups()

        backup = backups[current]

        answer = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Restore backup:\n\n{backup['name']}?\n\n"
            "An emergency backup of the current database will be created automatically."
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            restore_database(backup["path"])

            QMessageBox.information(
            self,
            "Restore Successful",
            "Database restored successfully.\n\nPlease restart the application."
            )

        except Exception as e:

            QMessageBox.critical(
            self,
            "Restore Failed",
            str(e)
            )
    
    def delete_selected_backup(self):

        current = self.list_widget.currentRow()

        if current < 0:
            QMessageBox.warning(
            self,
            "Delete Backup",
            "Please select a backup."
        )
            return

        backups = get_available_backups()

        backup = backups[current]

    # Never allow deleting emergency backups
        if backup["name"].startswith("EMERGENCY_"):

            QMessageBox.information(
            self,
            "Protected Backup",
            "Emergency backups cannot be deleted."
        )

            return

        reply = QMessageBox.question(
            self,
            "Delete Backup",
            f"Delete\n\n{backup['name']} ?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:

            delete_backup(backup["path"])

            QMessageBox.information(
            self,
            "Deleted",
            "Backup deleted successfully."
        )

            self.load_backups()

        except Exception as e:

            QMessageBox.critical(
            self,
            "Error",
            str(e)
        )
            
    def show_backup_details(self):

        current = self.list_widget.currentRow()

        if current < 0:

            self.details_label.setText(
                "Select a backup to view details."
        )

            return

        backups = get_available_backups()

        metadata = read_backup_metadata(
            backups[current]["path"]
    )

        if metadata is None:

            self.details_label.setText(
                "Metadata not available."
        )

            return

        self.details_label.setText(
    f"""
<h3> Backup Details</h3>

<b>Type</b><br>
{metadata.get("backup_type", "Unknown")}<br><br>

<b>Created</b><br>
{metadata.get("created_at", "Unknown")}<br><br>

<b>Medicines</b><br>
{metadata.get("medicine_count", 0)}<br><br>

<b>Invoices</b><br>
{metadata.get("invoice_count", 0)}<br><br>

<b>Inventory Value</b><br>
₹ {metadata.get("inventory_value", 0):,.2f}<br><br>

<b>Database Size</b><br>
{metadata.get("database_size_mb", 0)} MB<br><br>

<b>Application</b><br>
{metadata.get("application", "Unknown")}<br><br>

<b>Version</b><br>
{metadata.get("version", "Unknown")}<br><br>

<b>Status</b><br>
🟢 Valid Backup
"""
)