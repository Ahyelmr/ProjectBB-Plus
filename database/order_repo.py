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

    def create_order(
        self,
        cart_items: dict,
        total_amount: float,
        discount_applied: str = "None",
        amount_tendered: float | None = None,
        change_amount: float | None = None,
    ) -> tuple[int, int]:
        sequence_number = self.get_next_sequence()
        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        total_amount = round(float(total_amount), 2)
        if amount_tendered is None:
            amount_tendered = total_amount
        else:
            amount_tendered = round(float(amount_tendered), 2)

        if change_amount is None:
            change_amount = round(max(0.0, amount_tendered - total_amount), 2)
        else:
            change_amount = round(max(0.0, float(change_amount)), 2)

        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO orders (
                    sequence_number,
                    order_date,
                    total_amount,
                    amount_tendered,
                    change_amount,
                    discount_applied,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'PREPARING')
                """,
                (
                    sequence_number,
                    order_date,
                    total_amount,
                    amount_tendered,
                    change_amount,
                    discount_applied,
                ),
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

    def get_available_order_dates(self) -> list[str]:
        """Returns distinct YYYY-MM-DD dates from orders (newest first), always including today."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT SUBSTR(order_date, 1, 10) AS date_str
                FROM orders
                WHERE order_date IS NOT NULL AND LENGTH(TRIM(order_date)) >= 10
                ORDER BY date_str DESC
                """
            )
            dates = [row["date_str"] for row in cursor.fetchall() if row["date_str"]]

        if today_str not in dates:
            dates.insert(0, today_str)
        return dates

    def delete_orders_by_date(self, date_str: str) -> tuple[bool, str]:
        """Permanently deletes all order_items, orders, and daily_sequence rows for a previous date."""
        clean_date = (date_str or "").strip()[:10]
        try:
            datetime.strptime(clean_date, "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid date format: '{date_str}'."

        today_str = datetime.now().strftime("%Y-%m-%d")
        if clean_date >= today_str:
            return False, "Only sales records from previous dates can be deleted."

        try:
            with self._conn.get_connection() as conn:
                cursor = conn.cursor()
                date_pattern = clean_date + "%"

                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM orders WHERE order_date LIKE ?",
                    (date_pattern,),
                )
                order_count = cursor.fetchone()["cnt"]

                if order_count == 0:
                    cursor.execute(
                        "DELETE FROM daily_sequence WHERE date_str = ?",
                        (clean_date,),
                    )
                    conn.commit()
                    return False, f"No sales records found for {clean_date}."

                cursor.execute(
                    """
                    DELETE FROM order_items
                    WHERE order_id IN (
                        SELECT order_id FROM orders WHERE order_date LIKE ?
                    )
                    """,
                    (date_pattern,),
                )
                cursor.execute(
                    "DELETE FROM orders WHERE order_date LIKE ?",
                    (date_pattern,),
                )
                cursor.execute(
                    "DELETE FROM daily_sequence WHERE date_str = ?",
                    (clean_date,),
                )
                conn.commit()

            return True, f"Deleted {order_count} sales order record(s) for {clean_date}."
        except Exception as e:
            return False, f"Failed to delete sales records: {e}"

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
                    COALESCE(orders.amount_tendered, orders.total_amount) AS amount_tendered,
                    COALESCE(orders.change_amount, 0.0) AS change_amount,
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
                    "amount_tendered": float(row["amount_tendered"]),
                    "change_amount": float(row["change_amount"]),
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