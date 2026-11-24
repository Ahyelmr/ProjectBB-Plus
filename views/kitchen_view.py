import customtkinter as ctk
from components.page_header import PageHeader


class KitchenFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0, 1), weight=1, uniform="kds_cols")

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

        self.prep_column = self._create_column("Preparing", c["accent_gold"], col=0, padx=(10, 5))
        self.ready_column = self._create_column("Ready for Pickup", c["text_green"], col=1, padx=(5, 10))

        self.bind("<Configure>", lambda e: self.header.scale_logo_for_height(e.height, 38, 54, 0.06))
        self.load_orders()

    def _create_column(self, title: str, title_color: str, col: int, padx: tuple[int, int]):
        c = self.controller.colors
        f = self.controller.fonts
        column = ctk.CTkScrollableFrame(
            self,
            label_text=title,
            label_font=f["header"],
            label_fg_color=c["border"],
            label_text_color=title_color,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        column.grid(row=1, column=col, sticky="nsew", padx=padx, pady=(5, 10))
        return column

    def _go_back(self):
        self.controller.frames["CashierFrame"].refresh_kitchen_queue(force=True)
        self.controller.show_frame("CashierFrame")

    def on_show(self):
        self.load_orders()

    def _fetch_active_orders(self) -> list[dict]:
        """Uses the repository method once Batch 3 is installed, with a direct fallback for now."""
        if hasattr(self.controller.db, "get_active_orders"):
            return self.controller.db.get_active_orders(include_category=True)

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    orders.order_id,
                    orders.sequence_number,
                    orders.status,
                    order_items.quantity,
                    inventory.name AS item_name,
                    inventory.category
                FROM orders
                JOIN order_items ON orders.order_id = order_items.order_id
                JOIN inventory ON order_items.sku = inventory.sku
                WHERE orders.status IN ('PREPARING', 'PENDING', 'READY')
                ORDER BY orders.sequence_number ASC, orders.order_id ASC, order_items.item_id ASC
            """)
            rows = cursor.fetchall()

        orders_map = {}
        for row in rows:
            oid = row["order_id"]
            if oid not in orders_map:
                orders_map[oid] = {
                    "order_id": oid,
                    "sequence_number": row["sequence_number"],
                    "status": row["status"],
                    "items": [],
                }
            orders_map[oid]["items"].append((row["quantity"], row["item_name"], row["category"]))
        return list(orders_map.values())

    def load_orders(self):
        for widget in self.prep_column.winfo_children():
            widget.destroy()
        for widget in self.ready_column.winfo_children():
            widget.destroy()

        for order in self._fetch_active_orders():
            item_lines = [
                f"{qty}x {name}  ({cat})" if cat else f"{qty}x {name}"
                for qty, name, cat in order["items"]
            ]
            item_text = "\n".join(item_lines)

            if order["status"] in ("PREPARING", "PENDING"):
                self._create_prep_card(order["order_id"], order["sequence_number"], item_text)
            elif order["status"] == "READY":
                self._create_ready_card(order["order_id"], order["sequence_number"], item_text)

    def _create_base_card(self, parent, seq_num: int, item_text: str, accent_color: str):
        c = self.controller.colors
        f = self.controller.fonts

        card = ctk.CTkFrame(
            parent,
            border_width=1,
            corner_radius=10,
            fg_color=c["bg_input"],
            border_color=accent_color,
        )
        card.pack(fill="x", padx=8, pady=6)

        ctk.CTkLabel(
            card, text=f"Order #{seq_num}", font=f["header"], text_color=accent_color, anchor="w"
        ).pack(fill="x", padx=14, pady=(10, 4))

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

    def _create_prep_card(self, order_id: int, seq_num: int, item_text: str):
        c = self.controller.colors
        f = self.controller.fonts
        card = self._create_base_card(self.prep_column, seq_num, item_text, c["accent_gold"])

        ctk.CTkButton(
            card,
            text="Move to Ready",
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda oid=order_id, seq=seq_num: self._mark_ready(oid, seq),
        ).pack(fill="x", padx=14, pady=(0, 12))

    def _create_ready_card(self, order_id: int, seq_num: int, item_text: str):
        c = self.controller.colors
        f = self.controller.fonts
        card = self._create_base_card(self.ready_column, seq_num, item_text, c["text_green"])

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
            command=lambda seq=seq_num: self.controller.tts.announce_order(seq),
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

    def _mark_ready(self, order_id: int, seq_num: int):
        self.controller.queue.mark_order_ready(order_id, seq_num)
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
        self.refresh_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.prep_column.configure(
            fg_color=c["bg_card"],
            border_color=c["border"],
            label_fg_color=c["border"],
            label_text_color=c["accent_gold"],
        )
        self.ready_column.configure(
            fg_color=c["bg_card"],
            border_color=c["border"],
            label_fg_color=c["border"],
            label_text_color=c["text_green"],
        )
        self.load_orders()