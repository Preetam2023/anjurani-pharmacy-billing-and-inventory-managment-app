"""
Seeds the database with sample medicines so you have data to test
search, low-stock, expiry, and seller filtering against before the UI
is built.

Run with: python -m db.seed
Safe to re-run — it checks if data already exists first.
"""

from datetime import date, timedelta
from db.connection import get_connection
from db.schema import init_db
from db.queries import add_medicine, get_all_medicines

SAMPLE_MEDICINES = [
    # name, batch_no, expiry_in_days, price, stock, seller_name
    ("Paracetamol 500mg", "PCM-001", 200, 50.0, 12, "ABC Medicine Distributors"),   # low stock
    ("Crocin", "CRO-002", 400, 35.0, 80, "ABC Medicine Distributors"),
    ("Amoxicillin 250mg", "AMX-010", 45, 120.0, 30, "MediWell Supplies"),           # expiring soon
    ("Cetirizine 10mg", "CTZ-005", 300, 18.0, 150, "MediWell Supplies"),
    ("Azithromycin 500mg", "AZI-021", -10, 95.0, 25, "Sunrise Pharma Agencies"),    # already expired
    ("Ibuprofen 400mg", "IBU-014", 250, 28.0, 8, "Sunrise Pharma Agencies"),         # low stock
    ("Vitamin C 500mg", "VTC-003", 500, 60.0, 200, "ABC Medicine Distributors"),
    ("ORS Sachet", "ORS-007", 600, 15.0, 300, "MediWell Supplies"),
]


def seed():
    conn = get_connection()
    init_db()

    existing = get_all_medicines()
    if existing:
        print(f"Database already has {len(existing)} medicine(s). Skipping seed.")
        return

    today = date.today()
    for name, batch_no, days_offset, price, stock, seller_name in SAMPLE_MEDICINES:
        expiry = (today + timedelta(days=days_offset)).isoformat()
        add_medicine(name, batch_no, expiry, price, stock, seller_name)

    print(f"Seeded {len(SAMPLE_MEDICINES)} sample medicines.")


if __name__ == "__main__":
    seed()
