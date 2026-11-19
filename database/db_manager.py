import sqlite3
import os
import csv
import hashlib
import hmac
from datetime import datetime


class DatabaseManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "projectbb.db")
        self.init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # --- Password Security Helpers ---
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a random salt."""
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return f"pbkdf2_sha256${salt.hex()}${key.hex()}"

    @staticmethod
    def verify_password(stored_hash: str, provided_password: str) -> bool:
        """Verifies a plaintext password against a stored PBKDF2 hash safely."""
        try:
            algorithm, salt_hex, key_hex = stored_hash.split("$")
            if algorithm != "pbkdf2_sha256":
                return False
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            provided_key = hashlib.pbkdf2_hmac(
                "sha256", provided_password.encode("utf-8"), salt, 100_000
            )
            return hmac.compare_digest(expected_key, provided_key)
        except (ValueError, TypeError):
            return False

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Users Table (Login Screen & Access Control)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT CHECK(role IN ('Admin', 'Staff')) NOT NULL
                )
            """)

            # 2. Discounts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS discounts (
                    code TEXT PRIMARY KEY,
                    percentage REAL NOT NULL,
                    status TEXT CHECK(status IN ('ACTIVE', 'INACTIVE')) DEFAULT 'ACTIVE'
                )
            """)

            # 3. Inventory Table (Updated with 'category' column and infinite stock)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    sku TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    image_path TEXT
                )
            """)

            # 4. Daily Sequence Tracking Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_sequence (
                    date_str TEXT PRIMARY KEY,
                    last_sequence INTEGER NOT NULL
                )
            """)

            # 5. Orders Master Table
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

            # 6. Order Line Items Table
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

            # Inject default Admin & Staff users with hashed passwords
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", self.hash_password("admin123"), "Admin")
            )
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("staff", self.hash_password("staff123"), "Staff")
            )

            # Migrate any legacy unhashed passwords already in an existing DB
            cursor.execute("SELECT user_id, password_hash FROM users")
            for row in cursor.fetchall():
                if not row["password_hash"].startswith("pbkdf2_sha256$"):
                    cursor.execute(
                        "UPDATE users SET password_hash = ? WHERE user_id = ?",
                        (self.hash_password(row["password_hash"]), row["user_id"])
                    )

            conn.commit()

    # --- User Account Management ---
    def create_user(self, username: str, password: str, role: str) -> tuple[bool, str]:
        """Creates a new user account with a salted password hash."""
        clean_username = username.strip()
        clean_role = role.strip().capitalize()

        if clean_role not in ("Admin", "Staff"):
            return False, "Invalid account role. Must be Admin or Staff."
        if len(clean_username) < 3:
            return False, "Username must be at least 3 characters long."
        if " " in clean_username:
            return False, "Username cannot contain spaces."
        if len(password) < 6:
            return False, "Password must be at least 6 characters long."

        hashed_pw = self.hash_password(password)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (clean_username, hashed_pw, clean_role)
                )
                conn.commit()
            return True, f"{clean_role} account '{clean_username}' created successfully."
        except sqlite3.IntegrityError:
            return False, f"Username '{clean_username}' is already taken."
        except sqlite3.Error as e:
            return False, f"Database error ({self.db_path}): {e}"

    def authenticate_user(self, username: str, password: str):
        """Verifies user credentials and returns the user's role if valid, else None."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, password_hash, role FROM users WHERE username = ?",
                (username.strip(),)
            )
            user = cursor.fetchone()

        if not user:
            return None

        if self.verify_password(user["password_hash"], password):
            return user["role"]

        return None

    # --- Order & Sequence Management ---
    def get_next_sequence(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_sequence FROM daily_sequence WHERE date_str = ?", (today_str,))
            row = cursor.fetchone()

            if row:
                next_seq = row['last_sequence'] + 1
                cursor.execute("UPDATE daily_sequence SET last_sequence = ? WHERE date_str = ?", (next_seq, today_str))
            else:
                next_seq = 1
                cursor.execute("INSERT INTO daily_sequence (date_str, last_sequence) VALUES (?, ?)", (today_str, next_seq))

            conn.commit()
            return next_seq

    def create_order(self, cart_items, total_amount, discount_applied="None"):
        sequence_number = self.get_next_sequence()
        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (sequence_number, order_date, total_amount, discount_applied, status)
                VALUES (?, ?, ?, ?, 'PREPARING')
            """, (sequence_number, order_date, total_amount, discount_applied))

            order_id = cursor.lastrowid

            for sku, data in cart_items.items():
                cursor.execute("""
                    INSERT INTO order_items (order_id, sku, quantity, price_per_unit)
                    VALUES (?, ?, ?, ?)
                """, (order_id, sku, data['qty'], data['price']))

            conn.commit()
            return sequence_number, order_id

    # --- Inventory Management ---
    def sku_exists(self, sku: str) -> bool:
        """Checks whether a given SKU already exists in the inventory table."""
        clean_sku = sku.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM inventory WHERE UPPER(sku) = ?", (clean_sku,))
            return cursor.fetchone() is not None

    def get_inventory_categories(self) -> list[str]:
        """Returns a sorted list of distinct categories currently in the inventory."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT category
                FROM inventory
                WHERE category IS NOT NULL AND TRIM(category) != ''
                ORDER BY category ASC
            """)
            return [row["category"] for row in cursor.fetchall()]

    def add_inventory_item(
        self,
        sku: str,
        name: str,
        price: float,
        category: str,
        image_path: str = ""
    ) -> tuple[bool, str]:
        """Inserts a new inventory item or updates an existing item with the same SKU."""
        clean_sku = sku.strip().upper()
        clean_name = name.strip()
        clean_category = category.strip()
        clean_image = (image_path or "").strip()

        if not clean_sku:
            return False, "SKU is required."
        if not clean_name:
            return False, "Item name is required."
        if not clean_category:
            return False, "Category is required."

        try:
            numeric_price = float(price)
            if numeric_price < 0:
                return False, "Price cannot be negative."
        except (ValueError, TypeError):
            return False, "Price must be a valid number."

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO inventory (sku, name, price, category, image_path)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (clean_sku, clean_name, numeric_price, clean_category, clean_image)
                )
                conn.commit()
            return True, f"'{clean_name}' ({clean_sku}) has been saved to the menu."
        except sqlite3.Error as e:
            return False, f"Database error: {e}"

    def import_inventory_from_csv(self, filepath):
        """Reads a CSV file and bulk-updates the inventory database, parsing categories."""
        with open(filepath, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for row in reader:
                    sku = row.get('sku') or row.get('SKU')
                    name = row.get('name') or row.get('Name')
                    price_raw = row.get('price') or row.get('Price')
                    category = row.get('category') or row.get('Category')
                    image_path = row.get('image_path') or row.get('Image Path') or ""

                    if sku and name and price_raw is not None and category:
                        try:
                            price = float(price_raw)
                            cursor.execute(
                                "INSERT OR REPLACE INTO inventory (sku, name, price, category, image_path) VALUES (?, ?, ?, ?, ?)",
                                (sku.strip().upper(), name.strip(), price, category.strip(), image_path.strip())
                            )
                        except ValueError:
                            continue
                conn.commit()