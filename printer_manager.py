import win32print
from datetime import datetime

class PrinterManager:
    def __init__(self, printer_name="POS-58"):
        self.printer_name = printer_name

    def print_receipt(self, seq_num, cart_items, total_amount):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        receipt_text = f"--- PROJECTBB PLUS ---\nDate: {date_str}\nQueue Number: {seq_num}\n" + "-" * 32 + "\n"
        
        for item in cart_items:
            line_total = item['price'] * item['quantity']
            receipt_text += f"{item['quantity']}x {item['name']} - P{line_total:.2f}\n"
            
        receipt_text += "-" * 32 + "\n"
        receipt_text += f"TOTAL: P{total_amount:.2f}\nThank you for waiting!\n\n\n\n\n"
        
        try:
            hprinter = win32print.OpenPrinter(self.printer_name)
            try:
                hjob = win32print.StartDocPrinter(hprinter, 1, ("ProjectBB Receipt", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hprinter)
                    win32print.WritePrinter(hprinter, receipt_text.encode('utf-8'))
                    win32print.EndPagePrinter(hprinter)
                finally:
                    win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
        except Exception as e:
            print(f"Printer connection failed: {e}")