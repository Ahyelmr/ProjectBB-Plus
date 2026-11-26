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

    @staticmethod
    def _normalize_order_type(order_type: str | None) -> str:
        norm = (order_type or "DINE IN").strip().upper().replace("-", " ").replace("_", " ")
        norm = " ".join(norm.split())
        if norm in ("TAKE OUT", "TAKEOUT", "TO", "TO GO", "TOGO", "TAKEAWAY", "TAKE AWAY"):
            return "TAKE OUT"
        return "DINE IN"

    def _lookup_order_meta(self, order_id: int) -> tuple[int | None, str]:
        """Fetches (sequence_number, normalized_order_type) for an order_id."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sequence_number, COALESCE(order_type, 'DINE IN') AS order_type FROM orders WHERE order_id = ?",
                (order_id,),
            )
            row = cursor.fetchone()
            if row:
                return row["sequence_number"], self._normalize_order_type(row["order_type"])
        return None, "DINE IN"

    def process_new_transaction(
        self,
        cart_items: dict,
        total_amount: float,
        discount_applied: str = "None",
        amount_tendered: float | None = None,
        change_amount: float | None = None,
        order_type: str = "DINE IN",
    ) -> tuple[int, int]:
        """Saves a new order, prints the thermal receipt, and returns (sequence_number, order_id)."""
        norm_type = self._normalize_order_type(order_type)
        total_amount = round(float(total_amount), 2)
        if amount_tendered is None:
            amount_tendered = total_amount
        else:
            amount_tendered = round(float(amount_tendered), 2)

        if change_amount is None:
            change_amount = round(max(0.0, amount_tendered - total_amount), 2)
        else:
            change_amount = round(max(0.0, float(change_amount)), 2)

        seq_num, order_id = self.db.create_order(
            cart_items,
            total_amount,
            discount_applied,
            amount_tendered=amount_tendered,
            change_amount=change_amount,
            order_type=norm_type,
        )

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
            amount_tendered=amount_tendered,
            change_amount=change_amount,
            order_type=norm_type,
        )
        return seq_num, order_id

    def mark_order_ready(
        self,
        order_id: int,
        seq_num: int | None = None,
        order_type: str | None = None,
    ) -> None:
        """Marks an order as READY in the database and announces its order type & number."""
        if seq_num is None or order_type is None:
            db_seq, db_type = self._lookup_order_meta(order_id)
            if seq_num is None:
                seq_num = db_seq or 0
            if order_type is None:
                order_type = db_type
        else:
            order_type = self._normalize_order_type(order_type)

        if hasattr(self.db, "update_order_status"):
            self.db.update_order_status(order_id, "READY")
        else:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = 'READY' WHERE order_id = ?", (order_id,))
                conn.commit()
        self.announce_order(seq_num, order_type=order_type)

    def complete_order(self, order_id: int) -> None:
        """Marks an order as COMPLETED in the database."""
        if hasattr(self.db, "update_order_status"):
            self.db.update_order_status(order_id, "COMPLETED")
        else:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = 'COMPLETED' WHERE order_id = ?", (order_id,))
                conn.commit()

    def announce_order(self, seq_num: int | str, order_type: str | None = None) -> None:
        """Triggers voice paging for the specified order type and sequence number."""
        norm_type = self._normalize_order_type(order_type) if order_type else None
        self.tts.announce_order(seq_num, order_type=norm_type)

    def _play_announcement(self, seq_num: int | str, order_type: str | None = None) -> None:
        """Compatibility alias for legacy callers."""
        self.announce_order(seq_num, order_type=order_type)