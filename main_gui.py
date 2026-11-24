import customtkinter as ctk
from core import theme
from database.db_manager import DatabaseManager
from services.printer_service import PrinterService
from services.tts_service import TTSService
from services.queue_service import QueueService

from views.login_view import LoginFrame
from views.cashier.cashier_view import CashierFrame
from views.kitchen_view import KitchenFrame
from views.progress.progress_view import ProgressFrame
from views.inventory_view import InventoryFrame
from views.settings_view import SettingsFrame

ctk.set_default_color_theme("blue")


class ProjectBBApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ProjectBB Plus - POS System")
        self.geometry(theme.DEFAULT_GEOMETRY)
        self.minsize(*map(int, theme.MIN_GEOMETRY.split("x")))

        # Persisted display & usability settings
        self.settings = theme.load_settings()
        self.colors = theme.COLORS
        theme.apply_color_preset(self.colors, self.settings["theme_name"])
        ctk.set_widget_scaling(float(self.settings.get("ui_scaling", 1.0)))

        self.fonts = theme.get_fonts(self.settings["font_size"])
        self.font_metrics = theme.FONT_PRESETS[self.settings["font_size"]]

        # Core database & hardware services
        self.db = DatabaseManager()
        self.printer = PrinterService(printer_name="POS-58")
        self.tts = TTSService()
        self.queue = QueueService(self.db, printer_service=self.printer, tts_service=self.tts)
        self.current_user_role = None

        self.container = ctk.CTkFrame(self, fg_color=self.colors["bg_main"])
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for frame_cls in (
            LoginFrame,
            CashierFrame,
            KitchenFrame,
            ProgressFrame,
            InventoryFrame,
            SettingsFrame,
        ):
            frame = frame_cls(parent=self.container, controller=self)
            self.frames[frame_cls.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, page_name: str) -> None:
        frame = self.frames[page_name]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()

    def apply_preferences(self, new_settings: dict) -> None:
        """Applies font sizes, scaling, theme colors, and layout preferences across all frames."""
        self.settings.update(new_settings)
        theme.save_settings(self.settings)

        font_preset = self.settings["font_size"]
        self.font_metrics = theme.FONT_PRESETS[font_preset]
        theme.apply_font_preset(self.fonts, font_preset)

        theme.apply_color_preset(self.colors, self.settings["theme_name"])
        ctk.set_widget_scaling(float(self.settings.get("ui_scaling", 1.0)))

        self.container.configure(fg_color=self.colors["bg_main"])
        for frame in self.frames.values():
            if hasattr(frame, "apply_theme"):
                frame.apply_theme()
            if hasattr(frame, "on_settings_updated"):
                frame.on_settings_updated()


if __name__ == "__main__":
    app = ProjectBBApp()
    app.mainloop()