import sqlite3
import os
import csv
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "projectbb.db")
        self.init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
            
            # Inject default Admin user for testing
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", "admin123", "Admin") 
            )
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("staff", "staff123", "Staff") 
            )
            conn.commit()

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

    def import_inventory_from_csv(self, filepath):
        """Reads a CSV file and bulk-updates the inventory database, parsing categories."""
        with open(filepath, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for row in reader:
                    # Map the 5 columns from the updated CSV structure
                    sku = row.get('sku') or row.get('SKU')
                    name = row.get('name') or row.get('Name')
                    price_raw = row.get('price') or row.get('Price')
                    category = row.get('category') or row.get('Category')
                    image_path = row.get('image_path') or row.get('Image Path') or ""
                    
                    # Ensure all required fields exist before inserting
                    if sku and name and price_raw is not None and category:
                        try:
                            price = float(price_raw)
                            cursor.execute(
                                "INSERT OR REPLACE INTO inventory (sku, name, price, category, image_path) VALUES (?, ?, ?, ?, ?)",
                                (sku, name, price, category, image_path)
                            )
                        except ValueError:
                            continue # Skips rows where the price is not a valid number
                conn.commit()