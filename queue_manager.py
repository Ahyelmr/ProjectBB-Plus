import threading
import queue
import pythoncom
import win32com.client
from printer_manager import PrinterManager

class QueueManager:
    def __init__(self, db_manager, printer_name="POS-58"):
        self.db = db_manager
        self.printer = PrinterManager(printer_name=printer_name)
        
        # Thread-safe FIFO queue for speech requests
        self.audio_queue = queue.Queue()
        
        # Dedicated worker thread for TTS announcements
        self.audio_thread = threading.Thread(target=self._audio_worker, daemon=True)
        self.audio_thread.start()

    def process_new_transaction(self, cart_items, total_amount):
        order_id, seq_num = self.db.create_order(cart_items, total_amount)
        self.printer.print_receipt(seq_num, cart_items, total_amount)
        return order_id, seq_num

    def mark_order_ready(self, order_id, seq_num):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET status = 'READY' WHERE order_id = ?", (order_id,))
            conn.commit()
        self._play_announcement(seq_num)

    def complete_order(self, order_id):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET status = 'COMPLETED' WHERE order_id = ?", (order_id,))
            conn.commit()

    def _play_announcement(self, seq_num):
        """Pushes the sequence number to the audio worker queue."""
        self.audio_queue.put(seq_num)

    def _audio_worker(self):
        """
        Background worker that processes speech requests sequentially.
        Initializes COM runtime on each pass to guarantee thread-safe Windows SAPI5 playback.
        """
        while True:
            seq_num = self.audio_queue.get()
            try:
                # 1. Initialize COM library for the background thread
                pythoncom.CoInitialize()
                
                # 2. Native Windows SAPI5 dispatch (Fast, reliable, no loop locks)
                try:
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Speak(f"Order number {seq_num} is ready for pickup.")
                except Exception:
                    # Fallback using pyttsx3 inside the COM context
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty('volume', 1.0)
                    engine.setProperty('rate', 150)
                    engine.say(f"Order number {seq_num} is ready for pickup.")
                    engine.runAndWait()
            except Exception as e:
                print(f"Audio Paging Error: {e}")
            finally:
                # 3. Clean up COM runtime
                pythoncom.CoUninitialize()
                self.audio_queue.task_done()