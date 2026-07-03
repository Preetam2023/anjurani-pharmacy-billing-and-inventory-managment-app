import json
import os
import sqlite3
from datetime import datetime

from logic.config import APP_NAME, APP_VERSION


def get_database_statistics(database_path):
    """
    Read simple statistics from a backup database.
    """

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Medicine Count
    cursor.execute("SELECT COUNT(*) FROM medicines")
    medicine_count = cursor.fetchone()[0]

    # Invoice Count
    cursor.execute("SELECT COUNT(*) FROM invoices")
    invoice_count = cursor.fetchone()[0]

    # Inventory Value
    try:
        cursor.execute(
            "SELECT SUM(stock * price) FROM medicines"
        )

        inventory_value = cursor.fetchone()[0]

        if inventory_value is None:
            inventory_value = 0

    except Exception:
        inventory_value = 0

    conn.close()

    return {
        "medicine_count": medicine_count,
        "invoice_count": invoice_count,
        "inventory_value": round(inventory_value, 2)
    }

def create_backup_metadata(database_path, backup_type):
    """
    Create metadata JSON beside a backup database.
    """

    stats = get_database_statistics(database_path)

    metadata = {

        "application": APP_NAME,

        "version": APP_VERSION,

        "backup_type": backup_type,

        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "medicine_count": stats["medicine_count"],

        "invoice_count": stats["invoice_count"],
        "inventory_value": stats["inventory_value"],
        
        "database_size_bytes": os.path.getsize(database_path),

        "database_size_mb": round(
            os.path.getsize(database_path) / (1024 * 1024),
            2,
        ),
    }

    json_path = database_path.replace(".db", ".json")

    with open(json_path, "w", encoding="utf-8") as f:

        json.dump(
            metadata,
            f,
            indent=4,
        )

    return json_path


def read_backup_metadata(database_path):
    """
    Read metadata JSON for a backup.
    """

    json_path = database_path.replace(".db", ".json")

    if not os.path.exists(json_path):
        return None

    with open(json_path, "r", encoding="utf-8") as f:

        return json.load(f)