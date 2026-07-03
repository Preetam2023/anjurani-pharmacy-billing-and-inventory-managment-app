"""
Store details used on generated invoices.

IMPORTANT: update these with the client's actual store name, address, and
phone before final delivery — this is just placeholder text for now.
"""

STORE_NAME = "Anjurani Pharmacy"
STORE_ADDRESS = "Netajinagar, Gobindapur, Tamluk, Purba Medinipur"
STORE_PHONE = "+91 8145890904"
STORE_GSTIN = ""  # leave blank as not registered
APP_NAME = "Anjurani Pharmacy"
APP_VERSION = "1.0.0"

import os

# =====================================================
# Application Data Folder (Persistent)
# =====================================================

APP_FOLDER = os.path.join(
    os.path.expanduser("~"),
    "Documents",
    APP_NAME,
)

os.makedirs(APP_FOLDER, exist_ok=True)

# =====================================================
# Persistent Storage
# =====================================================

DATABASE_PATH = os.path.join(
    APP_FOLDER,
    "medical_store.db",
)

BACKUP_DIR = os.path.join(
    APP_FOLDER,
    "backups",
)

REPORTS_DIR = os.path.join(
    APP_FOLDER,
    "reports",
)

LOGS_DIR = os.path.join(
    APP_FOLDER,
    "logs",
)

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)