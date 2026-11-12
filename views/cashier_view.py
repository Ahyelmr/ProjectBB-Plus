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


class CashierFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=controller.colors["bg_main"])
        self.controller = controller
        self.cart = {}  # {sku: {'name': name, 'price': price, 'qty': qty, 'category': category}}
        self.current_total = 0.0
        self._last_logo_size = None

        # Main 3-Section Grid Layout
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=4, minsize=400)  # Left: Menu Grid
        self.grid_columnconfigure(1, weight=2, minsize=290)  # Middle: Current Order & Checkout
        self.grid_columnconfigure(2, weight=3, minsize=430)  # Right: Dual-Column Kitchen Queue

        # --- TOP BAR: Compact Logo + Sorting & Category Filter Controls ---
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

        self.logo_label = ctk.CTkLabel(self.top_bar, text="")
        self._update_logo(40, 40)

        ctk.CTkLabel(
            self.top_bar, text="Sort:",
            font=self.controller.fonts["body"],
            text_color=self.controller.colors["text_main"]
        ).pack(side="left", padx=(4, 4))

        self.sort_var = ctk.StringVar(value="Name (Asc)")
        self.sort_menu = ctk.CTkOptionMenu(
            self.top_bar,
            variable=self.sort_var,
            width=130,
            values=[
                "Name (Asc)", "Name (Desc)",
                "Price (Asc)", "Price (Desc)",
                "SKU Number"
            ],
            command=self.load_menu
        )
        self.sort_menu.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            self.top_bar, text="Category:",
            font=self.controller.fonts["body"],
            text_color=self.controller.colors["text_main"]
        ).pack(side="left", padx=(0, 4))

        self.category_var = ctk.StringVar(value="All Categories")
        self.category_menu = ctk.CTkOptionMenu(
            self.top_bar,
            variable=self.category_var,
            width=150,
            values=["All Categories"],
            command=self.load_menu
        )
        self.category_menu.pack(side="left", padx=(0, 5))

        # --- Left: Menu Grid ---
        self.menu_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.menu_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.menu_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # --- Center: Cart & Checkout Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(
            self, fg_color=self.controller.colors["bg_card"],
            corner_radius=12, border_width=1, border_color=self.controller.colors["border"]
        )
        self.sidebar_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=8, pady=10)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self.sidebar_frame, text="Current Order",
            font=self.controller.fonts["header"], text_color=self.controller.colors["text_main"]
        ).grid(row=0, column=0, pady=10)

        self.cart_list_frame = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.cart_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        # Discounts Dropdown
        self.discount_var = ctk.StringVar(value="None")
        self.discount_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            variable=self.discount_var,
            values=["None", "PWD (20%)", "Free Sandwich Coupon", "Free Meal Coupon"],
            command=lambda _: self.update_cart_display()
        )
        self.discount_menu.grid(row=3, column=0, pady=5, padx=15, sticky="ew")

        # Totals
        self.subtotal_label = ctk.CTkLabel(
            self.sidebar_frame, text="Subtotal: ₱0.00",
            font=self.controller.fonts["body"], text_color=self.controller.colors["text_muted"]
        )
        self.subtotal_label.grid(row=4, column=0, pady=(10, 0), padx=15, sticky="e")

        self.discount_label = ctk.CTkLabel(
            self.sidebar_frame, text="Discount: -₱0.00",
            font=self.controller.fonts["body"], text_color=self.controller.colors["accent_red"]
        )
        self.discount_label.grid(row=5, column=0, pady=0, padx=15, sticky="e")

        self.total_label = ctk.CTkLabel(
            self.sidebar_frame, text="Total: ₱0.00",
            font=self.controller.fonts["header"], text_color=self.controller.colors["accent_green"]
        )
        self.total_label.grid(row=6, column=0, pady=(5, 12), padx=15, sticky="e")

        self.checkout_btn = ctk.CTkButton(
            self.sidebar_frame, text="Checkout", height=42,
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["accent_green"], hover_color=self.controller.colors["green_hover"],
            command=self.process_checkout
        )
        self.checkout_btn.grid(row=7, column=0, pady=6, padx=15, sticky="ew")

        self.kitchen_btn = ctk.CTkButton(
            self.sidebar_frame, text="Full Kitchen View", height=36,
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"], hover_color=self.controller.colors["primary_hover"],
            command=lambda: [
                self.controller.frames["KitchenFrame"].load_orders(),
                controller.show_frame("KitchenFrame")
            ]
        )
        self.kitchen_btn.grid(row=8, column=0, pady=5, padx=15, sticky="ew")

        self.progress_btn = ctk.CTkButton(
            self.sidebar_frame, text="Daily Progress", height=36,
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["accent_gold"], hover_color=self.controller.colors["gold_hover"],
            command=lambda: [
                self.controller.frames["ProgressFrame"].load_daily_data(),
                self.controller.show_frame("ProgressFrame")
            ]
        )

        self.logout_btn = ctk.CTkButton(
            self.sidebar_frame, text="Logout", height=36,
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["accent_red"], hover_color=self.controller.colors["red_hover"],
            command=lambda: controller.show_frame("LoginFrame")
        )

        # --- Right: Live Kitchen Queue (Two Explicit Side-by-Side Columns) ---
        self.kitchen_container = ctk.CTkFrame(
            self, fg_color=self.controller.colors["bg_card"],
            corner_radius=12, border_width=1, border_color=self.controller.colors["border"]
        )
        self.kitchen_container.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(8, 10), pady=10)
        self.kitchen_container.grid_rowconfigure(0, weight=0)
        self.kitchen_container.grid_rowconfigure(1, weight=1)
        self.kitchen_container.grid_columnconfigure((0, 1), weight=1, uniform="kitchen_cols")

        ctk.CTkLabel(
            self.kitchen_container, text="Live Kitchen Queue",
            font=self.controller.fonts["header"], text_color=self.controller.colors["text_main"]
        ).grid(row=0, column=0, columnspan=2, pady=(10, 5))

        # Column 0: Orders Being Prepared
        self.prep_column = ctk.CTkScrollableFrame(
            self.kitchen_container,
            label_text="Preparing",
            label_font=self.controller.fonts["body"],
            label_text_color=self.controller.colors["accent_gold"],
            fg_color=self.controller.colors["bg_main"],
            corner_radius=8
        )
        self.prep_column.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))

        # Column 1: Orders Ready for Pickup
        self.ready_column = ctk.CTkScrollableFrame(
            self.kitchen_container,
            label_text="Ready for Pickup",
            label_font=self.controller.fonts["body"],
            label_text_color=self.controller.colors["accent_green"],
            fg_color=self.controller.colors["bg_main"],
            corner_radius=8
        )
        self.ready_column.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(0, 8))

        self.bind("<Configure>", self._on_resize)
        self.load_menu()
        self.refresh_kitchen_queue()

    def _on_resize(self, event):
        """Keeps the cashier toolbar logo compact and proportional to window height."""
        if event.height > 100:
            target = max(34, min(46, int(event.height * 0.055)))
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
                    children = self.top_bar.winfo_children()
                    first_other = next((w for w in children if w is not self.logo_label), None)
                    if first_other:
                        self.logo_label.pack(side="left", before=first_other, padx=(4, 8))
                    else:
                        self.logo_label.pack(side="left", padx=(4, 8))
        except Exception as e:
            print(f"Logo load error (CashierFrame): {e}")

    def update_admin_features(self):
        """Adjusts navigation layout based on user role."""
        if self.controller.current_user_role == "Admin":
            self.progress_btn.grid(row=9, column=0, pady=5, padx=15, sticky="ew")
            self.logout_btn.grid(row=10, column=0, pady=(5, 15), padx=15, sticky="ew")
        else:
            self.progress_btn.grid_forget()
            self.logout_btn.grid(row=9, column=0, pady=(5, 15), padx=15, sticky="ew")

    def refresh_categories(self):
        """Populates the category filter dropdown exclusively with categories found in the dataset."""
        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT category
                FROM inventory
                WHERE category IS NOT NULL AND TRIM(category) != ''
                ORDER BY category ASC
            """)
            categories = [row["category"] for row in cursor.fetchall()]

        options = ["All Categories"] + categories
        self.category_menu.configure(values=options)
        if self.category_var.get() not in options:
            self.category_var.set("All Categories")

    def load_menu(self, *_args):
        """Loads menu items filtered by selected category and ordered by selected sort option."""
        self.refresh_categories()

        for widget in self.menu_frame.winfo_children():
            widget.destroy()

        sort_map = {
            "Name (Asc)": "name ASC",
            "Name (Desc)": "name DESC",
            "Price (Asc)": "price ASC",
            "Price (Desc)": "price DESC",
            "SKU Number": "sku ASC"
        }
        order_clause = sort_map.get(self.sort_var.get(), "name ASC")
        selected_category = self.category_var.get()

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            if selected_category == "All Categories":
                cursor.execute(
                    f"SELECT sku, name, price, category, image_path FROM inventory ORDER BY {order_clause}"
                )
            else:
                cursor.execute(
                    f"SELECT sku, name, price, category, image_path FROM inventory WHERE category = ? ORDER BY {order_clause}",
                    (selected_category,)
                )
            items = cursor.fetchall()

        row_idx = 0
        col_idx = 0
        default_img_path = get_resource_path("assets/default.png")

        for item in items:
            btn_text = f"{item['name']}\n₱{item['price']:.2f}\n({item['category']})"
            btn_image = None

            raw_path = item["image_path"] or ""
            candidate_path = (
                raw_path
                if raw_path.startswith("assets")
                else os.path.join("assets", raw_path)
                if raw_path
                else ""
            )
            img_path = get_resource_path(candidate_path) if candidate_path else ""

            if img_path and os.path.exists(img_path):
                try:
                    pil_img = Image.open(img_path)
                    btn_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))
                except Exception:
                    pass

            if btn_image is None and os.path.exists(default_img_path):
                try:
                    pil_img = Image.open(default_img_path)
                    btn_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))
                except Exception:
                    pass

            if btn_image is None:
                try:
                    placeholder_pil = Image.new("RGB", (60, 60), color=(42, 59, 92))
                    btn_image = ctk.CTkImage(light_image=placeholder_pil, dark_image=placeholder_pil, size=(60, 60))
                except Exception:
                    pass

            btn = ctk.CTkButton(
                self.menu_frame,
                text=btn_text,
                font=self.controller.fonts["menu_item"],
                fg_color=self.controller.colors["primary"],
                hover_color=self.controller.colors["primary_hover"],
                text_color=self.controller.colors["text_main"],
                image=btn_image,
                compound="top",
                width=120,
                height=110,
                command=lambda i=item: self.add_to_cart(i)
            )
            btn.grid(row=row_idx, column=col_idx, padx=5, pady=5)

            col_idx += 1
            if col_idx > 2:
                col_idx = 0
                row_idx += 1

    def add_to_cart(self, item):
        sku = item["sku"]
        if sku in self.cart:
            self.cart[sku]["qty"] += 1
        else:
            self.cart[sku] = {
                "name": item["name"],
                "price": item["price"],
                "qty": 1,
                "category": item["category"]
            }
        self.update_cart_display()

    def remove_from_cart(self, sku):
        if sku in self.cart:
            self.cart[sku]["qty"] -= 1
            if self.cart[sku]["qty"] <= 0:
                del self.cart[sku]
        self.update_cart_display()

    def update_cart_display(self):
        for widget in self.cart_list_frame.winfo_children():
            widget.destroy()

        subtotal = 0.0
        discount_amount = 0.0
        current_discount = self.discount_var.get()

        meal_categories = {"Breakfast Meals", "Sandwiches", "Rice Meals", "Binalot", "Chicken Wings"}
        eligible_unit_prices = []
        meal_unit_prices = []
        all_unit_prices = []

        for sku, data in self.cart.items():
            unit_price = data["price"]
            qty = data["qty"]
            category = data["category"]
            line_total = unit_price * qty
            subtotal += line_total

            if qty > 0 and unit_price > 0:
                all_unit_prices.append(unit_price)
                if category in meal_categories:
                    meal_unit_prices.append(unit_price)

                if current_discount == "Free Sandwich Coupon" and category == "Sandwiches":
                    eligible_unit_prices.append(unit_price)
                elif current_discount == "Free Meal Coupon" and category in {"Rice Meals", "Chicken Wings"}:
                    eligible_unit_prices.append(unit_price)

            item_frame = ctk.CTkFrame(self.cart_list_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)

            ctk.CTkLabel(
                item_frame, text=f"{data['name']} x{qty}",
                font=self.controller.fonts["body"]
            ).pack(side="left", padx=4)

            ctk.CTkLabel(
                item_frame, text=f"₱{line_total:.2f}",
                font=self.controller.fonts["body"]
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                item_frame, text="-", width=24, height=24,
                command=lambda s=sku: self.remove_from_cart(s)
            ).pack(side="right", padx=4)

        # Enforce single-meal/single-item discount cap even when 2 or more meals are ordered
        if current_discount in {"Free Sandwich Coupon", "Free Meal Coupon"}:
            if eligible_unit_prices:
                discount_amount = max(eligible_unit_prices)
        elif current_discount == "PWD (20%)":
            if meal_unit_prices:
                discount_amount = max(meal_unit_prices) * 0.20
            elif all_unit_prices:
                discount_amount = max(all_unit_prices) * 0.20

        grand_total = max(0.0, subtotal - discount_amount)

        self.subtotal_label.configure(text=f"Subtotal: ₱{subtotal:.2f}")
        self.discount_label.configure(text=f"Discount: -₱{discount_amount:.2f}")
        self.total_label.configure(text=f"Total: ₱{grand_total:.2f}")
        self.current_total = grand_total

    def process_checkout(self):
        if not self.cart:
            return

        discount_name = self.discount_var.get()
        self.controller.db.create_order(self.cart, self.current_total, discount_name)
        self.cart.clear()
        self.discount_var.set("None")
        self.update_cart_display()
        self.refresh_kitchen_queue()

    def refresh_kitchen_queue(self):
        """Populates Preparing and Ready for Pickup columns separately."""
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
                    SELECT inventory.name, order_items.quantity
                    FROM order_items
                    JOIN inventory ON order_items.sku = inventory.sku
                    WHERE order_items.order_id = ?
                """, (order_id,))
                items = cursor.fetchall()
                item_text = "\n".join([f"{row['quantity']}x {row['name']}" for row in items])

                if status in ("PREPARING", "PENDING"):
                    self._create_prep_card(order_id, seq_num, item_text)
                elif status == "READY":
                    self._create_ready_card(order_id, seq_num, item_text)

        self.after(5000, self.refresh_kitchen_queue)

    def _create_prep_card(self, order_id, seq_num, item_text):
        card = ctk.CTkFrame(
            self.prep_column, border_width=1, corner_radius=8,
            fg_color=self.controller.colors["bg_card"],
            border_color=self.controller.colors["border"]
        )
        card.pack(fill="x", padx=3, pady=4)

        ctk.CTkLabel(
            card, text=f"Order #{seq_num}",
            font=self.controller.fonts["body"],
            text_color=self.controller.colors["accent_gold"]
        ).pack(pady=(5, 0))

        if item_text:
            ctk.CTkLabel(
                card, text=item_text, justify="left",
                font=("Arial", 11),
                text_color=self.controller.colors["text_main"]
            ).pack(pady=3, padx=6)

        ctk.CTkButton(
            card, text="Move to Ready", height=26,
            font=("Arial", 11, "bold"),
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=lambda o=order_id, s=seq_num: self.move_to_ready(o, s)
        ).pack(pady=6, padx=6, fill="x")

    def _create_ready_card(self, order_id, seq_num, item_text):
        card = ctk.CTkFrame(
            self.ready_column, border_width=1, corner_radius=8,
            fg_color=self.controller.colors["bg_card"],
            border_color=self.controller.colors["border"]
        )
        card.pack(fill="x", padx=3, pady=4)

        ctk.CTkLabel(
            card, text=f"Order #{seq_num}",
            font=self.controller.fonts["body"],
            text_color=self.controller.colors["accent_green"]
        ).pack(pady=(5, 0))

        if item_text:
            ctk.CTkLabel(
                card, text=item_text, justify="left",
                font=("Arial", 11),
                text_color=self.controller.colors["text_main"]
            ).pack(pady=3, padx=6)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=6, padx=4, fill="x")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="Call", height=26,
            font=("Arial", 11, "bold"),
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=lambda s=seq_num: self.announce_order(s)
        ).grid(row=0, column=0, padx=2, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Done", height=26,
            font=("Arial", 11, "bold"),
            fg_color=self.controller.colors["accent_green"],
            hover_color=self.controller.colors["green_hover"],
            command=lambda o=order_id: self.complete_order(o)
        ).grid(row=0, column=1, padx=2, sticky="ew")

    def move_to_ready(self, order_id, seq_num):
        if hasattr(self.controller, "queue") and self.controller.queue:
            self.controller.queue.mark_order_ready(order_id, seq_num)
        else:
            with self.controller.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = 'READY' WHERE order_id = ?", (order_id,))
                conn.commit()
            self.announce_order(seq_num)
        self.refresh_kitchen_queue()

    def complete_order(self, order_id):
        if hasattr(self.controller, "queue") and self.controller.queue:
            self.controller.queue.complete_order(order_id)
        else:
            with self.controller.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = 'COMPLETED' WHERE order_id = ?", (order_id,))
                conn.commit()
        self.refresh_kitchen_queue()

    def announce_order(self, sequence_number):
        if hasattr(self.controller, "queue") and self.controller.queue:
            self.controller.queue._play_announcement(sequence_number)
        else:
            import pyttsx3
            try:
                engine = pyttsx3.init()
                engine.say(f"Order number {sequence_number} is ready for pickup.")
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")