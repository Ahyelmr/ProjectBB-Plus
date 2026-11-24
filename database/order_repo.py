from datetime import datetime


class OrderRepository:
    def __init__(self, db_conn):
        self._conn = db_conn

    def get_next_sequence(self) -> int:
        today_str = datetime.now().strftime("%Y-%m-%d")
        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_sequence FROM daily_sequence WHERE date_str = ?", (today_str,))
            row = cursor.fetchone()

            if row:
                next_seq = row["last_sequence"] + 1
                cursor.execute(
                    "UPDATE daily_sequence SET last_sequence = ? WHERE date_str = ?",
                    (next_seq, today_str),
                )
            else:
                next_seq = 1
                cursor.execute(
                    "INSERT INTO daily_sequence (date_str, last_sequence) VALUES (?, ?)",
                    (today_str, next_seq),
                )

            conn.commit()
            return next_seq

    def create_order(self, cart_items: dict, total_amount: float, discount_applied: str = "None") -> tuple[int, int]:
        sequence_number = self.get_next_sequence()
        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO orders (sequence_number, order_date, total_amount, discount_applied, status)
                VALUES (?, ?, ?, ?, 'PREPARING')
                """,
                (sequence_number, order_date, total_amount, discount_applied),
            )
            order_id = cursor.lastrowid

            for sku, data in cart_items.items():
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, sku, quantity, price_per_unit)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, sku, data["qty"], data["price"]),
                )

            conn.commit()
            return sequence_number, order_id

    def update_order_status(self, order_id: int, status: str) -> None:
        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
            conn.commit()

    def get_active_orders(self, include_category: bool = False) -> list[dict]:
        """Returns all PREPARING, PENDING, and READY orders grouped with their line items."""
        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    orders.order_id,
                    orders.sequence_number,
                    orders.status,
                    order_items.quantity,
                    inventory.name AS item_name,
                    inventory.category
                FROM orders
                JOIN order_items ON orders.order_id = order_items.order_id
                JOIN inventory ON order_items.sku = inventory.sku
                WHERE orders.status IN ('PREPARING', 'PENDING', 'READY')
                ORDER BY orders.sequence_number ASC, orders.order_id ASC, order_items.item_id ASC
            """)
            rows = cursor.fetchall()

        orders_map = {}
        for row in rows:
            oid = row["order_id"]
            if oid not in orders_map:
                orders_map[oid] = {
                    "order_id": oid,
                    "sequence_number": row["sequence_number"],
                    "status": row["status"],
                    "items": [],
                }
            if include_category:
                orders_map[oid]["items"].append((row["quantity"], row["item_name"], row["category"]))
            else:
                orders_map[oid]["items"].append((row["quantity"], row["item_name"]))
        return list(orders_map.values())

    def get_daily_item_tally(self, date_str: str) -> list[tuple[str, int, float]]:
        """Returns [(item_name, total_qty, total_earned)] for COMPLETED orders on date_str."""
        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    inventory.name AS item_name,
                    SUM(order_items.quantity) AS total_qty,
                    SUM(order_items.quantity * COALESCE(order_items.price_per_unit, inventory.price)) AS total_earned
                FROM order_items
                JOIN orders ON order_items.order_id = orders.order_id
                JOIN inventory ON order_items.sku = inventory.sku
                WHERE orders.status = 'COMPLETED' AND orders.order_date LIKE ?
                GROUP BY inventory.name
                ORDER BY total_qty DESC, inventory.name ASC
                """,
                (date_str + "%",),
            )
            return [
                (row["item_name"], row["total_qty"], float(row["total_earned"] or 0.0))
                for row in cursor.fetchall()
            ]

    def get_daily_orders_sequence(self, date_str: str) -> list[dict]:
        """Returns all orders on date_str in sequence with line-item details."""
        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    orders.order_id,
                    orders.sequence_number,
                    orders.order_date,
                    orders.total_amount,
                    COALESCE(orders.discount_applied, 'None') AS discount_applied,
                    orders.status,
                    inventory.name AS item_name,
                    inventory.category AS category,
                    order_items.quantity,
                    COALESCE(order_items.price_per_unit, inventory.price) AS unit_price
                FROM orders
                JOIN order_items ON orders.order_id = order_items.order_id
                JOIN inventory ON order_items.sku = inventory.sku
                WHERE orders.order_date LIKE ?
                ORDER BY orders.sequence_number ASC, orders.order_id ASC, order_items.item_id ASC
                """,
                (date_str + "%",),
            )
            rows = cursor.fetchall()

        orders_map = {}
        for row in rows:
            oid = row["order_id"]
            if oid not in orders_map:
                orders_map[oid] = {
                    "order_id": oid,
                    "sequence_number": row["sequence_number"],
                    "order_date": row["order_date"],
                    "total_amount": row["total_amount"],
                    "discount_applied": row["discount_applied"],
                    "status": row["status"],
                    "items": [],
                }
            orders_map[oid]["items"].append({
                "name": row["item_name"],
                "category": row["category"],
                "quantity": row["quantity"],
                "unit_price": row["unit_price"],
                "line_total": row["quantity"] * row["unit_price"],
            })
        return list(orders_map.values())