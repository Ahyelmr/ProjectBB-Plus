import os
import shutil
import sqlite3
import sys
from core.paths import get_db_path
from database.user_repo import UserRepository


class DatabaseConnection:
    """Manages SQLite connections and schema initialization for data/projectbb.db."""

    def __init__(self, db_path: str | None = None):
        self._is_default_db = db_path is None
        self.db_path = db_path or get_db_path()
        self._seed_bundled_db_if_needed()
        self.init_db()

    def _seed_bundled_db_if_needed(self) -> None:
        """
        On first launch of a frozen PyInstaller bundle, copies the pre-loaded
        starter database from sys._MEIPASS/data/projectbb.db into the writable data/ folder.
        """
        if not self._is_default_db or not getattr(sys, "frozen", False):
            return
        if os.path.exists(self.db_path):
            return

        bundled_db = os.path.join(sys._MEIPASS, "data", "projectbb.db")
        if os.path.exists(bundled_db):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            shutil.copy2(bundled_db, self.db_path)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT CHECK(role IN ('Admin', 'Staff')) NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS discounts (
                    code TEXT PRIMARY KEY,
                    percentage REAL NOT NULL,
                    status TEXT CHECK(status IN ('ACTIVE', 'INACTIVE')) DEFAULT 'ACTIVE'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    sku TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    image_path TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_sequence (
                    date_str TEXT NOT NULL,
                    order_type TEXT NOT NULL DEFAULT 'DINE IN',
                    last_sequence INTEGER NOT NULL,
                    PRIMARY KEY (date_str, order_type)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence_number INTEGER NOT NULL,
                    order_type TEXT NOT NULL DEFAULT 'DINE IN',
                    order_date TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    amount_tendered REAL NOT NULL DEFAULT 0.0,
                    change_amount REAL NOT NULL DEFAULT 0.0,
                    discount_applied TEXT,
                    status TEXT DEFAULT 'PENDING'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    sku TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price_per_unit REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id),
                    FOREIGN KEY (sku) REFERENCES inventory (sku)
                )
            """)

            # Non-destructive migration for daily_sequence lacking order_type composite PK
            cursor.execute("PRAGMA table_info(daily_sequence)")
            existing_seq_cols = {row["name"] for row in cursor.fetchall()}
            if "order_type" not in existing_seq_cols:
                cursor.execute("ALTER TABLE daily_sequence RENAME TO daily_sequence_legacy")
                cursor.execute("""
                    CREATE TABLE daily_sequence (
                        date_str TEXT NOT NULL,
                        order_type TEXT NOT NULL DEFAULT 'DINE IN',
                        last_sequence INTEGER NOT NULL,
                        PRIMARY KEY (date_str, order_type)
                    )
                """)
                cursor.execute("DROP TABLE daily_sequence_legacy")

            # Non-destructive migration for existing databases lacking payment or order_type columns
            cursor.execute("PRAGMA table_info(orders)")
            existing_order_cols = {row["name"] for row in cursor.fetchall()}
            if "order_type" not in existing_order_cols:
                cursor.execute(
                    "ALTER TABLE orders ADD COLUMN order_type TEXT NOT NULL DEFAULT 'DINE IN'"
                )
            if "amount_tendered" not in existing_order_cols:
                cursor.execute(
                    "ALTER TABLE orders ADD COLUMN amount_tendered REAL NOT NULL DEFAULT 0.0"
                )
                cursor.execute("UPDATE orders SET amount_tendered = total_amount")
            if "change_amount" not in existing_order_cols:
                cursor.execute(
                    "ALTER TABLE orders ADD COLUMN change_amount REAL NOT NULL DEFAULT 0.0"
                )

            # Normalize any legacy/variant order_type strings in orders
            cursor.execute("""
                UPDATE orders
                SET order_type = CASE
                    WHEN UPPER(REPLACE(REPLACE(COALESCE(order_type, 'DINE IN'), '-', ' '), '_', ' '))
                         IN ('TAKE OUT', 'TAKEOUT', 'TO', 'TO GO', 'TOGO', 'TAKEAWAY', 'TAKE AWAY')
                    THEN 'TAKE OUT'
                    ELSE 'DINE IN'
                END
            """)

            # Reconcile daily_sequence strictly from actual orders per (date, order_type)
            cursor.execute("DELETE FROM daily_sequence")
            cursor.execute("""
                INSERT INTO daily_sequence (date_str, order_type, last_sequence)
                SELECT
                    SUBSTR(order_date, 1, 10) AS date_str,
                    order_type,
                    MAX(sequence_number) AS last_sequence
                FROM orders
                WHERE order_date IS NOT NULL AND LENGTH(TRIM(order_date)) >= 10
                GROUP BY SUBSTR(order_date, 1, 10), order_type
            """)

            # Non-destructive migration for existing inventory tables lacking is_active
            cursor.execute("PRAGMA table_info(inventory)")
            existing_inv_cols = {row["name"] for row in cursor.fetchall()}
            if "is_active" not in existing_inv_cols:
                cursor.execute(
                    "ALTER TABLE inventory ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1"
                )

            # Seed default accounts with PBKDF2-SHA256 hashes
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", UserRepository.hash_password("admin123"), "Admin"),
            )
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("staff", UserRepository.hash_password("staff123"), "Staff"),
            )

            # Migrate any legacy plaintext passwords in an existing DB
            cursor.execute("SELECT user_id, password_hash FROM users")
            for row in cursor.fetchall():
                if not row["password_hash"].startswith("pbkdf2_sha256$"):
                    cursor.execute(
                        "UPDATE users SET password_hash = ? WHERE user_id = ?",
                        (UserRepository.hash_password(row["password_hash"]), row["user_id"]),
                    )

            conn.commit()