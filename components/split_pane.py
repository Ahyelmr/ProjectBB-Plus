import customtkinter as ctk


class VerticalSplitter(ctk.CTkFrame):
    """Draggable vertical divider handle with hover color feedback."""

    def __init__(self, parent, colors: dict, on_drag, on_release=None, width: int = 6):
        self._idle_color = colors["border"]
        self._hover_color = colors["primary"]
        super().__init__(
            parent,
            width=width,
            fg_color=self._idle_color,
            corner_radius=3,
            cursor="sb_h_double_arrow",
        )
        self.bind("<Enter>", lambda _e: self.configure(fg_color=self._hover_color))
        self.bind("<Leave>", lambda _e: self.configure(fg_color=self._idle_color))
        self.bind("<B1-Motion>", on_drag)
        if on_release:
            self.bind("<ButtonRelease-1>", on_release)

    def apply_theme(self, colors: dict) -> None:
        self._idle_color = colors["border"]
        self._hover_color = colors["primary"]
        self.configure(fg_color=self._idle_color)