import win32print
import time

def test_printer_latency(printer_name="POS-58"):
    print(f"Connecting to {printer_name}...")
    test_text = "--- LATENCY TEST ---\nHello ProjectBB Plus!\n" + "-" * 20 + "\n\n\n\n"
    
    try:
        # Start the high-resolution timer
        start_time = time.perf_counter()
        
        # Direct hardware print execution
        hprinter = win32print.OpenPrinter(printer_name)
        try:
            hjob = win32print.StartDocPrinter(hprinter, 1, ("Latency Test", None, "RAW"))
            try:
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, test_text.encode('utf-8'))
                win32print.EndPagePrinter(hprinter)
            finally:
                win32print.EndDocPrinter(hprinter)
        finally:
            win32print.ClosePrinter(hprinter)
            
        # Stop the timer and calculate milliseconds
        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000
        
        print(f"✅ Print successful!")
        print(f"⏱️ Print Execution Latency: {latency:.2f} ms")
        
    except Exception as e:
        print(f"❌ Printer connection failed: {e}\nVerify the printer is plugged in, turned on, and named exactly '{printer_name}' in Windows Settings.")

if __name__ == "__main__":
    test_printer_latency()