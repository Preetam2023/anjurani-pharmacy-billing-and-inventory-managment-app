"""
Reusable database query functions.

The Inventory, Billing, and History UI modules (Phase 4-6) will call these
instead of writing raw SQL directly in the UI code.
"""

from datetime import date, timedelta, datetime
from db.connection import get_connection
import sqlite3

def current_timestamp():
    """
    Local (IST) timestamp instead of SQLite's UTC CURRENT_TIMESTAMP.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class InsufficientStockError(Exception):
    """Raised when an invoice would reduce a medicine's stock below zero."""
    pass


# ---------- Medicines ----------

def add_medicine(
    name,
    batch_no,
    expiry_date,
    packet_price,
    stock,
    seller_name=None,
    packets=None,
    units_per_packet=1,
):
    conn = get_connection()
    unit_price = packet_price / max(units_per_packet, 1)

    cur = conn.execute(
        """
        INSERT INTO medicines
    (
        name,
        batch_no,
        expiry_date,
        packet_price,
        units_per_packet,
        price,
        stock,
        seller_name
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        name,
        batch_no,
        expiry_date,
        packet_price,
        units_per_packet,
        unit_price,
        stock,
        seller_name,
    ),
)
    medicine_id = cur.lastrowid

    # Log the initial stock as the first stock_history entry, so "when was
    # this received / from whom" has an answer from day one, not just from
    # the next restock onward.
    if stock and stock > 0:
        purchase_cost = packet_price * (packets or 0)

        conn.execute(
            """
        INSERT INTO stock_history
        (
            medicine_id,
            medicine_name,
            batch_no,
            seller_name,
            packet_price,
            packets,
            units_per_packet,
            purchase_cost,
            quantity_added,
            received_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            medicine_id,
            name,
            batch_no,
            seller_name,
            packet_price,
            packets,
            units_per_packet,
            purchase_cost,
            stock,
            current_timestamp(),
        ),
    )
    conn.commit()
    return medicine_id


def update_medicine(medicine_id, name=None, batch_no=None, expiry_date=None, packet_price=None,
units_per_packet=None,
stock=None,seller_name=None):
    """Update only the fields provided. Stock changes go through add_stock()."""
    conn = get_connection()
    fields, values = [], []
    if name is not None:
        fields.append("name = ?"); values.append(name)
    if batch_no is not None:
        fields.append("batch_no = ?"); values.append(batch_no)
    if expiry_date is not None:
        fields.append("expiry_date = ?"); values.append(expiry_date)
    if packet_price is not None:
        if units_per_packet is None:

            row = conn.execute(
                "SELECT units_per_packet FROM medicines WHERE id=?",
                (medicine_id,),
            ).fetchone()

            units_per_packet = row["units_per_packet"]

        unit_price = packet_price / max(units_per_packet, 1)

        fields.append("packet_price = ?")
        values.append(packet_price)

        fields.append("price = ?")
        values.append(unit_price)
    elif units_per_packet is not None:
        row = conn.execute(
            "SELECT packet_price FROM medicines WHERE id=?",
            (medicine_id,),
        ).fetchone()

        unit_price = row["packet_price"] / max(units_per_packet, 1)

        fields.append("price = ?")
        values.append(unit_price)
    if units_per_packet is not None:
        fields.append("units_per_packet = ?")
        values.append(units_per_packet)
    if stock is not None:
        fields.append("stock = ?")
        values.append(stock)
    if seller_name is not None:
        fields.append("seller_name = ?"); values.append(seller_name)
    if not fields:
        return
    values.append(medicine_id)
    conn.execute(f"UPDATE medicines SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()


def add_stock(
    medicine_id,
    quantity,
    packet_price=None,
    seller_name=None,
    batch_no=None,
    packets=None,
    units_per_packet=None,
):
    """
    Increase stock and log a stock_history entry for inventory tracking.
    If seller_name is given, it also becomes the medicine's "current"
    seller (consistent with how Add Medicine's seller default works —
    the most recent delivery is the most relevant seller to show/default to).
    """
    conn = get_connection()
    medicine = conn.execute(
    """
    SELECT
        name,
        batch_no,
        packet_price,
        units_per_packet
    FROM medicines
    WHERE id=?
    """, (medicine_id,)
    ).fetchone()

    conn.execute(
        "UPDATE medicines SET stock = stock + ? WHERE id = ?",
        (quantity, medicine_id),
    )
    if seller_name:
        conn.execute(
            "UPDATE medicines SET seller_name = ? WHERE id = ?",
            (seller_name, medicine_id),
        )
    if packet_price is not None:
        unit_price = packet_price / max(units_per_packet or 1, 1)

        conn.execute(
            """
        UPDATE medicines
        SET
            packet_price = ?,
            units_per_packet = ?,
            price = ?
        WHERE id = ?
        """,
            (
            packet_price,
            units_per_packet,
            unit_price,
            medicine_id,
            ),
        )
    if quantity and quantity > 0 and medicine is not None:
        purchase_cost = (packet_price or medicine["packet_price"]) * (packets or 0)

        conn.execute(
            """
        INSERT INTO stock_history
        (
            medicine_id,
            medicine_name,
            batch_no,
            seller_name,
            packet_price,
            packets,
            units_per_packet,
            purchase_cost,
            quantity_added,
            received_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            medicine_id,
            medicine["name"],
            batch_no or medicine["batch_no"],
            seller_name,
            packet_price or medicine["packet_price"],
            packets,
            units_per_packet,
            purchase_cost,
            quantity,
            current_timestamp(),
        ),
    )

    conn.commit()



def delete_medicine(medicine_id):
    conn = get_connection()

    # Check if this medicine has ever been sold
    used = conn.execute(
        """
        SELECT 1
        FROM invoice_items
        WHERE medicine_id = ?
        LIMIT 1
        """,
        (medicine_id,)
    ).fetchone()

    if used:
        return False

    try:
        # Remove stock history first
        conn.execute(
            "DELETE FROM stock_history WHERE medicine_id = ?",
            (medicine_id,)
        )

        # Now remove the medicine
        conn.execute(
            "DELETE FROM medicines WHERE id = ?",
            (medicine_id,)
        )

        conn.commit()
        return True

    except sqlite3.Error:
        conn.rollback()
        raise


def get_medicine_by_id(medicine_id):
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM medicines WHERE id = ?", (medicine_id,)
    ).fetchone()


def get_all_medicines():
    conn = get_connection()
    return conn.execute("SELECT * FROM medicines ORDER BY name").fetchall()


def search_medicines(query):
    """Search by name or batch number. Used by the billing screen's live search."""
    conn = get_connection()
    like = f"%{query}%"
    return conn.execute(
        "SELECT * FROM medicines WHERE name LIKE ? OR batch_no LIKE ? ORDER BY name",
        (like, like),
    ).fetchall()


def get_low_stock(threshold=20):
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM medicines WHERE stock < ? ORDER BY stock ASC",
        (threshold,),
    ).fetchall()


def get_expiring_soon(days=90):
    conn = get_connection()
    today = date.today()
    cutoff = today + timedelta(days=days)
    return conn.execute(
        "SELECT * FROM medicines WHERE expiry_date >= ? AND expiry_date <= ? "
        "ORDER BY expiry_date ASC",
        (today.isoformat(), cutoff.isoformat()),
    ).fetchall()


def get_expired():
    conn = get_connection()
    today = date.today().isoformat()
    return conn.execute(
        "SELECT * FROM medicines WHERE expiry_date < ? ORDER BY expiry_date ASC",
        (today,),
    ).fetchall()


def get_distinct_sellers():
    """All distinct seller/distributor names used so far, newest-used
    first isn't needed here — just an alphabetical list for the dropdown."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT seller_name FROM medicines "
        "WHERE seller_name IS NOT NULL AND TRIM(seller_name) != '' "
        "ORDER BY seller_name COLLATE NOCASE"
    ).fetchall()
    return [row["seller_name"] for row in rows]


def get_last_used_seller():
    """
    The seller name used on the most recently added medicine — used as
    the default pre-filled value when adding the next one, since the
    same distributor often supplies several items in one delivery.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT seller_name FROM medicines "
        "WHERE seller_name IS NOT NULL AND TRIM(seller_name) != '' "
        "ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return row["seller_name"] if row else ""


def get_stock_history(medicine_query=None, seller_name=None, date_from=None, date_to=None):
    """
    Flexible stock-receipt history lookup for the Stock History dialog.
    All filters are optional:
      - medicine_query: partial match against medicine name or batch number
      - seller_name: exact match against a specific seller
      - date_from / date_to: 'YYYY-MM-DD' strings, inclusive range
    Most recent first.
    """
    conn = get_connection()
    query = "SELECT * FROM stock_history WHERE 1=1"
    params = []

    if medicine_query:
        query += " AND (medicine_name LIKE ? OR batch_no LIKE ?)"
        like = f"%{medicine_query}%"
        params.extend([like, like])
    if seller_name:
        query += " AND seller_name = ?"
        params.append(seller_name)
    if date_from:
        query += " AND date(received_at) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date(received_at) <= ?"
        params.append(date_to)

    query += " ORDER BY received_at DESC"
    return conn.execute(query, params).fetchall()


# ---------- Invoices ----------

def generate_invoice_no():
    """Format: INV-YYYYMMDD-### where ### is today's running count + 1."""
    conn = get_connection()
    today = date.today()
    count_row = conn.execute(
        "SELECT COUNT(*) AS c FROM invoices WHERE date(invoice_date) = ?",
        (today.isoformat(),),
    ).fetchone()
    seq = count_row["c"] + 1
    return f"INV-{today.strftime('%Y%m%d')}-{seq:03d}"


def create_invoice(invoice_no, subtotal, discount_percent, grand_total, items, customer_id=None):
    """
    items: list of dicts -> {medicine_id, quantity, unit_price, total_price}
    Saves the invoice + items and reduces stock, all in one transaction.
    Raises InsufficientStockError (and writes nothing) if any item would
    take a medicine's stock below zero.
    """
    conn = get_connection()
    try:
        # Validate every line against current stock BEFORE writing anything,
        # so a partial/invalid invoice never gets created.
        for item in items:
            medicine = conn.execute(
                "SELECT name, stock FROM medicines WHERE id = ?",
                (item["medicine_id"],),
            ).fetchone()
            if medicine is None:
                raise InsufficientStockError(
                    f"Medicine with id {item['medicine_id']} no longer exists."
                )
            if item["quantity"] > medicine["stock"]:
                raise InsufficientStockError(
                    f"Only {medicine['stock']} unit(s) of '{medicine['name']}' "
                    f"are in stock (requested {item['quantity']})."
                )

        invoice_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur = conn.execute(
            """
            INSERT INTO invoices
            (invoice_no, invoice_date, customer_id, subtotal, discount_percent, grand_total)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                invoice_no,
                invoice_date,
                customer_id,
                subtotal,
                discount_percent,
                grand_total,
            ),
        )
        invoice_id = cur.lastrowid

        for item in items:
            conn.execute(
                "INSERT INTO invoice_items "
                "(invoice_id, medicine_id, batch_no, expiry_date, quantity, unit_price, total_price) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (invoice_id, item["medicine_id"], item.get("batch_no"), item.get("expiry_date"),
                 item["quantity"], item["unit_price"], item["total_price"]),
            )
            conn.execute(
                "UPDATE medicines SET stock = stock - ? WHERE id = ?",
                (item["quantity"], item["medicine_id"]),
            )

        conn.commit()
        return invoice_id
    except Exception:
        conn.rollback()
        raise


def get_all_invoices():
    conn = get_connection()
    return conn.execute(
        "SELECT invoices.*, customers.name AS customer_name, customers.phone AS customer_phone "
        "FROM invoices LEFT JOIN customers ON customers.id = invoices.customer_id "
        "ORDER BY invoices.invoice_date DESC"
    ).fetchall()


def get_invoice_by_no(invoice_no):
    conn = get_connection()
    return conn.execute(
        "SELECT invoices.*, customers.name AS customer_name, customers.phone AS customer_phone "
        "FROM invoices LEFT JOIN customers ON customers.id = invoices.customer_id "
        "WHERE invoices.invoice_no = ?",
        (invoice_no,),
    ).fetchone()


def get_invoice_by_id(invoice_id):
    conn = get_connection()
    return conn.execute(
        "SELECT invoices.*, customers.name AS customer_name, customers.phone AS customer_phone "
        "FROM invoices LEFT JOIN customers ON customers.id = invoices.customer_id "
        "WHERE invoices.id = ?",
        (invoice_id,),
    ).fetchone()


def get_invoices_by_date(target_date):
    """target_date as 'YYYY-MM-DD' string."""
    conn = get_connection()
    return conn.execute(
        "SELECT invoices.*, customers.name AS customer_name, customers.phone AS customer_phone "
        "FROM invoices LEFT JOIN customers ON customers.id = invoices.customer_id "
        "WHERE date(invoices.invoice_date) = ? ORDER BY invoices.invoice_date DESC",
        (target_date,),
    ).fetchall()


def search_invoices(invoice_no=None, target_date=None):
    """
    Flexible invoice search for the History screen. Either filter can be
    left as None to skip it; passing neither returns everything.
    invoice_no does a partial (LIKE) match; target_date is an exact
    'YYYY-MM-DD' match.
    """
    conn = get_connection()
    query = (
        "SELECT invoices.*, customers.name AS customer_name, customers.phone AS customer_phone "
        "FROM invoices LEFT JOIN customers ON customers.id = invoices.customer_id "
        "WHERE 1=1"
    )
    params = []
    if invoice_no:
        query += " AND invoices.invoice_no LIKE ?"
        params.append(f"%{invoice_no}%")
    if target_date:
        query += " AND date(invoices.invoice_date) = ?"
        params.append(target_date)
    query += " ORDER BY invoices.invoice_date DESC"
    return conn.execute(query, params).fetchall()


def get_invoice_items(invoice_id):
    conn = get_connection()
    return conn.execute(
        "SELECT invoice_items.*, medicines.name AS medicine_name, "
        "medicines.expiry_date AS medicine_expiry_date "
        "FROM invoice_items "
        "JOIN medicines ON medicines.id = invoice_items.medicine_id "
        "WHERE invoice_id = ?",
        (invoice_id,),
    ).fetchall()


# ---------- Customers ----------

def get_customer_by_phone(phone):
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM customers WHERE phone = ?", (phone,)
    ).fetchone()


def get_or_create_customer(phone, name):
    """
    Returns the customer's id. If the phone number already exists and a
    different name was entered this time, the stored name is updated —
    phone number is treated as the stable key, name can drift/correct.
    """
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM customers WHERE phone = ?", (phone,)
    ).fetchone()
    if existing:
        if name and name != existing["name"]:
            conn.execute("UPDATE customers SET name = ? WHERE id = ?", (name, existing["id"]))
            conn.commit()
        return existing["id"]

    cur = conn.execute(
        "INSERT INTO customers (phone, name) VALUES (?, ?)", (phone, name)
    )
    conn.commit()
    return cur.lastrowid


# ---------- Quick-add / frequently sold ----------

def get_most_sold_medicines(limit=8):
    """
    Top medicines by total quantity sold across all invoices, limited to
    medicines that currently have stock (no point quick-adding something
    that can't be sold). Used for the Billing screen's quick-add row.
    """
    conn = get_connection()
    return conn.execute(
        "SELECT medicines.id, medicines.name, medicines.price, medicines.stock, "
        "SUM(invoice_items.quantity) AS total_sold "
        "FROM invoice_items "
        "JOIN medicines ON medicines.id = invoice_items.medicine_id "
        "WHERE medicines.stock > 0 "
        "GROUP BY medicines.id "
        "ORDER BY total_sold DESC "
        "LIMIT ?",
        (limit,),
    ).fetchall()


def get_sales_summary(granularity="day"):
    """
    Returns invoice totals grouped by period, most recent first.
    granularity: 'day' | 'month' | 'year'
    Each row: {period, bills, total_sales} — period is 'YYYY-MM-DD',
    'YYYY-MM', or 'YYYY' depending on granularity.
    """
    if granularity == "day":
        period_expr = "date(invoice_date)"
    elif granularity == "month":
        period_expr = "strftime('%Y-%m', invoice_date)"
    elif granularity == "year":
        period_expr = "strftime('%Y', invoice_date)"
    else:
        raise ValueError(f"Unknown granularity: {granularity!r}")

    conn = get_connection()
    return conn.execute(
        f"SELECT {period_expr} AS period, COUNT(*) AS bills, "
        f"COALESCE(SUM(grand_total), 0) AS total_sales "
        f"FROM invoices GROUP BY period ORDER BY period DESC"
    ).fetchall()


# ---------- Dashboard helpers ----------

def get_today_summary():
    conn = get_connection()
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT COUNT(*) AS bill_count, COALESCE(SUM(grand_total), 0) AS total_sales "
        "FROM invoices WHERE date(invoice_date) = ?",
        (today,),
    ).fetchone()
    items_row = conn.execute(
        "SELECT COALESCE(SUM(invoice_items.quantity), 0) AS items_sold "
        "FROM invoice_items "
        "JOIN invoices ON invoices.id = invoice_items.invoice_id "
        "WHERE date(invoices.invoice_date) = ?",
        (today,),
    ).fetchone()
    inventory_value_row = conn.execute(
        "SELECT COALESCE(SUM(packet_price * (stock * 1.0 / units_per_packet)),0) AS inventory_value FROM medicines"
    ).fetchone()
    return {
        "bills_today": row["bill_count"],
        "sales_today": row["total_sales"],
        "items_sold_today": items_row["items_sold"],
        "inventory_value": inventory_value_row["inventory_value"],
    }
