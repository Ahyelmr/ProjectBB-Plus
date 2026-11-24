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
                    image_path TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_sequence (
                    date_str TEXT PRIMARY KEY,
                    last_sequence INTEGER NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence_number INTEGER NOT NULL,
                    order_date TEXT NOT NULL,
                    total_amount REAL NOT NULL,
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