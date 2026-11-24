from datetime import datetime

try:
    import win32print
except ImportError:
    win32print = None


class PrinterService:
    def __init__(self, printer_name: str = "POS-58"):
        self.printer_name = printer_name

    def format_receipt(self, seq_num: int, cart_items: list[dict], total_amount: float) -> str:
        """Formats the 58mm thermal receipt text for an order."""
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "--- PROJECTBB PLUS ---",
            f"Date: {date_str}",
            f"Queue Number: {seq_num}",
            "-" * 32,
        ]

        for item in cart_items:
            line_total = item["price"] * item["quantity"]
            lines.append(f"{item['quantity']}x {item['name']} - P{line_total:.2f}")

        lines.extend([
            "-" * 32,
            f"TOTAL: P{total_amount:.2f}",
            "Thank you for waiting!",
            "",
            "",
            "",
            "",
            "",
        ])
        return "\n".join(lines)

    def print_receipt(self, seq_num: int, cart_items: list[dict], total_amount: float) -> bool:
        """Sends the formatted receipt text directly to the configured Windows printer."""
        receipt_text = self.format_receipt(seq_num, cart_items, total_amount)

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