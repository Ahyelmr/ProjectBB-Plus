from database.connection import DatabaseConnection
from database.user_repo import UserRepository
from database.inventory_repo import InventoryRepository
from database.order_repo import OrderRepository


class DatabaseManager:
    """Unified facade delegating to domain-specific SQLite repositories."""

    def __init__(self, db_path: str | None = None):
        self.conn = DatabaseConnection(db_path=db_path)
        self.db_path = self.conn.db_path
        self.users = UserRepository(self.conn)
        self.inventory = InventoryRepository(self.conn)
        self.orders = OrderRepository(self.conn)

    def _get_connection(self):
        return self.conn.get_connection()

    # --- Users ---
    hash_password = staticmethod(UserRepository.hash_password)
    verify_password = staticmethod(UserRepository.verify_password)

    def create_user(self, username: str, password: str, role: str) -> tuple[bool, str]:
        return self.users.create_user(username, password, role)

    def authenticate_user(self, username: str, password: str) -> str | None:
        return self.users.authenticate_user(username, password)

    # --- Inventory ---
    def sku_exists(self, sku: str) -> bool:
        return self.inventory.sku_exists(sku)

    def get_inventory_categories(self) -> list[str]:
        return self.inventory.get_categories()

    def get_menu_items(self, category: str = "All Categories", sort_by: str = "Name (Asc)") -> list:
        return self.inventory.get_menu_items(category=category, sort_by=sort_by)

    def add_inventory_item(
        self, sku: str, name: str, price: float, category: str, image_path: str = ""
    ) -> tuple[bool, str]:
        return self.inventory.add_item(sku, name, price, category, image_path)

    def import_inventory_from_csv(self, filepath: str) -> None:
        self.inventory.import_from_csv(filepath)

    # --- Orders ---
    def get_next_sequence(self) -> int:
        return self.orders.get_next_sequence()

    def create_order(self, cart_items: dict, total_amount: float, discount_applied: str = "None") -> tuple[int, int]:
        return self.orders.create_order(cart_items, total_amount, discount_applied)

    def update_order_status(self, order_id: int, status: str) -> None:
        self.orders.update_order_status(order_id, status)

    def get_active_orders(self, include_category: bool = False) -> list[dict]:
        return self.orders.get_active_orders(include_category=include_category)

    def get_daily_item_tally(self, date_str: str) -> list[tuple[str, int, float]]:
        return self.orders.get_daily_item_tally(date_str)

    def get_daily_orders_sequence(self, date_str: str) -> list[dict]:
        return self.orders.get_daily_orders_sequence(date_str)