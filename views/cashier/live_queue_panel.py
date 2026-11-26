from tkinter import messagebox
import customtkinter as ctk
from components.split_pane import VerticalSplitter


class LiveQueuePanel(ctk.CTkFrame):
    """Docked Live Kitchen Queue panel with separate Dine-In and Takeout queues."""

    QUEUE_DINE_IN = "DINE IN"
    QUEUE_TAKEOUT = "TAKE OUT"
    QUEUE_LABELS = {
        QUEUE_DINE_IN: "Dine-In",
        QUEUE_TAKEOUT: "Takeout",
    }

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
        self._last_orders: list[dict] = []
        self._active_filter = "ALL"  # "ALL" | "DINE IN" | "TAKE OUT"

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=self._prep_weight, minsize=120)
        self.grid_columnconfigure(1, weight=0, minsize=8)
        self.grid_columnconfigure(2, weight=self._ready_weight, minsize=120)

        # --- Row 0: Top Panel Header + Total Active Badge ---
        self.header_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.header_bar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 4))

        self.queue_header = ctk.CTkLabel(
            self.header_bar,
            text="Live Kitchen Queue",
            font=f["header"],
            text_color=c["text_main"],
        )
        self.queue_header.pack(side="left")

        self.total_badge_frame, self.total_badge_label = self._build_badge(
            self.header_bar,
            text="0 Active",
            fg_color=c["bg_input"],
            text_color=c["text_muted"],
            border_color=c["border"],
        )
        self.total_badge_frame.pack(side="right")

        # --- Row 1: Queue Filter Tabs (All / Dine-In / Takeout) ---
        self.filter_bar = ctk.CTkFrame(
            self,
            fg_color=c["bg_input"],
            corner_radius=8,
            border_width=1,
            border_color=c["border"],
        )
        self.filter_bar.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 6))
        self.filter_bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.filter_buttons: dict[str, ctk.CTkButton] = {}
        for col, (key, label) in enumerate(
            [("ALL", "All (0)"), (self.QUEUE_DINE_IN, "Dine-In (0)"), (self.QUEUE_TAKEOUT, "Takeout (0)")]
        ):
            btn = ctk.CTkButton(
                self.filter_bar,
                text=label,
                height=26,
                corner_radius=6,
                font=f["small"],
                command=lambda k=key: self._set_queue_filter(k),
            )
            btn.grid(row=0, column=col, sticky="ew", padx=3, pady=3)
            self.filter_buttons[key] = btn

        # --- Row 2: Column Headers + Count Badges ---
        self.prep_header = ctk.CTkFrame(self, fg_color=c["border"], corner_radius=8, height=32)
        self.prep_header.grid(row=2, column=0, sticky="ew", padx=(8, 2), pady=(0, 4))
        self.prep_header.pack_propagate(False)

        self.prep_header_label = ctk.CTkLabel(
            self.prep_header,
            text="Preparing",
            font=f["subheader"],
            text_color=c["accent_gold"],
        )
        self.prep_header_label.pack(side="left", padx=(10, 4))

        self.prep_count_frame, self.prep_count_label = self._build_badge(
            self.prep_header,
            text="0",
            fg_color=c["accent_gold"],
            text_color=c["text_on_gold"],
        )
        self.prep_count_frame.pack(side="right", padx=(4, 8))

        self.ready_header = ctk.CTkFrame(self, fg_color=c["border"], corner_radius=8, height=32)
        self.ready_header.grid(row=2, column=2, sticky="ew", padx=(2, 8), pady=(0, 4))
        self.ready_header.pack_propagate(False)

        self.ready_header_label = ctk.CTkLabel(
            self.ready_header,
            text="Ready for Pickup",
            font=f["subheader"],
            text_color=c["text_green"],
        )
        self.ready_header_label.pack(side="left", padx=(10, 4))

        self.ready_count_frame, self.ready_count_label = self._build_badge(
            self.ready_header,
            text="0",
            fg_color=c["accent_green"],
            text_color="#FFFFFF",
        )
        self.ready_count_frame.pack(side="right", padx=(4, 8))

        # --- Row 3: Scrollable Columns + Splitter ---
        self.prep_column = ctk.CTkScrollableFrame(
            self,
            fg_color=c["bg_input"],
            border_width=1,
            border_color=c["border"],
            corner_radius=8,
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.prep_column.grid(row=3, column=0, sticky="nsew", padx=(8, 2), pady=(0, 8))

        self.splitter = VerticalSplitter(self, colors=c, on_drag=self._on_splitter_drag)
        self.splitter.grid(row=2, column=1, rowspan=2, sticky="ns", pady=(4, 12))

        self.ready_column = ctk.CTkScrollableFrame(
            self,
            fg_color=c["bg_input"],
            border_width=1,
            border_color=c["border"],
            corner_radius=8,
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.ready_column.grid(row=3, column=2, sticky="nsew", padx=(2, 8), pady=(0, 8))

        self._style_filter_buttons(0, 0)

    def _badge_font(self):
        f = self.controller.fonts
        return f.get("badge", f["small"])

    def _build_badge(
        self,
        parent,
        text: str,
        fg_color: str,
        text_color: str,
        border_color: str | None = None,
    ) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
        frame_kwargs = {
            "fg_color": fg_color,
            "corner_radius": 10,
            "border_width": 1 if border_color else 0,
        }
        if border_color:
            frame_kwargs["border_color"] = border_color

        pill = ctk.CTkFrame(parent, **frame_kwargs)
        label = ctk.CTkLabel(
            pill,
            text=text,
            font=self._badge_font(),
            text_color=text_color,
            height=18,
        )
        label.pack(padx=7, pady=1)
        return pill, label

    @classmethod
    def _normalize_order_type(cls, order: dict) -> str:
        raw = (
            order.get("order_type")
            or order.get("dining_option")
            or order.get("service_type")
            or cls.QUEUE_DINE_IN
        )
        cleaned = " ".join(str(raw).strip().upper().replace("-", " ").replace("_", " ").split())
        if cleaned in ("TAKE OUT", "TAKEOUT", "TO", "TO GO", "TOGO", "TAKEAWAY", "TAKE AWAY"):
            return cls.QUEUE_TAKEOUT
        return cls.QUEUE_DINE_IN

    @classmethod
    def _format_order_code(cls, order: dict, queue_key: str) -> str:
        if order.get("order_code"):
            return order["order_code"]
        prefix = "TO" if queue_key == cls.QUEUE_TAKEOUT else "DI"
        return f"{prefix} {int(order['sequence_number']):03d}"

    def _queue_badge_colors(self, queue_key: str) -> tuple[str, str]:
        c = self.controller.colors
        if queue_key == self.QUEUE_TAKEOUT:
            return c["accent_gold"], c["text_on_gold"]
        return c["primary"], "#FFFFFF"

    def _set_queue_filter(self, filter_key: str) -> None:
        if filter_key == self._active_filter:
            return
        self._active_filter = filter_key
        self._render_columns(self._last_orders)

    def _style_filter_buttons(self, dine_in_count: int, takeout_count: int) -> None:
        c = self.controller.colors
        total_count = dine_in_count + takeout_count
        labels = {
            "ALL": f"All ({total_count})",
            self.QUEUE_DINE_IN: f"Dine-In ({dine_in_count})",
            self.QUEUE_TAKEOUT: f"Takeout ({takeout_count})",
        }

        for key, btn in self.filter_buttons.items():
            is_active = key == self._active_filter
            if is_active:
                if key == self.QUEUE_TAKEOUT:
                    fg, hover, txt = c["accent_gold"], c["gold_hover"], c["text_on_gold"]
                else:
                    fg, hover, txt = c["primary"], c["primary_hover"], "#FFFFFF"
            else:
                fg, hover, txt = "transparent", c["border"], c["text_muted"]

            btn.configure(
                text=labels[key],
                fg_color=fg,
                hover_color=hover,
                text_color=txt,
            )

    def _on_splitter_drag(self, _event) -> None:
        container_w = max(1, self.winfo_width())
        rel_x = self.winfo_pointerx() - self.winfo_rootx()
        ratio = max(0.25, min(0.75, rel_x / container_w))
        self._prep_weight = int(round(ratio * 100))
        self._ready_weight = 100 - self._prep_weight

        self.grid_columnconfigure(0, weight=self._prep_weight, minsize=120)
        self.grid_columnconfigure(2, weight=self._ready_weight, minsize=120)

    def refresh(self, force: bool = False) -> None:
        if not self.winfo_exists():
            return

        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None

        orders = self.controller.db.get_active_orders(include_category=False)
        snapshot = tuple(
            (
                o["order_id"],
                o["sequence_number"],
                self._normalize_order_type(o),
                o["status"],
                tuple(o["items"]),
            )
            for o in orders
        )

        if force or snapshot != self._last_snapshot:
            self._last_snapshot = snapshot
            self._last_orders = orders
            self._render_columns(orders)

        interval_sec = int(self.controller.settings.get("queue_refresh_sec", 5))
        if interval_sec > 0 and self.winfo_exists():
            self._refresh_job = self.after(interval_sec * 1000, self.refresh)

    def _update_header_badges(
        self, total_active: int, prep_count: int, ready_count: int
    ) -> None:
        c = self.controller.colors

        self.total_badge_label.configure(
            text=f"{total_active} Active",
            text_color="#FFFFFF" if total_active > 0 else c["text_muted"],
        )
        self.total_badge_frame.configure(
            fg_color=c["primary"] if total_active > 0 else c["bg_input"],
            border_color=c["primary"] if total_active > 0 else c["border"],
        )

        self.prep_count_label.configure(
            text=str(prep_count),
            text_color=c["text_on_gold"] if prep_count > 0 else c["text_muted"],
        )
        self.prep_count_frame.configure(
            fg_color=c["accent_gold"] if prep_count > 0 else c["bg_input"],
        )

        self.ready_count_label.configure(
            text=str(ready_count),
            text_color="#FFFFFF" if ready_count > 0 else c["text_muted"],
        )
        self.ready_count_frame.configure(
            fg_color=c["accent_green"] if ready_count > 0 else c["bg_input"],
        )

    def _render_columns(self, orders: list[dict]) -> None:
        for widget in self.prep_column.winfo_children():
            widget.destroy()
        for widget in self.ready_column.winfo_children():
            widget.destroy()

        active_orders = [o for o in orders if o["status"] in ("PENDING", "PREPARING", "READY")]
        dine_in_total = sum(1 for o in active_orders if self._normalize_order_type(o) == self.QUEUE_DINE_IN)
        takeout_total = sum(1 for o in active_orders if self._normalize_order_type(o) == self.QUEUE_TAKEOUT)
        self._style_filter_buttons(dine_in_total, takeout_total)

        if self._active_filter == "ALL":
            visible_orders = active_orders
        else:
            visible_orders = [
                o for o in active_orders if self._normalize_order_type(o) == self._active_filter
            ]

        prep_orders = [o for o in visible_orders if o["status"] in ("PREPARING", "PENDING")]
        ready_orders = [o for o in visible_orders if o["status"] == "READY"]

        self._update_header_badges(len(active_orders), len(prep_orders), len(ready_orders))

        self._render_column_queues(
            column=self.prep_column,
            orders=prep_orders,
            empty_suffix="preparing",
            card_builder=self._create_prep_card,
        )
        self._render_column_queues(
            column=self.ready_column,
            orders=ready_orders,
            empty_suffix="ready",
            card_builder=self._create_ready_card,
        )

    def _render_column_queues(
        self,
        column: ctk.CTkScrollableFrame,
        orders: list[dict],
        empty_suffix: str,
        card_builder,
    ) -> None:
        c = self.controller.colors
        f = self.controller.fonts

        if self._active_filter != "ALL":
            if not orders:
                queue_name = self.QUEUE_LABELS[self._active_filter]
                ctk.CTkLabel(
                    column,
                    text=f"No {queue_name} orders {empty_suffix}",
                    font=f["small"],
                    text_color=c["text_muted"],
                ).pack(pady=16)
                return

            ordered = sorted(orders, key=lambda o: (o["sequence_number"], o["order_id"]))
            for order in ordered:
                card_builder(order)
            return

        if not orders:
            ctk.CTkLabel(
                column,
                text=f"No orders {empty_suffix}",
                font=f["small"],
                text_color=c["text_muted"],
            ).pack(pady=16)
            return

        for queue_key in (self.QUEUE_DINE_IN, self.QUEUE_TAKEOUT):
            queue_orders = sorted(
                [o for o in orders if self._normalize_order_type(o) == queue_key],
                key=lambda o: (o["sequence_number"], o["order_id"]),
            )
            self._render_subqueue_header(column, queue_key, len(queue_orders))
            if not queue_orders:
                ctk.CTkLabel(
                    column,
                    text=f"No {self.QUEUE_LABELS[queue_key]} orders",
                    font=f["small"],
                    text_color=c["text_muted"],
                ).pack(pady=(2, 8))
            else:
                for order in queue_orders:
                    card_builder(order)

    def _render_subqueue_header(
        self, parent: ctk.CTkScrollableFrame, queue_key: str, count: int
    ) -> None:
        c = self.controller.colors
        f = self.controller.fonts
        badge_bg, badge_fg = self._queue_badge_colors(queue_key)

        bar = ctk.CTkFrame(
            parent, fg_color=c["bg_card"], corner_radius=6, border_width=1, border_color=c["border"]
        )
        bar.pack(fill="x", padx=4, pady=(6, 2))

        ctk.CTkLabel(
            bar,
            text=f"{self.QUEUE_LABELS[queue_key]} Queue",
            font=f["small"],
            text_color=c["text_main"],
        ).pack(side="left", padx=(8, 4), pady=3)

        pill, _ = self._build_badge(
            bar,
            text=str(count),
            fg_color=badge_bg if count > 0 else c["bg_input"],
            text_color=badge_fg if count > 0 else c["text_muted"],
        )
        pill.pack(side="right", padx=(4, 6), pady=3)

    def _render_card_badges(self, card: ctk.CTkFrame, queue_key: str, items: list) -> None:
        c = self.controller.colors
        meta_row = ctk.CTkFrame(card, fg_color="transparent")
        meta_row.pack(fill="x", padx=8, pady=(0, 6))

        type_bg, type_fg = self._queue_badge_colors(queue_key)
        type_pill, _ = self._build_badge(
            meta_row,
            text=queue_key,
            fg_color=type_bg,
            text_color=type_fg,
        )
        type_pill.pack(side="left", padx=(0, 4))

        total_qty = sum(qty for qty, *_ in items)
        qty_text = f"{total_qty} item" if total_qty == 1 else f"{total_qty} items"
        qty_pill, _ = self._build_badge(
            meta_row,
            text=qty_text,
            fg_color=c["bg_input"],
            text_color=c["text_muted"],
            border_color=c["border"],
        )
        qty_pill.pack(side="left")

    def _reprint_order(self, order_id: int, btn: ctk.CTkButton) -> None:
        if btn.winfo_exists():
            btn.configure(state="disabled", text="Printing...")

        success, message = self.controller.queue.reprint_order(order_id)
        if not btn.winfo_exists():
            return

        if success:
            btn.configure(text="Printed")
            self.after(
                1500,
                lambda b=btn: b.configure(state="normal", text="Reprint")
                if b.winfo_exists()
                else None,
            )
        else:
            btn.configure(state="normal", text="Reprint")
            messagebox.showwarning("Reprint Failed", message)

    def _mark_ready(self, order_id: int, seq_num: int, queue_key: str) -> None:
        self.controller.queue.mark_order_ready(order_id, seq_num, order_type=queue_key)
        self.refresh(force=True)

    def _announce_order(self, seq_num: int, queue_key: str) -> None:
        self.controller.tts.announce_order(seq_num, order_type=queue_key)

    def _complete_order(self, order_id: int) -> None:
        self.controller.queue.complete_order(order_id)
        self.refresh(force=True)

    def _create_prep_card(self, order: dict) -> None:
        c = self.controller.colors
        f = self.controller.fonts

        order_id = order["order_id"]
        seq_num = order["sequence_number"]
        status = order["status"]
        items = order["items"]
        queue_key = self._normalize_order_type(order)
        order_code = self._format_order_code(order, queue_key)

        is_pending = status == "PENDING"
        border_color = c["primary"] if is_pending else c["accent_gold"]
        badge_bg = c["primary"] if is_pending else c["accent_gold"]
        badge_fg = "#FFFFFF" if is_pending else c["text_on_gold"]
        badge_text = "PENDING" if is_pending else "PREPARING"

        card = ctk.CTkFrame(
            self.prep_column,
            fg_color=c["bg_card"],
            border_width=1,
            border_color=border_color,
            corner_radius=8,
        )
        card.pack(fill="x", padx=4, pady=4)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=8, pady=(6, 4))

        ctk.CTkLabel(
            top_row,
            text=order_code,
            font=f["subheader"],
            text_color=c["accent_gold"],
        ).pack(side="left")

        status_pill, _ = self._build_badge(
            top_row,
            text=badge_text,
            fg_color=badge_bg,
            text_color=badge_fg,
        )
        status_pill.pack(side="right")

        self._render_card_badges(card, queue_key, items)

        items_text = "\n".join(f"• {qty}x {name}" for qty, name, *_ in items) or "• No items"
        ctk.CTkLabel(
            card,
            text=items_text,
            font=f["small"],
            text_color=c["text_main"],
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=8, pady=(0, 6))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=2)

        reprint_btn = ctk.CTkButton(
            btn_row,
            text="Reprint",
            height=28,
            font=f["small"],
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_width=1,
            border_color=c["border"],
            text_color=c["text_main"],
        )
        reprint_btn.configure(
            command=lambda oid=order_id, b=reprint_btn: self._reprint_order(oid, b)
        )
        reprint_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        ctk.CTkButton(
            btn_row,
            text="Move to Ready",
            height=28,
            font=f["small"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=lambda oid=order_id, seq=seq_num, qk=queue_key: self._mark_ready(oid, seq, qk),
        ).grid(row=0, column=1, sticky="ew", padx=(3, 0))

    def _create_ready_card(self, order: dict) -> None:
        c = self.controller.colors
        f = self.controller.fonts

        order_id = order["order_id"]
        seq_num = order["sequence_number"]
        items = order["items"]
        queue_key = self._normalize_order_type(order)
        order_code = self._format_order_code(order, queue_key)

        card = ctk.CTkFrame(
            self.ready_column,
            fg_color=c["bg_card"],
            border_width=1,
            border_color=c["text_green"],
            corner_radius=8,
        )
        card.pack(fill="x", padx=4, pady=4)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=8, pady=(6, 4))

        ctk.CTkLabel(
            top_row,
            text=order_code,
            font=f["subheader"],
            text_color=c["text_green"],
        ).pack(side="left")

        status_pill, _ = self._build_badge(
            top_row,
            text="READY",
            fg_color=c["accent_green"],
            text_color="#FFFFFF",
        )
        status_pill.pack(side="right")

        self._render_card_badges(card, queue_key, items)

        items_text = "\n".join(f"• {qty}x {name}" for qty, name, *_ in items) or "• No items"
        ctk.CTkLabel(
            card,
            text=items_text,
            font=f["small"],
            text_color=c["text_main"],
            justify="left",
            anchor="w",
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
            command=lambda seq=seq_num, qk=queue_key: self._announce_order(seq, qk),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 3))

        ctk.CTkButton(
            btn_row,
            text="Done",
            height=28,
            font=f["small"],
            fg_color=c["accent_green"],
            hover_color=c["green_hover"],
            text_color="#FFFFFF",
            command=lambda oid=order_id: self._complete_order(oid),
        ).grid(row=0, column=1, sticky="ew", padx=(3, 0))

    def apply_theme(self) -> None:
        c = self.controller.colors
        self.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.queue_header.configure(text_color=c["text_main"])
        self.filter_bar.configure(fg_color=c["bg_input"], border_color=c["border"])
        self.splitter.apply_theme(c)

        self.prep_header.configure(fg_color=c["border"])
        self.prep_header_label.configure(text_color=c["accent_gold"])
        self.ready_header.configure(fg_color=c["border"])
        self.ready_header_label.configure(text_color=c["text_green"])

        self.prep_column.configure(
            fg_color=c["bg_input"],
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.ready_column.configure(
            fg_color=c["bg_input"],
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.refresh(force=True)