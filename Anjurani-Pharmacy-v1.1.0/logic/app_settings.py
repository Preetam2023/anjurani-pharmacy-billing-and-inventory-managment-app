import json
from pathlib import Path

APP_FOLDER = Path.home() / "Documents" / "Anjurani Pharmacy"
APP_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = APP_FOLDER / "settings.json"

DEFAULT_SETTINGS = {
    "invoice_layout": "modern"
}


def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            settings = DEFAULT_SETTINGS.copy()
            settings.update(data)
            return settings

        except Exception:
            return DEFAULT_SETTINGS.copy()

    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


def get_invoice_layout():
    return load_settings()["invoice_layout"]


def set_invoice_layout(layout):
    settings = load_settings()
    settings["invoice_layout"] = layout
    save_settings(settings)