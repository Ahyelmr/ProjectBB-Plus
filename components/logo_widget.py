import os
import customtkinter as ctk
from PIL import Image
from core.paths import get_resource_path


class LogoLabel(ctk.CTkLabel):
    """Displays assets/logo.png with cached aspect-ratio scaling."""

    def __init__(self, parent, relative_path: str = "assets/logo.png", initial_size: tuple[int, int] = (42, 42)):
        super().__init__(parent, text="")
        self._relative_path = relative_path
        self._last_size = None
        self._ctk_image = None
        self.has_logo = False
        self.set_max_size(*initial_size)

    def set_max_size(self, max_w: int, max_h: int) -> bool:
        """Resizes the logo proportionally to fit within (max_w, max_h)."""
        logo_path = get_resource_path(self._relative_path)
        if not os.path.exists(logo_path):
            self.has_logo = False
            self._ctk_image = None
            self.configure(image=None)
            return False

        try:
            with Image.open(logo_path) as img:
                orig_w, orig_h = img.size
                ratio = min(max_w / orig_w, max_h / orig_h)
                new_size = (max(1, int(orig_w * ratio)), max(1, int(orig_h * ratio)))

                if new_size == self._last_size and self.has_logo:
                    return True

                self._last_size = new_size
                resized = img.resize(new_size, Image.Resampling.LANCZOS)
                self._ctk_image = ctk.CTkImage(light_image=resized, dark_image=resized, size=new_size)
                self.configure(image=self._ctk_image)
                self.has_logo = True
                return True
        except Exception as e:
            print(f"Logo load error: {e}")
            return False