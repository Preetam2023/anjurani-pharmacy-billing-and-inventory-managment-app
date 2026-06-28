# Medical Store Billing System

Offline desktop billing & inventory app for a retail medical store.
Stack: Python 3.12+, PySide6, SQLite, ReportLab, PyInstaller.

## Setup (Windows)

1. Make sure Python 3.12+ is installed (check with `python --version`).
2. Open a terminal in this project folder.
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate it:
   ```
   venv\Scripts\activate
   ```
5. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
6. Run the app:
   ```
   python main.py
   ```

If a window opens saying "Setup successful — PySide6 is working.", the
environment is good and we move to the next phase (database layer).

## Project Structure

```
medical-billing-system/
├── main.py          # entry point
├── requirements.txt
├── ui/               # screens / widgets (Billing, Inventory, History, Dashboard)
├── db/                # database connection + queries
├── logic/             # business logic (billing calc, stock updates, alerts)
├── assets/            # icons, images
└── reports/           # generated PDF invoices
```

## Git

```
git init
git add .
git commit -m "Phase 1: project setup"
```
