import csv
import sqlite3

SORT_CLAUSES = {
    "Name (Asc)": "name ASC",
    "Name (Desc)": "name DESC",
    "Price (Asc)": "price ASC",
    "Price (Desc)": "price DESC",
    "SKU Number": "sku ASC",
}


class InventoryRepository:
    def __init__(self, db_conn):
        self._conn = db_conn

    def sku_exists(self, sku: str) -> bool:
        clean_sku = sku.strip().upper()
        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM inventory WHERE UPPER(sku) = ?", (clean_sku,))
            return cursor.fetchone() is not None

    def get_categories(self) -> list[str]:
        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT category
                FROM inventory
                WHERE category IS NOT NULL AND TRIM(category) != ''
                ORDER BY category ASC
            """)
            return [row["category"] for row in cursor.fetchall()]

    def get_menu_items(
        self,
        category: str = "All Categories",
        sort_by: str = "Name (Asc)",
        search_query: str = "",
    ) -> list:
        order_clause = SORT_CLAUSES.get(sort_by, "name ASC")
        conditions = []
        params = []

        if category and category != "All Categories":
            conditions.append("category = ?")
            params.append(category)

        clean_query = (search_query or "").strip().lower()
        if clean_query:
            conditions.append("(LOWER(name) LIKE ? OR LOWER(sku) LIKE ?)")
            like_pattern = f"%{clean_query}%"
            params.extend([like_pattern, like_pattern])

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT sku, name, price, category, image_path FROM inventory "
                f"{where_sql} ORDER BY {order_clause}",
                tuple(params),
            )
            return cursor.fetchall()

    def add_item(
        self, sku: str, name: str, price: float, category: str, image_path: str = ""
    ) -> tuple[bool, str]:
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
            with self._conn.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO inventory (sku, name, price, category, image_path)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (clean_sku, clean_name, numeric_price, clean_category, clean_image),
                )
                conn.commit()
            return True, f"'{clean_name}' ({clean_sku}) has been saved to the menu."
        except sqlite3.Error as e:
            return False, f"Database error: {e}"

    def import_from_csv(self, filepath: str) -> None:
        with open(filepath, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            with self._conn.get_connection() as conn:
                cursor = conn.cursor()
                for row in reader:
                    sku = row.get("sku") or row.get("SKU")
                    name = row.get("name") or row.get("Name")
                    price_raw = row.get("price") or row.get("Price")
                    category = row.get("category") or row.get("Category")
                    image_path = row.get("image_path") or row.get("Image Path") or ""

                    if sku and name and price_raw is not None and category:
                        try:
                            price = float(price_raw)
                            cursor.execute(
                                "INSERT OR REPLACE INTO inventory (sku, name, price, category, image_path) "
                                "VALUES (?, ?, ?, ?, ?)",
                                (sku.strip().upper(), name.strip(), price, category.strip(), image_path.strip()),
                            )
                        except ValueError:
                            continue
                conn.commit()