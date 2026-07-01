import os
import shutil
import sqlite3
from datetime import datetime
import platform
import subprocess
from db.connection import close_connection
from logic.backup_metadata import create_backup_metadata
# ----------------------------------------------------
# Project Paths
# ----------------------------------------------------

from logic.config import (
    DATABASE_PATH,
    BACKUP_DIR,
)


# ----------------------------------------------------
# Folder Setup
# ----------------------------------------------------

def ensure_backup_folder():
    """
    Create backup folder if it does not already exist.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)


# ----------------------------------------------------
# Create Backup
# ----------------------------------------------------

def backup_database():

    ensure_backup_folder()

    if not os.path.exists(DATABASE_PATH):
        raise FileNotFoundError("Database file not found.")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    backup_name = f"MANUAL_{timestamp}.db"

    backup_path = os.path.join(BACKUP_DIR, backup_name)

    shutil.copy2(DATABASE_PATH, backup_path)
    # Verify backup
    if not validate_database(backup_path):
        try:
            os.remove(backup_path)
        except Exception:
            pass

        raise Exception(
        "Backup verification failed. Backup was not created."
        )
    create_backup_metadata(
        backup_path,
        "MANUAL"
    )

    return backup_path

def create_auto_backup():
    """
    Creates one automatic backup per day.
    """

    ensure_backup_folder()

    today = datetime.now().strftime("%Y-%m-%d")

    # Check if today's AUTO backup already exists
    for file in os.listdir(BACKUP_DIR):

        if file.startswith("AUTO_") and today in file:
            return None

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    backup_name = f"AUTO_{timestamp}.db"

    backup_path = os.path.join(BACKUP_DIR, backup_name)

    shutil.copy2(DATABASE_PATH, backup_path)
# Verify backup
    if not validate_database(backup_path):
        try:
            os.remove(backup_path)
        except Exception:
            pass

        raise Exception(
            "Backup verification failed. Backup was not created."
        )
    cleanup_auto_backups()
    create_backup_metadata(
        backup_path,
        "AUTO"
    )
    return backup_path

def create_emergency_backup():
    """
    Creates an emergency backup before restoring another database.
    """

    ensure_backup_folder()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    backup_name = f"EMERGENCY_{timestamp}.db"

    backup_path = os.path.join(BACKUP_DIR, backup_name)

    shutil.copy2(DATABASE_PATH, backup_path)
# Verify backup
    if not validate_database(backup_path):
        try:
            os.remove(backup_path)
        except Exception:
            pass

        raise Exception(
            "Backup verification failed. Backup was not created."
        )
    create_backup_metadata(
        backup_path,
        "EMERGENCY"
    )
    return backup_path
# ----------------------------------------------------
# List Available Backups
# ----------------------------------------------------

def get_available_backups():

    ensure_backup_folder()

    backups = []

    for file in os.listdir(BACKUP_DIR):

        if file.endswith(".db"):

            full_path = os.path.join(BACKUP_DIR, file)

            # Try to read date from filename
            try:
                timestamp_str = file.replace(".db", "")

                if timestamp_str.startswith("MANUAL_"):
                    timestamp_str = timestamp_str.replace("MANUAL_", "")

                elif timestamp_str.startswith("AUTO_"):
                    timestamp_str = timestamp_str.replace("AUTO_", "")

                elif timestamp_str.startswith("EMERGENCY_"):
                    timestamp_str = timestamp_str.replace("EMERGENCY_", "")

                created = datetime.strptime(
                timestamp_str,
                "%Y-%m-%d_%H-%M-%S"
                )

            except Exception:
                created = datetime.fromtimestamp(os.path.getmtime(full_path))

            backups.append(
                {
                    "name": file,
                    "path": full_path,
                    "created": created,
                    "size": os.path.getsize(full_path),
                }
            )

    backups.sort(
        key=lambda x: x["created"],
        reverse=True
    )

    return backups


# ----------------------------------------------------
# Validate SQLite Backup
# ----------------------------------------------------

def validate_database(db_path):

    if not os.path.exists(db_path):
        return False

    try:

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )

        tables = [row[0] for row in cursor.fetchall()]

        required = [
            "medicines",
            "invoices",
            "invoice_items"
        ]

        for table in required:

            if table not in tables:

                conn.close()

                return False

        conn.close()

        return True

    except Exception:

        return False
    
def open_backup_folder():
    """
    Open the backup folder in the system's file explorer.
    """

    ensure_backup_folder()

    system = platform.system()

    if system == "Windows":
        os.startfile(BACKUP_DIR)

    elif system == "Darwin":
        subprocess.Popen(["open", BACKUP_DIR])

    else:
        subprocess.Popen(["xdg-open", BACKUP_DIR])
        
def restore_database(backup_path):
    """
    Restore the selected backup database safely.
    """

    if not validate_database(backup_path):
        raise Exception("Invalid backup database.")

    # Emergency backup first
    create_emergency_backup()

    # Close current SQLite connection
    close_connection()

    # Remove WAL/SHM files if they exist
    for ext in ("-wal", "-shm"):
        extra = DATABASE_PATH + ext
        if os.path.exists(extra):
            try:
                os.remove(extra)
            except Exception:
                pass

    # Replace database
    shutil.copy2(backup_path, DATABASE_PATH)
    if not validate_database(DATABASE_PATH):
        raise Exception(
            "Database restore verification failed."
    )
    return True

def delete_backup(backup_path):
    """
    Delete a selected backup file.
    """

    if not os.path.exists(backup_path):
        raise FileNotFoundError("Backup file not found.")
    json_path = backup_path.replace(".db", ".json")

    if os.path.exists(json_path):
        os.remove(json_path)


    os.remove(backup_path)

    return True

def cleanup_auto_backups(keep=30):
    """
    Keep only the latest automatic backups.
    """

    ensure_backup_folder()

    auto_backups = []

    for file in os.listdir(BACKUP_DIR):

        if file.startswith("AUTO_") and file.endswith(".db"):

            path = os.path.join(BACKUP_DIR, file)

            auto_backups.append(
                (
                    os.path.getmtime(path),
                    path
                )
            )

    auto_backups.sort(reverse=True)

    for _, path in auto_backups[keep:]:

        try:
            json_path = path.replace(".db", ".json")

            if os.path.exists(json_path):
                os.remove(json_path)
            os.remove(path)
        except Exception:
            pass