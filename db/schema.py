"""
Database schema: creates tables and indexes if they don't already exist.
Call init_db() once at app startup.

Also handles small migrations (e.g. adding a column to a table that
already exists from an earlier version of the app) so the existing
medical_store.db file on a dev/client machine doesn't need to be deleted
every time the schema grows.
"""

from db.connection import get_connection

CREATE_MEDICINES = """
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    batch_no TEXT NOT NULL,
    expiry_date DATE,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    seller_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_CUSTOMERS = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INVOICES = """
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT UNIQUE NOT NULL,
    invoice_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    customer_id INTEGER REFERENCES customers(id),
    subtotal REAL NOT NULL,
    discount_percent REAL NOT NULL DEFAULT 0,
    grand_total REAL NOT NULL
);
"""

CREATE_INVOICE_ITEMS = """
CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    medicine_id INTEGER NOT NULL,
    batch_no TEXT,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    total_price REAL NOT NULL,
    FOREIGN KEY(invoice_id) REFERENCES invoices(id),
    FOREIGN KEY(medicine_id) REFERENCES medicines(id)
);
"""

CREATE_STOCK_HISTORY = """
CREATE TABLE IF NOT EXISTS stock_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER,
    medicine_name TEXT NOT NULL,
    batch_no TEXT,
    seller_name TEXT,
    packets INTEGER,
    units_per_packet INTEGER,
    quantity_added INTEGER NOT NULL,
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(medicine_id) REFERENCES medicines(id)
);
"""

# Indexes for the columns we search/filter on most.
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_medicines_name ON medicines(name);",
    "CREATE INDEX IF NOT EXISTS idx_medicines_batch_no ON medicines(batch_no);",
    "CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);",
    "CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id ON invoice_items(invoice_id);",
    "CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_medicines_seller_name ON medicines(seller_name);",
    "CREATE INDEX IF NOT EXISTS idx_stock_history_medicine_id ON stock_history(medicine_id);",
    "CREATE INDEX IF NOT EXISTS idx_stock_history_seller_name ON stock_history(seller_name);",
    "CREATE INDEX IF NOT EXISTS idx_stock_history_received_at ON stock_history(received_at);",
]


def _migrate_medicines_seller_name(conn):
    """Adds seller_name to medicines if it's missing (older databases)."""
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(medicines)").fetchall()]
    if "seller_name" not in columns:
        conn.execute("ALTER TABLE medicines ADD COLUMN seller_name TEXT")


def _migrate_invoices_customer_id(conn):
    """
    Adds the customer_id column to an invoices table that was created
    before this column existed. Safe to run every startup — it only
    acts if the column is actually missing.
    """
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(invoices)").fetchall()]
    if "customer_id" not in columns:
        conn.execute("ALTER TABLE invoices ADD COLUMN customer_id INTEGER REFERENCES customers(id)")


def _migrate_invoice_items_batch_no(conn):
    """Adds batch_no to invoice_items if it's missing (older databases)."""
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(invoice_items)").fetchall()]
    if "batch_no" not in columns:
        conn.execute("ALTER TABLE invoice_items ADD COLUMN batch_no TEXT")


def init_db():
    conn = get_connection()
    conn.execute(CREATE_MEDICINES)
    conn.execute(CREATE_CUSTOMERS)
    conn.execute(CREATE_INVOICES)
    conn.execute(CREATE_INVOICE_ITEMS)
    conn.execute(CREATE_STOCK_HISTORY)
    _migrate_invoices_customer_id(conn)
    _migrate_invoice_items_batch_no(conn)
    _migrate_medicines_seller_name(conn)
    for stmt in CREATE_INDEXES:
        conn.execute(stmt)
    conn.commit()
