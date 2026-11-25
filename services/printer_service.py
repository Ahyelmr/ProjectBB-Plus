from datetime import datetime
import textwrap

try:
    import win32print
except ImportError:
    win32print = None


class PrinterService:
    RECEIPT_WIDTH = 32

    def __init__(self, printer_name: str = "POS-58"):
        self.printer_name = printer_name

    def format_receipt(
        self,
        seq_num: int,
        cart_items: list[dict],
        total_amount: float,
        discount_name: str = "None",
        amount_tendered: float | None = None,
        change_amount: float | None = None,
    ) -> str:
        """Formats the 58mm thermal receipt text for an order."""
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        divider = "-" * self.RECEIPT_WIDTH
        lines = [
            "--- PROJECTBB PLUS ---",
            f"Date: {date_str}",
            f"Queue Number: {seq_num}",
            divider,
        ]

        subtotal = 0.0
        for item in cart_items:
            line_total = item["price"] * item["quantity"]
            subtotal += line_total
            lines.append(f"{item['quantity']}x {item['name']} - P{line_total:.2f}")

        lines.append(divider)

        discount_amount = max(0.0, subtotal - total_amount)
        has_discount = bool(discount_name and discount_name != "None" and discount_amount > 0)

        if has_discount:
            lines.append(f"Subtotal: P{subtotal:.2f}")
            if "coupon" in discount_name.lower():
                lines.append("COUPON REDEEMED:")
                lines.extend(textwrap.wrap(discount_name, width=self.RECEIPT_WIDTH))
            else:
                lines.extend(textwrap.wrap(f"Discount: {discount_name}", width=self.RECEIPT_WIDTH))
            lines.append(f"Less: -P{discount_amount:.2f}")

        tendered = total_amount if amount_tendered is None else float(amount_tendered)
        change = (
            max(0.0, tendered - total_amount)
            if change_amount is None
            else max(0.0, float(change_amount))
        )

        lines.extend([
            f"TOTAL: P{total_amount:.2f}",
            f"Tendered: P{tendered:.2f}",
            f"Change: P{change:.2f}",
            divider,
            "Thank you for waiting!",
            "",
            "",
            "",
            "",
            "",
        ])
        return "\n".join(lines)

    def print_receipt(
        self,
        seq_num: int,
        cart_items: list[dict],
        total_amount: float,
        discount_name: str = "None",
        amount_tendered: float | None = None,
        change_amount: float | None = None,
    ) -> bool:
        """Sends the formatted receipt text directly to the configured Windows printer."""
        receipt_text = self.format_receipt(
            seq_num,
            cart_items,
            total_amount,
            discount_name=discount_name,
            amount_tendered=amount_tendered,
            change_amount=change_amount,
        )

        if win32print is None:
            print("Printer skipped: win32print is not available on this platform.")
            return False

        try:
            hprinter = win32print.OpenPrinter(self.printer_name)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("ProjectBB Receipt", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hprinter)
                    win32print.WritePrinter(hprinter, receipt_text.encode("utf-8"))
                    win32print.EndPagePrinter(hprinter)
                finally:
                    win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
            return True
        except Exception as e:
            print(f"Printer connection failed: {e}")
            return False