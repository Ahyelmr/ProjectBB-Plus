import customtkinter as ctk
from components.split_pane import VerticalSplitter


class LiveQueuePanel(ctk.CTkFrame):
    """Docked Live Kitchen Queue panel with Preparing and Ready for Pickup columns."""

    def __init__(self, parent, controller):
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
        self._prep_weight = 50
        self._ready_weight = 50
        self._refresh_job = None
        self._last_snapshot = None

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=self._prep_weight, minsize=120)
        self.grid_columnconfigure(1, weight=0, minsize=8)
        self.grid_columnconfigure(2, weight=self._ready_weight, minsize=120)

        self.queue_header = ctk.CTkLabel(
            self, text="Live Kitchen Queue", font=f["header"], text_color=c["text_main"]
        )
        self.queue_header.grid(row=0, column=0, columnspan=3, pady=(10, 4))

        self.prep_column = ctk.CTkScrollableFrame(
            self,
            label_text="Preparing",
            label_font=f["subheader"],
            label_fg_color=c["border"],
            label_text_color=c["accent_gold"],
            fg_color=c["bg_input"],
            border_width=1,
            border_color=c["border"],
            corner_radius=8,
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.prep_column.grid(row=1, column=0, sticky="nsew", padx=(8, 2), pady=(0, 8))

        self.splitter = VerticalSplitter(self, colors=c, on_drag=self._on_splitter_drag)
        self.splitter.grid(row=1, column=1, sticky="ns", pady=(4, 12))

        self.ready_column = ctk.CTkScrollableFrame(
            self,
            label_text="Ready for Pickup",
            label_font=f["subheader"],
            label_fg_color=c["border"],
            label_text_color=c["text_green"],
            fg_color=c["bg_input"],
            border_width=1,
            border_color=c["border"],
            corner_radius=8,
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.ready_column.grid(row=1, column=2, sticky="nsew", padx=(2, 8), pady=(0, 8))

    def _on_splitter_drag(self, _event) -> None:
        container_w = max(1, self.winfo_width())
        rel_x = self.winfo_pointerx() - self.winfo_rootx()
        ratio = max(0.25, min(0.75, rel_x / container_w))
        self._prep_weight = int(round(ratio * 100))
        self._ready_weight = 100 - self._prep_weight

        self.grid_columnconfigure(0, weight=self._prep_weight, minsize=120)
        self.grid_columnconfigure(2, weight=self._ready_weight, minsize=120)

    def refresh(self, force: bool = False) -> None:
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None

        orders = self.controller.db.get_active_orders(include_category=False)
        snapshot = tuple(
            (o["order_id"], o["status"], tuple(o["items"]))
            for o in orders
        )

        if force or snapshot != self._last_snapshot:
            self._last_snapshot = snapshot
            self._render_columns(orders)

        interval_sec = int(self.controller.settings.get("queue_refresh_sec", 5))
        if interval_sec > 0 and self.winfo_exists():
            self._refresh_job = self.after(interval_sec * 1000, self.refresh)

    def _render_columns(self, orders: list[dict]) -> None:
        c = self.controller.colors
        f = self.controller.fonts

        for widget in self.prep_column.winfo_children():
            widget.destroy()
        for widget in self.ready_column.winfo_children():
            widget.destroy()

        prep_orders = [o for o in orders if o["status"] in ("PREPARING", "PENDING")]
        ready_orders = [o for o in orders if o["status"] == "READY"]

        if not prep_orders:
            ctk.CTkLabel(
                self.prep_column, text="No orders preparing", font=f["small"], text_color=c["text_muted"]
            ).pack(pady=16)
        else:
            for order in prep_orders:
                self._create_prep_card(order["order_id"], order["sequence_number"], order["items"])

        if not ready_orders:
            ctk.CTkLabel(
                self.ready_column, text="No orders ready", font=f["small"], text_color=c["text_muted"]
            ).pack(pady=16)
        else:
            for order in ready_orders:
                self._create_ready_card(order["order_id"], order["sequence_number"], order["items"])

    def _create_prep_card(self, order_id: int, seq_num: int, items: list) -> None:
        c = self.controller.colors
        f = self.controller.fonts

        card = ctk.CTkFrame(
            self.prep_column,
            fg_color=c["bg_card"],
            border_width=1,
            border_color=c["accent_gold"],
            corner_radius=8,
        )
        card.pack(fill="x", padx=4, pady=4)

        ctk.CTkLabel(
            card, text=f"Order #{seq_num}", font=f["subheader"], text_color=c["accent_gold"]
        ).pack(anchor="w", padx=8, pady=(6, 2))

        items_text = "\n".join(f"• {qty}x {name}" for qty, name in items)
        ctk.CTkLabel(
            card, text=items_text, font=f["small"], text_color=c["text_main"], justify="left", anchor="w"
        ).pack(fill="x", padx=8, pady=(0, 6))

        ctk.CTkButton(
            card,
            text="Move to Ready",
            height=28,
            font=f["small"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=lambda oid=order_id, seq=seq_num: [
                self.controller.queue.mark_order_ready(oid, seq),
                self.refresh(force=True),
            ],
        ).pack(fill="x", padx=8, pady=(0, 8))

    def _create_ready_card(self, order_id: int, seq_num: int, items: list) -> None:
        c = self.controller.colors
        f = self.controller.fonts

        card = ctk.CTkFrame(
            self.ready_column,
            fg_color=c["bg_card"],
            border_width=1,
            border_color=c["text_green"],
            corner_radius=8,
        )
        card.pack(fill="x", padx=4, pady=4)

        ctk.CTkLabel(
            card, text=f"Order #{seq_num}", font=f["subheader"], text_color=c["text_green"]
        ).pack(anchor="w", padx=8, pady=(6, 2))

        items_text = "\n".join(f"• {qty}x {name}" for qty, name in items)
        ctk.CTkLabel(
            card, text=items_text, font=f["small"], text_color=c["text_main"], justify="left", anchor="w"
        ).pack(fill="x", padx=8, pady=(0, 6))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_row,
            text="Call",
            height=28,
            font=f["small"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda seq=seq_num: self.controller.tts.announce_order(seq),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 3))

        ctk.CTkButton(
            btn_row,
            text="Done",
            height=28,
            font=f["small"],
            fg_color=c["accent_green"],
            hover_color=c["green_hover"],
            text_color="#FFFFFF",
            command=lambda oid=order_id: [
                self.controller.queue.complete_order(oid),
                self.refresh(force=True),
            ],
        ).grid(row=0, column=1, sticky="ew", padx=(3, 0))

    def apply_theme(self) -> None:
        c = self.controller.colors
        self.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.queue_header.configure(text_color=c["text_main"])
        self.splitter.apply_theme(c)
        self.prep_column.configure(
            fg_color=c["bg_input"],
            label_fg_color=c["border"],
            label_text_color=c["accent_gold"],
            border_color=c["border"],
        )
        self.ready_column.configure(
            fg_color=c["bg_input"],
            label_fg_color=c["border"],
            label_text_color=c["text_green"],
            border_color=c["border"],
        )
        self.refresh(force=True)