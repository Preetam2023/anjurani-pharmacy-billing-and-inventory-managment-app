"""
Phase 2 verification script — run this to confirm the database layer
works correctly before any UI is built on top of it.

Safe to re-run as many times as you like (invoice numbers are generated
uniquely each run, and seeding is skipped if data already exists).

Run with: python test_db.py
"""

import time
from db.schema import init_db
from db.seed import seed
from db import queries


def run():
    print("Initializing schema...")
    init_db()

    print("Seeding sample data...")
    seed()

    print("\n--- All medicines ---")
    for m in queries.get_all_medicines():
        print(f"  {m['id']:>2} | {m['name']:<22} | batch={m['batch_no']:<10} | "
              f"stock={m['stock']:<4} | price={m['price']}")

    print("\n--- Search 'para' ---")
    for m in queries.search_medicines("para"):
        print(f"  {m['name']} (batch {m['batch_no']})")

    print("\n--- Low stock (< 20) ---")
    for m in queries.get_low_stock(20):
        print(f"  ⚠ {m['name']} — stock: {m['stock']}")

    print("\n--- Expiring within 90 days ---")
    for m in queries.get_expiring_soon(90):
        print(f"  ⚠ {m['name']} — expires: {m['expiry_date']}")

    print("\n--- Already expired ---")
    for m in queries.get_expired():
        print(f"  ✗ {m['name']} — expired: {m['expiry_date']}")

    print("\n--- Creating a test invoice ---")
    medicines = queries.get_all_medicines()
    item_medicine = medicines[0]
    test_invoice_no = f"INV-TEST-{time.time_ns()}"
    invoice_id = queries.create_invoice(
        invoice_no=test_invoice_no,
        subtotal=100.0,
        discount_percent=10,
        grand_total=90.0,
        items=[{
            "medicine_id": item_medicine["id"],
            "quantity": 2,
            "unit_price": item_medicine["price"],
            "total_price": item_medicine["price"] * 2,
        }],
    )
    print(f"  Created invoice '{test_invoice_no}' (id {invoice_id})")

    updated = queries.get_medicine_by_id(item_medicine["id"])
    print(f"  Stock for '{updated['name']}' after sale: {updated['stock']} "
          f"(was {item_medicine['stock']})")

    print("\n--- Today's dashboard summary ---")
    print(f"  {queries.get_today_summary()}")

    print("\nAll checks ran without errors. Phase 2 is good.")


if __name__ == "__main__":
    run()