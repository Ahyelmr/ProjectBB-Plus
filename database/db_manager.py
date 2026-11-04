import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        # Maps the DB to the executable's folder to ensure data persistence after packaging
        self.db_path = os.path.join(os.getcwd(), "projectbb.db")
        self.init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT CHECK(role IN ('Admin', 'Staff')) NOT NULL
                )
            """)
            
            # Added image_path column to the inventory schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    sku TEXT PRIMARY KEY, 
                    name TEXT NOT NULL, 
                    price REAL NOT NULL, 
                    stock_qty INTEGER NOT NULL,
                    image_path TEXT DEFAULT ''
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    sequence_number INTEGER NOT NULL, 
                    status TEXT NOT NULL, 
                    total_amount REAL NOT NULL, 
                    order_date TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    order_id INTEGER, 
                    sku TEXT, 
                    quantity INTEGER, 
                    FOREIGN KEY(order_id) REFERENCES orders(order_id)
                )
            """)

            cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", "admin123", "Admin"))
            cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("staff", "staff123", "Staff"))
            
            cursor.execute("SELECT COUNT(*) FROM inventory")
            if cursor.fetchone()[0] == 0:
                # Injects default test items mapped to hypothetical image paths
                cursor.execute("INSERT INTO inventory VALUES ('SKU01', 'Test Burger', 50.0, 100, 'assets/burger.png'), ('SKU02', 'Test Fries', 30.0, 100, 'assets/fries.png')")
            conn.commit()

    def add_inventory_item(self, sku, name, price, stock_qty, image_path=""):
        """Inserts or updates an inventory item with its associated image path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO inventory (sku, name, price, stock_qty, image_path) VALUES (?, ?, ?, ?, ?)",
                (sku, name, price, stock_qty, image_path)
            )
            conn.commit()
            
    def add_user(self, username, password_hash, role):
        """Creates a new user account if the username does not already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()

    def create_order(self, cart_list, total_amount):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT MAX(sequence_number) FROM orders WHERE order_date LIKE ?", (today + '%',))
            max_seq = cursor.fetchone()[0]
            seq_num = 1 if max_seq is None else max_seq + 1
            
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO orders (sequence_number, status, total_amount, order_date) VALUES (?, ?, ?, ?)", (seq_num, 'PENDING', total_amount, date_str))
            order_id = cursor.lastrowid
            
            for item in cart_list:
                cursor.execute("INSERT INTO order_items (order_id, sku, quantity) VALUES (?, ?, ?)", (order_id, item['sku'], item['quantity']))
                cursor.execute("UPDATE inventory SET stock_qty = stock_qty - ? WHERE sku = ?", (item['quantity'], item['sku']))
            conn.commit()
            return order_id, seq_num