import customtkinter as ctk


class CartPanel(ctk.CTkFrame):
    """Center Cashier sidebar for active order items, discounts, checkout, and navigation."""

    MEAL_CATEGORIES = {"Breakfast Meals", "Sandwiches", "Rice Meals", "Binalot", "Chicken Wings"}

    def __init__(self, parent, controller, on_order_completed):
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
        self.on_order_completed = on_order_completed
        self.cart = {}
        self.current_total = 0.0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.order_header = ctk.CTkLabel(
            self, text="Current Order", font=f["header"], text_color=c["text_main"]
        )
        self.order_header.grid(row=0, column=0, pady=(10, 4))

        self.cart_list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=c["bg_input"],
            corner_radius=8,
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.cart_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=4)

        self.discount_var = ctk.StringVar(value="None")
        self.discount_menu = ctk.CTkOptionMenu(
            self,
            variable=self.discount_var,
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            values=["None", "PWD (20%)", "Free Sandwich Coupon", "Free Meal Coupon"],
            command=lambda _: self.update_display(),
        )
        self.discount_menu.grid(row=3, column=0, pady=5, padx=12, sticky="ew")

        self.subtotal_label = ctk.CTkLabel(
            self, text="Subtotal: ₱0.00", font=f["body"], text_color=c["text_muted"]
        )
        self.subtotal_label.grid(row=4, column=0, pady=(6, 0), padx=14, sticky="e")

        self.discount_label = ctk.CTkLabel(
            self, text="Discount: -₱0.00", font=f["body"], text_color=c["text_red"]
        )
        self.discount_label.grid(row=5, column=0, pady=1, padx=14, sticky="e")

        self.total_label = ctk.CTkLabel(
            self, text="Total: ₱0.00", font=f["header"], text_color=c["text_green"]
        )
        self.total_label.grid(row=6, column=0, pady=(2, 8), padx=14, sticky="e")

        self.checkout_btn = ctk.CTkButton(
            self,
            text="Checkout",
            height=40,
            font=f["button"],
            fg_color=c["accent_green"],
            hover_color=c["green_hover"],
            text_color="#FFFFFF",
            command=self.process_checkout,
        )
        self.checkout_btn.grid(row=7, column=0, pady=4, padx=12, sticky="ew")

        self.kitchen_btn = ctk.CTkButton(
            self,
            text="Full Kitchen View",
            height=34,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda: controller.show_frame("KitchenFrame"),
        )
        self.kitchen_btn.grid(row=8, column=0, pady=4, padx=12, sticky="ew")

        self.progress_btn = ctk.CTkButton(
            self,
            text="Daily Progress",
            height=34,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=lambda: controller.show_frame("ProgressFrame"),
        )

        self.settings_btn = ctk.CTkButton(
            self,
            text="Settings & Font Size",
            height=34,
            font=f["button"],
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_width=1,
            border_color=c["border"],
            text_color=c["text_main"],
            command=lambda: controller.show_frame("SettingsFrame"),
        )

        self.logout_btn = ctk.CTkButton(
            self,
            text="Logout",
            height=34,
            font=f["button"],
            fg_color=c["accent_red"],
            hover_color=c["red_hover"],
            text_color="#FFFFFF",
            command=lambda: controller.show_frame("LoginFrame"),
        )

        self.update_admin_features()

    def add_item(self, item) -> None:
        sku = item["sku"]
        if sku in self.cart:
            self.cart[sku]["qty"] += 1
        else:
            self.cart[sku] = {
                "name": item["name"],
                "price": item["price"],
                "qty": 1,
                "category": item["category"],
            }
        self.update_display()

    def remove_item(self, sku: str) -> None:
        if sku in self.cart:
            self.cart[sku]["qty"] -= 1
            if self.cart[sku]["qty"] <= 0:
                del self.cart[sku]
        self.update_display()

    def update_display(self) -> None:
        c = self.controller.colors
        f = self.controller.fonts

        for widget in self.cart_list_frame.winfo_children():
            widget.destroy()

        subtotal = 0.0
        current_discount = self.discount_var.get()
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
                if category in self.MEAL_CATEGORIES:
                    meal_unit_prices.append(unit_price)
                if current_discount == "Free Sandwich Coupon" and category == "Sandwiches":
                    eligible_unit_prices.append(unit_price)
                elif current_discount == "Free Meal Coupon" and category in {"Rice Meals", "Chicken Wings"}:
                    eligible_unit_prices.append(unit_price)

            item_frame = ctk.CTkFrame(self.cart_list_frame, fg_color=c["bg_card"], corner_radius=6)
            item_frame.pack(fill="x", pady=3, padx=2)

            ctk.CTkLabel(
                item_frame,
                text=f"{data['name']} x{qty}",
                font=f["small"],
                text_color=c["text_main"],
                wraplength=125,
                justify="left",
            ).pack(side="left", padx=6, pady=4)

            ctk.CTkButton(
                item_frame,
                text="-",
                width=26,
                height=26,
                font=f["button"],
                fg_color=c["accent_red"],
                hover_color=c["red_hover"],
                text_color="#FFFFFF",
                command=lambda s=sku: self.remove_item(s),
            ).pack(side="right", padx=(2, 6), pady=4)

            ctk.CTkLabel(
                item_frame,
                text=f"₱{line_total:.2f}",
                font=f["small"],
                text_color=c["accent_gold"],
            ).pack(side="right", padx=4, pady=4)

        discount_amount = 0.0
        if current_discount in {"Free Sandwich Coupon", "Free Meal Coupon"} and eligible_unit_prices:
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

    def process_checkout(self) -> None:
        if not self.cart:
            return

        discount_name = self.discount_var.get()
        self.controller.queue.process_new_transaction(self.cart, self.current_total, discount_name)

        self.cart.clear()
        self.discount_var.set("None")
        self.update_display()
        if callable(self.on_order_completed):
            self.on_order_completed()

    def update_admin_features(self) -> None:
        """Adjusts sidebar action buttons based on user role, keeping Settings accessible."""
        self.progress_btn.grid_forget()
        self.settings_btn.grid_forget()
        self.logout_btn.grid_forget()

        row = 9
        if self.controller.current_user_role == "Admin":
            self.progress_btn.grid(row=row, column=0, pady=4, padx=12, sticky="ew")
            row += 1

        self.settings_btn.grid(row=row, column=0, pady=4, padx=12, sticky="ew")
        row += 1
        self.logout_btn.grid(row=row, column=0, pady=(4, 12), padx=12, sticky="ew")

    def apply_theme(self) -> None:
        c = self.controller.colors
        self.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.cart_list_frame.configure(fg_color=c["bg_input"])
        self.order_header.configure(text_color=c["text_main"])
        self.subtotal_label.configure(text_color=c["text_muted"])
        self.discount_label.configure(text_color=c["text_red"])
        self.total_label.configure(text_color=c["text_green"])
        self.discount_menu.configure(
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
        )
        self.checkout_btn.configure(fg_color=c["accent_green"], hover_color=c["green_hover"])
        self.kitchen_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.progress_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.settings_btn.configure(
            fg_color=c["bg_input"], hover_color=c["border"], border_color=c["border"], text_color=c["text_main"]
        )
        self.logout_btn.configure(fg_color=c["accent_red"], hover_color=c["red_hover"])
        self.update_display()