import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        """Initializes the database path and builds tables upon creation."""
        self.db_path = os.path.join(os.path.dirname(__file__), "projectbb.db")
        self.init_db()

    def _get_connection(self):
        """Establishes and returns a connection to the local SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def init_db(self):
        """Creates the core database tables if they do not already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Menu Items / SKUs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    sku TEXT PRIMARY KEY, 
                    name TEXT NOT NULL,
                    price REAL NOT NULL, 
                    stock_qty INTEGER NOT NULL
                )
            """)
            
            # 2. Daily Sequence Tracking Table (For Automated Resets)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_sequence (
                    date_str TEXT PRIMARY KEY, 
                    last_sequence INTEGER NOT NULL
                )
            """)
            
            # 3. Orders Master Table (FIFO Queue Tracking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    sequence_number INTEGER NOT NULL,
                    order_date TEXT NOT NULL,
                    total_amount REAL NOT NULL, 
                    status TEXT DEFAULT 'PENDING'
                )
            """)
            
            # 4. Order Line Items Table
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
            conn.commit()

    def get_next_sequence_number(self):
        """Generates a non-repeating order sequence number that resets daily."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_sequence FROM daily_sequence WHERE date_str = ?", (today,))
            row = cursor.fetchone()
            next_seq = 1 if row is None else row["last_sequence"] + 1
            
            if row is None:
                cursor.execute("INSERT INTO daily_sequence VALUES (?, ?)", (today, next_seq))
            else:
                cursor.execute("UPDATE daily_sequence SET last_sequence = ? WHERE date_str = ?", (next_seq, today))
            
            conn.commit()
            return next_seq

    def create_order(self, cart_items, total_amount):
        """Logs transaction, deducts SKU stock in real time, and assigns sequence number."""
        today_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        seq_num = self.get_next_sequence_number()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert main order record
            cursor.execute(
                "INSERT INTO orders (sequence_number, order_date, total_amount, status) VALUES (?, ?, ?, 'PENDING')",
                (seq_num, today_time, total_amount)
            )
            order_id = cursor.lastrowid
            
            # Insert items & deduct stock
            for item in cart_items:
                sku = item["sku"]
                qty = item["quantity"]
                price = item["price"]
                
                cursor.execute(
                    "INSERT INTO order_items (order_id, sku, quantity, price_per_unit) VALUES (?, ?, ?, ?)",
                    (order_id, sku, qty, price)
                )
                cursor.execute(
                    "UPDATE inventory SET stock_qty = stock_qty - ? WHERE sku = ?",
                    (qty, sku)
                )
            conn.commit()
            return order_id, seq_num


# Execution block: This runs only when the script is executed directly in the terminal
if __name__ == "__main__":
    db = DatabaseManager()
    print(f"✅ Database initialized successfully at: {db.db_path}")