from services.printer_service import PrinterService
from services.tts_service import TTSService


class QueueService:
    """Coordinates checkout printing, kitchen status transitions, and voice paging."""

    def __init__(
        self,
        db_manager,
        printer_service: PrinterService | None = None,
        tts_service: TTSService | None = None,
        printer_name: str = "POS-58",
    ):
        self.db = db_manager
        self.printer = printer_service or PrinterService(printer_name=printer_name)
        self.tts = tts_service or TTSService()

    def process_new_transaction(
        self,
        cart_items: dict,
        total_amount: float,
        discount_applied: str = "None",
    ) -> tuple[int, int]:
        """Saves a new order, prints the thermal receipt, and returns (sequence_number, order_id)."""
        seq_num, order_id = self.db.create_order(cart_items, total_amount, discount_applied)

        receipt_items = [
            {
                "sku": sku,
                "name": data["name"],
                "price": data["price"],
                "quantity": data["qty"],
            }
            for sku, data in cart_items.items()
        ]
        self.printer.print_receipt(
            seq_num,
            receipt_items,
            total_amount,
            discount_name=discount_applied,
        )
        return seq_num, order_id

    def mark_order_ready(self, order_id: int, seq_num: int) -> None:
        """Marks an order as READY in the database and announces its sequence number."""
        if hasattr(self.db, "update_order_status"):
            self.db.update_order_status(order_id, "READY")
        else:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = 'READY' WHERE order_id = ?", (order_id,))
                conn.commit()
        self.announce_order(seq_num)

    def complete_order(self, order_id: int) -> None:
        """Marks an order as COMPLETED in the database."""
        if hasattr(self.db, "update_order_status"):
            self.db.update_order_status(order_id, "COMPLETED")
        else:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = 'COMPLETED' WHERE order_id = ?", (order_id,))
                conn.commit()

    def announce_order(self, seq_num: int) -> None:
        """Triggers voice paging for the specified order sequence number."""
        self.tts.announce_order(seq_num)

    def _play_announcement(self, seq_num: int) -> None:
        """Compatibility alias for legacy callers."""
        self.announce_order(seq_num)