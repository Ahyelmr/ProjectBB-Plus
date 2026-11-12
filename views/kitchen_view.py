import os
import sys
import customtkinter as ctk
from PIL import Image


def get_resource_path(relative_path):
    """Resolves asset paths for both standard execution and PyInstaller bundles."""
    if not relative_path:
        return ""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)


class KitchenFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=controller.colors["bg_main"])
        self.controller = controller
        self._last_logo_size = None

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0, 1), weight=1, uniform="kds_cols")

        # Top Navigation & Controls
        self.top_bar = ctk.CTkFrame(
            self, height=56, fg_color=self.controller.colors["bg_card"],
            corner_radius=12, border_width=1, border_color=self.controller.colors["border"]
        )
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        self.back_btn = ctk.CTkButton(
            self.top_bar,
            text="Back to Cashier",
            width=140,
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=lambda: [
                self.controller.frames["CashierFrame"].refresh_kitchen_queue(),
                controller.show_frame("CashierFrame")
            ]
        )
        self.back_btn.pack(side="left", padx=10, pady=10)

        # Centered Header Container (Logo + Title)
        self.header_center = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.header_center.pack(side="left", expand=True)

        self.logo_label = ctk.CTkLabel(self.header_center, text="")
        self._update_logo(44, 44)

        self.title_label = ctk.CTkLabel(
            self.header_center,
            text="Kitchen Display System (KDS)",
            font=self.controller.fonts["header"],
            text_color=self.controller.colors["text_main"]
        )
        self.title_label.pack(side="left", padx=6)

        self.refresh_btn = ctk.CTkButton(
            self.top_bar,
            text="Refresh Queue",
            width=120,
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["accent_gold"],
            hover_color=self.controller.colors["gold_hover"],
            command=self.load_orders
        )
        self.refresh_btn.pack(side="right", padx=10, pady=10)

        # Column 0: Orders Being Prepared
        self.prep_column = ctk.CTkScrollableFrame(
            self,
            label_text="Preparing",
            label_font=self.controller.fonts["header"],
            label_text_color=self.controller.colors["accent_gold"],
            fg_color=self.controller.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.controller.colors["border"]
        )
        self.prep_column.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # Column 1: Orders Ready for Pickup
        self.ready_column = ctk.CTkScrollableFrame(
            self,
            label_text="Ready for Pickup",
            label_font=self.controller.fonts["header"],
            label_text_color=self.controller.colors["accent_green"],
            fg_color=self.controller.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.controller.colors["border"]
        )
        self.ready_column.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)

        self.bind("<Configure>", self._on_resize)
        self.load_orders()

    def _on_resize(self, event):
        """Scales the KDS header logo proportionally to window height."""
        if event.height > 100:
            target = max(38, min(54, int(event.height * 0.06)))
            self._update_logo(target, target)

    def _update_logo(self, max_w, max_h):
        logo_path = get_resource_path("assets/logo.png")
        if not os.path.exists(logo_path):
            self.logo_label.pack_forget()
            return

        try:
            with Image.open(logo_path) as img:
                orig_w, orig_h = img.size
                ratio = min(max_w / orig_w, max_h / orig_h)
                new_size = (max(1, int(orig_w * ratio)), max(1, int(orig_h * ratio)))

                if new_size == self._last_logo_size:
                    return
                self._last_logo_size = new_size

                resized = img.resize(new_size, Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=resized, dark_image=resized, size=new_size)
                self.logo_label.configure(image=ctk_img)
                if not self.logo_label.winfo_ismapped():
                    self.logo_label.pack(side="left", before=self.title_label, padx=(0, 8))
        except Exception as e:
            print(f"Logo load error (KitchenFrame): {e}")

    def load_orders(self):
        """Clears and reloads Preparing and Ready for Pickup tickets separately."""
        for widget in self.prep_column.winfo_children():
            widget.destroy()
        for widget in self.ready_column.winfo_children():
            widget.destroy()

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT order_id, sequence_number, status
                FROM orders
                WHERE status IN ('PREPARING', 'PENDING', 'READY')
                ORDER BY sequence_number ASC
            """)
            orders = cursor.fetchall()

            for order in orders:
                order_id = order["order_id"]
                seq_num = order["sequence_number"]
                status = order["status"]

                cursor.execute("""
                    SELECT inventory.name, inventory.category, order_items.quantity
                    FROM order_items
                    JOIN inventory ON order_items.sku = inventory.sku
                    WHERE order_items.order_id = ?
                """, (order_id,))
                items = cursor.fetchall()

                item_text = "\n".join([f"{item['quantity']}x {item['name']} ({item['category']})" for item in items])

                if status in ("PREPARING", "PENDING"):
                    self.create_prep_card(order_id, seq_num, item_text)
                elif status == "READY":
                    self.create_ready_card(order_id, seq_num, item_text)

    def create_prep_card(self, order_id, seq_num, item_text):
        card = ctk.CTkFrame(
            self.prep_column, border_width=1, corner_radius=10,
            fg_color=self.controller.colors["bg_main"],
            border_color=self.controller.colors["border"]
        )
        card.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            card, text=f"Order #{seq_num}",
            font=self.controller.fonts["header"],
            text_color=self.controller.colors["accent_gold"]
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            card, text=item_text, justify="left",
            font=self.controller.fonts["body"],
            text_color=self.controller.colors["text_main"]
        ).pack(pady=5, padx=10)

        ctk.CTkButton(
            card,
            text="Move to Ready",
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=lambda: [
                self.controller.queue.mark_order_ready(order_id, seq_num),
                self.load_orders(),
                self.controller.frames["CashierFrame"].refresh_kitchen_queue()
            ]
        ).pack(pady=10)

    def create_ready_card(self, order_id, seq_num, item_text):
        card = ctk.CTkFrame(
            self.ready_column, border_width=1, corner_radius=10,
            fg_color=self.controller.colors["bg_main"],
            border_color=self.controller.colors["border"]
        )
        card.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            card, text=f"Order #{seq_num}",
            font=self.controller.fonts["header"],
            text_color=self.controller.colors["accent_green"]
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            card, text=item_text, justify="left",
            font=self.controller.fonts["body"],
            text_color=self.controller.colors["text_main"]
        ).pack(pady=5, padx=10)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Call (TTS)",
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            width=100,
            command=lambda: self.controller.queue._play_announcement(seq_num)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Done",
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["accent_green"],
            hover_color=self.controller.colors["green_hover"],
            width=100,
            command=lambda: [
                self.controller.queue.complete_order(order_id),
                self.load_orders(),
                self.controller.frames["CashierFrame"].refresh_kitchen_queue()
            ]
        ).pack(side="right", padx=5)