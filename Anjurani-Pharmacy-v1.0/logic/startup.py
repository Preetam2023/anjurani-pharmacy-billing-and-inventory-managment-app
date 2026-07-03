import os
from db.schema import init_db
from logic.config import (
    APP_FOLDER,
    BACKUP_DIR,
    REPORTS_DIR,
    LOGS_DIR,
)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


def ensure_folder(path):
    """
    Create a folder if it does not already exist.
    """
    os.makedirs(path, exist_ok=True)


def initialize_application():
    """
    Prepare application folders and database.
    """

    os.makedirs(APP_FOLDER, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    init_db()   
    # --------------------------------------------------
    # Ensure database exists
    # --------------------------------------------------


    