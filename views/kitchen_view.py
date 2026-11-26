import customtkinter as ctk
from components.page_header import PageHeader


class KitchenFrame(ctk.CTkFrame):
    QUEUE_DINE_IN = "DINE IN"
    QUEUE_TAKEOUT = "TAKE OUT"
    QUEUE_LABELS = {
        QUEUE_DINE_IN: "Dine-In",
        QUEUE_TAKEOUT: "Takeout",
    }

    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller
        self._active_filter = "ALL"  # "ALL" | "DINE IN" | "TAKE OUT"
        self._last_orders: list[dict] = []

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure((0, 1), weight=1, uniform="kds_cols")

        # Row 0: Page Header
        self.header = PageHeader(
            self,
            controller=controller,
            title="Kitchen Display System (KDS)",
            back_command=self._go_back,
            logo_size=44,
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))

        self.refresh_btn = ctk.CTkButton(
            self.header.right_slot,
            text="Refresh Queue",
            width=135,
            height=36,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=self.load_orders,
        )
        self.refresh_btn.pack()

        # Row 1: Queue Filter Tabs (All / Dine-In / Takeout)
        self.filter_bar = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=c["border"],
        )
        self.filter_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(2, 6))
        self.filter_bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.filter_buttons: dict[str, ctk.CTkButton] = {}
        for col, (key, label) in enumerate(
            [("ALL", "All Queues (0)"), (self.QUEUE_DINE_IN, "Dine-In (0)"), (self.QUEUE_TAKEOUT, "Takeout (0)")]
        ):
            btn = ctk.CTkButton(
                self.filter_bar,
                text=label,
                height=32,
                corner_radius=8,
                font=f["button"],
                command=lambda k=key: self._set_queue_filter(k),
            )
            btn.grid(row=0, column=col, sticky="ew", padx=4, pady=4)
            self.filter_buttons[key] = btn

        # Row 2 & 3: Preparing and Ready Columns with Count Badges
        (
            self.prep_header,
            self.prep_header_label,
            self.prep_count_frame,
            self.prep_count_label,
            self.prep_column,
        ) = self._create_column("Preparing", c["accent_gold"], c["accent_gold"], c["text_on_gold"], col=0, padx=(10, 5))

        (
            self.ready_header,
            self.ready_header_label,
            self.ready_count_frame,
            self.ready_count_label,
            self.ready_column,
        ) = self._create_column("Ready for Pickup", c["text_green"], c["accent_green"], "#FFFFFF", col=1, padx=(5, 10))

        self.bind("<Configure>", lambda e: self.header.scale_logo_for_height(e.height, 38, 54, 0.06))
        self.load_orders()

    @classmethod
    def _normalize_order_type(cls, order_type: str | None) -> str:
        norm = " ".join((order_type or cls.QUEUE_DINE_IN).strip().upper().replace("-", " ").replace("_", " ").split())
        if norm in ("TAKE OUT", "TAKEOUT", "TO", "TO GO", "TOGO", "TAKEAWAY", "TAKE AWAY"):
            return cls.QUEUE_TAKEOUT
        return cls.QUEUE_DINE_IN

    @classmethod
    def _format_order_code(cls, order_type: str | None, seq_num: int) -> str:
        norm = cls._normalize_order_type(order_type)
        prefix = "TO" if norm == cls.QUEUE_TAKEOUT else "DI"
        return f"{prefix} {int(seq_num):03d}"

    def _badge_font(self):
        return self.controller.fonts.get("badge", self.controller.fonts["small"])

    def _build_badge(
        self,
        parent,
        text: str,
        fg_color: str,
        text_color: str,
        border_color: str | None = None,
    ) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
        kwargs = {
            "fg_color": fg_color,
            "corner_radius": 10,
            "border_width": 1 if border_color else 0,
        }
        if border_color:
            kwargs["border_color"] = border_color

        pill = ctk.CTkFrame(parent, **kwargs)
        label = ctk.CTkLabel(
            pill,
            text=text,
            font=self._badge_font(),
            text_color=text_color,
            height=20,
        )
        label.pack(padx=8, pady=1)
        return pill, label

    def _queue_badge_colors(self, queue_key: str) -> tuple[str, str]:
        c = self.controller.colors
        if queue_key == self.QUEUE_TAKEOUT:
            return c["accent_gold"], c["text_on_gold"]
        return c["primary"], "#FFFFFF"

    def _create_column(
        self,
        title: str,
        title_color: str,
        badge_bg: str,
        badge_fg: str,
        col: int,
        padx: tuple[int, int],
    ):
        c = self.controller.colors
        f = self.controller.fonts

        header = ctk.CTkFrame(self, fg_color=c["border"], corner_radius=10, height=38)
        header.grid(row=2, column=col, sticky="ew", padx=padx, pady=(2, 4))
        header.pack_propagate(False)

        header_label = ctk.CTkLabel(
            header, text=title, font=f["header"], text_color=title_color
        )
        header_label.pack(side="left", padx=(14, 6))

        count_frame, count_label = self._build_badge(
            header, text="0", fg_color=badge_bg, text_color=badge_fg
        )
        count_frame.pack(side="right", padx=(6, 12))

        column = ctk.CTkScrollableFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        column.grid(row=3, column=col, sticky="nsew", padx=padx, pady=(0, 10))
        return header, header_label, count_frame, count_label, column

    def _set_queue_filter(self, filter_key: str) -> None:
        if filter_key == self._active_filter:
            return
        self._active_filter = filter_key
        self._render_orders(self._last_orders)

    def _style_filter_buttons(self, dine_in_count: int, takeout_count: int) -> None:
        c = self.controller.colors
        total_count = dine_in_count + takeout_count
        labels = {
            "ALL": f"All Queues ({total_count})",
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

            btn.configure(text=labels[key], fg_color=fg, hover_color=hover, text_color=txt)

    def _go_back(self):
        self.controller.frames["CashierFrame"].refresh_kitchen_queue(force=True)
        self.controller.show_frame("CashierFrame")

    def on_show(self):
        self.load_orders()

    def _fetch_active_orders(self) -> list[dict]:
        if hasattr(self.controller.db, "get_active_orders"):
            return self.controller.db.get_active_orders(include_category=True)

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    orders.order_id,
                    orders.sequence_number,
                    COALESCE(orders.order_type, 'DINE IN') AS order_type,
                    orders.status,
                    order_items.quantity,
                    inventory.name AS item_name,
                    inventory.category
                FROM orders
                JOIN order_items ON orders.order_id = order_items.order_id
                JOIN inventory ON order_items.sku = inventory.sku
                WHERE orders.status IN ('PREPARING', 'PENDING', 'READY')
                ORDER BY orders.order_id ASC, order_items.item_id ASC
            """)
            rows = cursor.fetchall()

        orders_map = {}
        for row in rows:
            oid = row["order_id"]
            if oid not in orders_map:
                otype = self._normalize_order_type(row["order_type"])
                orders_map[oid] = {
                    "order_id": oid,
                    "sequence_number": row["sequence_number"],
                    "order_type": otype,
                    "order_code": self._format_order_code(otype, row["sequence_number"]),
                    "status": row["status"],
                    "items": [],
                }
            orders_map[oid]["items"].append((row["quantity"], row["item_name"], row["category"]))
        return list(orders_map.values())

    def load_orders(self):
        self._last_orders = self._fetch_active_orders()
        self._render_orders(self._last_orders)

    def _render_orders(self, orders: list[dict]) -> None:
        c = self.controller.colors

        for widget in self.prep_column.winfo_children():
            widget.destroy()
        for widget in self.ready_column.winfo_children():
            widget.destroy()

        active_orders = [o for o in orders if o["status"] in ("PREPARING", "PENDING", "READY")]
        dine_in_total = sum(
            1 for o in active_orders if self._normalize_order_type(o.get("order_type")) == self.QUEUE_DINE_IN
        )
        takeout_total = sum(
            1 for o in active_orders if self._normalize_order_type(o.get("order_type")) == self.QUEUE_TAKEOUT
        )
        self._style_filter_buttons(dine_in_total, takeout_total)

        if self._active_filter == "ALL":
            visible_orders = active_orders
        else:
            visible_orders = [
                o
                for o in active_orders
                if self._normalize_order_type(o.get("order_type")) == self._active_filter
            ]

        prep_orders = [o for o in visible_orders if o["status"] in ("PREPARING", "PENDING")]
        ready_orders = [o for o in visible_orders if o["status"] == "READY"]

        self.prep_count_label.configure(
            text=str(len(prep_orders)),
            text_color=c["text_on_gold"] if prep_orders else c["text_muted"],
        )
        self.prep_count_frame.configure(
            fg_color=c["accent_gold"] if prep_orders else c["bg_input"]
        )

        self.ready_count_label.configure(
            text=str(len(ready_orders)),
            text_color="#FFFFFF" if ready_orders else c["text_muted"],
        )
        self.ready_count_frame.configure(
            fg_color=c["accent_green"] if ready_orders else c["bg_input"]
        )

        self._render_column_queues(self.prep_column, prep_orders, "preparing", self._create_prep_card)
        self._render_column_queues(self.ready_column, ready_orders, "ready", self._create_ready_card)

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
                    font=f["body"],
                    text_color=c["text_muted"],
                ).pack(pady=20)
                return

            for order in sorted(orders, key=lambda o: (o["sequence_number"], o["order_id"])):
                card_builder(order)
            return

        if not orders:
            ctk.CTkLabel(
                column,
                text=f"No orders {empty_suffix}",
                font=f["body"],
                text_color=c["text_muted"],
            ).pack(pady=20)
            return

        for queue_key in (self.QUEUE_DINE_IN, self.QUEUE_TAKEOUT):
            queue_orders = sorted(
                [o for o in orders if self._normalize_order_type(o.get("order_type")) == queue_key],
                key=lambda o: (o["sequence_number"], o["order_id"]),
            )
            self._render_subqueue_header(column, queue_key, len(queue_orders))
            if not queue_orders:
                ctk.CTkLabel(
                    column,
                    text=f"No {self.QUEUE_LABELS[queue_key]} orders",
                    font=f["small"],
                    text_color=c["text_muted"],
                ).pack(pady=(4, 10))
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
            parent, fg_color=c["bg_input"], corner_radius=8, border_width=1, border_color=c["border"]
        )
        bar.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            bar,
            text=f"{self.QUEUE_LABELS[queue_key]} Queue",
            font=f["subheader"],
            text_color=c["text_main"],
        ).pack(side="left", padx=(12, 6), pady=5)

        pill, _ = self._build_badge(
            bar,
            text=str(count),
            fg_color=badge_bg if count > 0 else c["bg_card"],
            text_color=badge_fg if count > 0 else c["text_muted"],
        )
        pill.pack(side="right", padx=(6, 10), pady=5)

    def _create_base_card(self, parent, order: dict, accent_color: str, status_text: str, status_bg: str, status_fg: str):
        c = self.controller.colors
        f = self.controller.fonts

        order_type = self._normalize_order_type(order.get("order_type"))
        order_code = order.get("order_code") or self._format_order_code(
            order_type, order["sequence_number"]
        )
        items = order["items"]
        item_lines = [
            f"{qty}x {name}  ({cat})" if cat else f"{qty}x {name}"
            for qty, name, *rest in items
            for cat in ([rest[0]] if rest else [""])
        ]
        item_text = "\n".join(item_lines)

        card = ctk.CTkFrame(
            parent,
            border_width=1,
            corner_radius=10,
            fg_color=c["bg_input"],
            border_color=accent_color,
        )
        card.pack(fill="x", padx=8, pady=6)

        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            header_row,
            text=order_code,
            font=f["header"],
            text_color=accent_color,
            anchor="w",
        ).pack(side="left")

        status_pill, _ = self._build_badge(
            header_row, text=status_text, fg_color=status_bg, text_color=status_fg
        )
        status_pill.pack(side="right")

        meta_row = ctk.CTkFrame(card, fg_color="transparent")
        meta_row.pack(fill="x", padx=14, pady=(0, 6))

        type_bg, type_fg = self._queue_badge_colors(order_type)
        type_pill, _ = self._build_badge(
            meta_row, text=order_type, fg_color=type_bg, text_color=type_fg
        )
        type_pill.pack(side="left", padx=(0, 6))

        total_qty = sum(qty for qty, *_ in items)
        qty_text = f"{total_qty} item" if total_qty == 1 else f"{total_qty} items"
        qty_pill, _ = self._build_badge(
            meta_row,
            text=qty_text,
            fg_color=c["bg_card"],
            text_color=c["text_muted"],
            border_color=c["border"],
        )
        qty_pill.pack(side="left")

        ctk.CTkLabel(
            card,
            text=item_text,
            justify="left",
            anchor="w",
            wraplength=420,
            font=f["body"],
            text_color=c["text_main"],
        ).pack(fill="x", padx=14, pady=(2, 10))
        return card

    def _create_prep_card(self, order: dict):
        c = self.controller.colors
        f = self.controller.fonts

        order_id = order["order_id"]
        seq_num = order["sequence_number"]
        order_type = self._normalize_order_type(order.get("order_type"))
        is_pending = order["status"] == "PENDING"

        accent = c["primary"] if is_pending else c["accent_gold"]
        status_text = "PENDING" if is_pending else "PREPARING"
        status_fg = "#FFFFFF" if is_pending else c["text_on_gold"]

        card = self._create_base_card(
            self.prep_column, order, accent, status_text, accent, status_fg
        )

        ctk.CTkButton(
            card,
            text="Move to Ready",
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda oid=order_id, seq=seq_num, otype=order_type: self._mark_ready(
                oid, seq, otype
            ),
        ).pack(fill="x", padx=14, pady=(0, 12))

    def _create_ready_card(self, order: dict):
        c = self.controller.colors
        f = self.controller.fonts

        order_id = order["order_id"]
        seq_num = order["sequence_number"]
        order_type = self._normalize_order_type(order.get("order_type"))

        card = self._create_base_card(
            self.ready_column, order, c["text_green"], "READY", c["accent_green"], "#FFFFFF"
        )

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame,
            text="Call (TTS)",
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda seq=seq_num, otype=order_type: self.controller.tts.announce_order(
                seq, order_type=otype
            ),
        ).grid(row=0, column=0, padx=4, sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="Done",
            height=36,
            font=f["button"],
            fg_color=c["accent_green"],
            hover_color=c["green_hover"],
            text_color="#FFFFFF",
            command=lambda oid=order_id: self._complete_order(oid),
        ).grid(row=0, column=1, padx=4, sticky="ew")

    def _mark_ready(self, order_id: int, seq_num: int, order_type: str = "DINE IN"):
        self.controller.queue.mark_order_ready(order_id, seq_num, order_type=order_type)
        self.load_orders()
        self.controller.frames["CashierFrame"].refresh_kitchen_queue(force=True)

    def _complete_order(self, order_id: int):
        self.controller.queue.complete_order(order_id)
        self.load_orders()
        self.controller.frames["CashierFrame"].refresh_kitchen_queue(force=True)

    def apply_theme(self):
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        self.header.apply_theme()
        self.filter_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.refresh_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.prep_header.configure(fg_color=c["border"])
        self.prep_header_label.configure(text_color=c["accent_gold"])
        self.ready_header.configure(fg_color=c["border"])
        self.ready_header_label.configure(text_color=c["text_green"])
        self.prep_column.configure(
            fg_color=c["bg_card"],
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.ready_column.configure(
            fg_color=c["bg_card"],
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.load_orders()