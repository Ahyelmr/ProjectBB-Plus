import threading
import queue


class TTSService:
    """Thread-safe FIFO voice paging service using Windows SAPI5 with pyttsx3 fallback."""

    def __init__(self, voice_index: int = 1, volume: int = 100, rate: int = -1):
        self.voice_index = voice_index
        self.volume = volume
        self.rate = rate
        self._audio_queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._audio_worker, daemon=True)
        self._worker_thread.start()

    def announce_order(self, seq_num: int | str, order_type: str | None = None) -> None:
        """Queues a pickup announcement including Dine In / Take Out and order number."""
        spoken_type = None
        parsed_num = seq_num

        if isinstance(seq_num, str):
            raw = seq_num.strip().upper()
            if raw.startswith("DI"):
                spoken_type = "Dine In"
                num_part = raw[2:].strip()
                parsed_num = int(num_part) if num_part.isdigit() else num_part
            elif raw.startswith("TO"):
                spoken_type = "Take Out"
                num_part = raw[2:].strip()
                parsed_num = int(num_part) if num_part.isdigit() else num_part
            elif raw.isdigit():
                parsed_num = int(raw)

        if order_type:
            norm = " ".join(order_type.strip().upper().replace("-", " ").replace("_", " ").split())
            if norm in ("TAKE OUT", "TAKEOUT", "TO", "TO GO", "TOGO", "TAKEAWAY", "TAKE AWAY"):
                spoken_type = "Take Out"
            elif norm in ("DINE IN", "DINEIN", "DI"):
                spoken_type = "Dine In"

        if spoken_type:
            self.speak(f"{spoken_type} {parsed_num} is ready for pickup.")
        else:
            self.speak(f"{parsed_num} is ready for pickup.")

    def speak(self, message: str) -> None:
        """Pushes any announcement string onto the background TTS queue."""
        if message:
            self._audio_queue.put(message)

    def _audio_worker(self) -> None:
        """Processes speech requests sequentially inside a thread-safe COM context."""
        while True:
            message = self._audio_queue.get()
            com_initialized = False
            try:
                try:
                    import pythoncom
                    import win32com.client

                    pythoncom.CoInitialize()
                    com_initialized = True

                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    voices = speaker.GetVoices()
                    if voices.Count > self.voice_index:
                        speaker.Voice = voices.Item(self.voice_index)

                    speaker.Volume = self.volume
                    speaker.Rate = self.rate
                    speaker.Speak(message)
                except Exception:
                    import pyttsx3

                    engine = pyttsx3.init()
                    voices = engine.getProperty("voices")
                    if len(voices) > self.voice_index:
                        engine.setProperty("voice", voices[self.voice_index].id)
                    engine.setProperty("volume", max(0.0, min(1.0, self.volume / 100.0)))
                    engine.setProperty("rate", 150)
                    engine.say(message)
                    engine.runAndWait()
            except Exception as e:
                print(f"Audio Paging Error: {e}")
            finally:
                if com_initialized:
                    try:
                        import pythoncom
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass
                self._audio_queue.task_done()