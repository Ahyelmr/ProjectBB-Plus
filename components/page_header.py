import customtkinter as ctk
from components.logo_widget import LogoLabel


class PageHeader(ctk.CTkFrame):
    """Standard top navigation bar shared across Kitchen, Settings, and Progress screens."""

    def __init__(
        self,
        parent,
        controller,
        title: str,
        back_command,
        back_text: str = "Back to Cashier",
        logo_size: int = 42,
    ):
        c = controller.colors
        f = controller.fonts
        super().__init__(
            parent,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        self.controller = controller
        self._last_logo_size = logo_size
        self._resize_job = None

        self.back_btn = ctk.CTkButton(
            self,
            text=back_text,
            width=145,
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=back_command,
        )
        self.back_btn.pack(side="left", padx=12, pady=10)

        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.pack(side="left", expand=True)

        self.logo = LogoLabel(self.center_frame, initial_size=(logo_size, logo_size))
        if self.logo.has_logo:
            self.logo.pack(side="left", padx=(0, 8))

        self.title_label = ctk.CTkLabel(
            self.center_frame,
            text=title,
            font=f["header"],
            text_color=c["text_main"],
        )
        self.title_label.pack(side="left", padx=6)

        self.right_slot = ctk.CTkFrame(self, fg_color="transparent")
        self.right_slot.pack(side="right", padx=12, pady=10)

    def scale_logo_for_height(
        self, height: int, min_px: int = 36, max_px: int = 52, ratio: float = 0.055
    ) -> None:
        if height <= 100 or not self.logo.has_logo:
            return

        target = max(min_px, min(max_px, int(height * ratio)))
        if target == self._last_logo_size:
            return

        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = self.after(60, lambda t=target: self._apply_logo_size(t))

    def _apply_logo_size(self, target: int) -> None:
        self._resize_job = None
        if not self.winfo_exists() or not self.logo.has_logo:
            return
        if target != self._last_logo_size:
            self._last_logo_size = target
            self.logo.set_max_size(target, target)

    def apply_theme(self) -> None:
        c = self.controller.colors
        self.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.title_label.configure(text_color=c["text_main"])
        self.back_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])