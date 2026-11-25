import customtkinter as ctk
from views.cashier.checkout_dialog import CheckoutDialog


class CartPanel(ctk.CTkFrame):
    """Center Cashier sidebar for active order items, discounts, checkout, and navigation."""

    MEAL_CATEGORIES = {"Breakfast Meals", "Sandwiches", "Rice Meals", "Binalot", "Chicken Wings"}
    SANDWICH_CATEGORIES = {"Sandwiches"}
    RICE_MEAL_CATEGORIES = {"Rice Meals", "Chicken Wings"}

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
        self.current_subtotal = 0.0
        self.current_discount_amount = 0.0
        self.current_total = 0.0

        # Cached row widgets keyed by SKU to avoid full destroy/recreate lag
        self._row_widgets = {}
        self._last_subtotal_text = "Subtotal: ₱0.00"
        self._last_discount_text = "Discount: -₱0.00"
        self._last_total_text = "Total: ₱0.00"
        self._last_admin_role = None
        self._checking_out = False
        self._checkout_dialog = None

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
            values=[
                "None",
                "PWD (20%)",
                "Free Sandwich Coupon",
                "Free Meal Coupon",
                "Free Sandwich & Meal Coupon",
            ],
            command=lambda _: self._recalculate_totals(),
        )
        self.discount_menu.grid(row=3, column=0, pady=5, padx=12, sticky="ew")

        self.subtotal_label = ctk.CTkLabel(
            self, text=self._last_subtotal_text, font=f["body"], text_color=c["text_muted"]
        )
        self.subtotal_label.grid(row=4, column=0, pady=(6, 0), padx=14, sticky="e")

        self.discount_label = ctk.CTkLabel(
            self, text=self._last_discount_text, font=f["body"], text_color=c["text_red"]
        )
        self.discount_label.grid(row=5, column=0, pady=1, padx=14, sticky="e")

        self.total_label = ctk.CTkLabel(
            self, text=self._last_total_text, font=f["header"], text_color=c["text_green"]
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
            text="Sales & Inventory",
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
        self._upsert_row(sku)
        self._recalculate_totals()

    def remove_item(self, sku: str) -> None:
        if sku not in self.cart:
            return
        self.cart[sku]["qty"] -= 1
        if self.cart[sku]["qty"] <= 0:
            del self.cart[sku]
            self._remove_row(sku)
        else:
            self._upsert_row(sku)
        self._recalculate_totals()

    def _upsert_row(self, sku: str) -> None:
        data = self.cart[sku]
        qty = data["qty"]
        line_total = data["price"] * qty
        name_text = f"{data['name']} x{qty}"
        price_text = f"₱{line_total:.2f}"

        row = self._row_widgets.get(sku)
        if row is not None:
            if row["last_name_text"] != name_text:
                row["name_lbl"].configure(text=name_text)
                row["last_name_text"] = name_text
            if row["last_price_text"] != price_text:
                row["price_lbl"].configure(text=price_text)
                row["last_price_text"] = price_text
            return

        c = self.controller.colors
        f = self.controller.fonts

        item_frame = ctk.CTkFrame(self.cart_list_frame, fg_color=c["bg_card"], corner_radius=6)
        item_frame.pack(fill="x", pady=3, padx=2)

        name_lbl = ctk.CTkLabel(
            item_frame,
            text=name_text,
            font=f["small"],
            text_color=c["text_main"],
            wraplength=125,
            justify="left",
        )
        name_lbl.pack(side="left", padx=6, pady=4)

        remove_btn = ctk.CTkButton(
            item_frame,
            text="-",
            width=26,
            height=26,
            font=f["button"],
            fg_color=c["accent_red"],
            hover_color=c["red_hover"],
            text_color="#FFFFFF",
            command=lambda s=sku: self.remove_item(s),
        )
        remove_btn.pack(side="right", padx=(2, 6), pady=4)

        price_lbl = ctk.CTkLabel(
            item_frame,
            text=price_text,
            font=f["small"],
            text_color=c["accent_gold"],
        )
        price_lbl.pack(side="right", padx=4, pady=4)

        self._row_widgets[sku] = {
            "frame": item_frame,
            "name_lbl": name_lbl,
            "price_lbl": price_lbl,
            "remove_btn": remove_btn,
            "last_name_text": name_text,
            "last_price_text": price_text,
        }

    def _remove_row(self, sku: str) -> None:
        row = self._row_widgets.pop(sku, None)
        if row is not None and row["frame"].winfo_exists():
            row["frame"].destroy()

    def _sync_cart_rows(self) -> None:
        stale_skus = [sku for sku in self._row_widgets if sku not in self.cart]
        for sku in stale_skus:
            self._remove_row(sku)
        for sku in self.cart:
            self._upsert_row(sku)

    def _recalculate_totals(self) -> None:
        subtotal = 0.0
        current_discount = self.discount_var.get()
        sandwich_unit_prices = []
        rice_meal_unit_prices = []
        meal_unit_prices = []
        all_unit_prices = []

        for data in self.cart.values():
            unit_price = data["price"]
            qty = data["qty"]
            category = data["category"]
            subtotal += unit_price * qty

            if qty > 0 and unit_price > 0:
                all_unit_prices.append(unit_price)
                if category in self.MEAL_CATEGORIES:
                    meal_unit_prices.append(unit_price)
                if category in self.SANDWICH_CATEGORIES:
                    sandwich_unit_prices.append(unit_price)
                if category in self.RICE_MEAL_CATEGORIES:
                    rice_meal_unit_prices.append(unit_price)

        discount_amount = 0.0
        if current_discount == "Free Sandwich Coupon":
            if sandwich_unit_prices:
                discount_amount = max(sandwich_unit_prices)
        elif current_discount == "Free Meal Coupon":
            if rice_meal_unit_prices:
                discount_amount = max(rice_meal_unit_prices)
        elif current_discount == "Free Sandwich & Meal Coupon":
            if sandwich_unit_prices:
                discount_amount += max(sandwich_unit_prices)
            if rice_meal_unit_prices:
                discount_amount += max(rice_meal_unit_prices)
        elif current_discount == "PWD (20%)":
            if meal_unit_prices:
                discount_amount = max(meal_unit_prices) * 0.20
            elif all_unit_prices:
                discount_amount = max(all_unit_prices) * 0.20

        subtotal = round(subtotal, 2)
        discount_amount = round(discount_amount, 2)
        grand_total = round(max(0.0, subtotal - discount_amount), 2)

        self.current_subtotal = subtotal
        self.current_discount_amount = discount_amount
        self.current_total = grand_total

        sub_text = f"Subtotal: ₱{subtotal:.2f}"
        disc_text = f"Discount: -₱{discount_amount:.2f}"
        tot_text = f"Total: ₱{grand_total:.2f}"

        if sub_text != self._last_subtotal_text:
            self.subtotal_label.configure(text=sub_text)
            self._last_subtotal_text = sub_text
        if disc_text != self._last_discount_text:
            self.discount_label.configure(text=disc_text)
            self._last_discount_text = disc_text
        if tot_text != self._last_total_text:
            self.total_label.configure(text=tot_text)
            self._last_total_text = tot_text

    def update_display(self) -> None:
        self._sync_cart_rows()
        self._recalculate_totals()

    def process_checkout(self) -> None:
        """Opens the two-stage CheckoutDialog for payment entry and change calculation."""
        if not self.cart or self._checking_out:
            return

        if self._checkout_dialog is not None:
            try:
                if self._checkout_dialog.winfo_exists():
                    self._checkout_dialog.lift()
                    self._checkout_dialog.focus_set()
                    return
            except Exception:
                pass
            self._checkout_dialog = None

        self._recalculate_totals()
        self._checkout_dialog = CheckoutDialog(
            parent=self,
            controller=self.controller,
            cart_items=self.cart,
            subtotal=self.current_subtotal,
            discount_name=self.discount_var.get(),
            discount_amount=self.current_discount_amount,
            total_amount=self.current_total,
            on_confirm=self._complete_checkout,
        )

    def _complete_checkout(self, amount_tendered: float, change_amount: float) -> None:
        """Commits the paid order to DB + receipt printer and pushes it to the Live Kitchen Queue."""
        if not self.cart or self._checking_out:
            return

        self._checking_out = True
        self.checkout_btn.configure(state="disabled")
        try:
            discount_name = self.discount_var.get()
            self.controller.queue.process_new_transaction(
                self.cart,
                self.current_total,
                discount_name,
                amount_tendered=amount_tendered,
                change_amount=change_amount,
            )

            self.cart.clear()
            for sku in list(self._row_widgets.keys()):
                self._remove_row(sku)
            self.discount_var.set("None")
            self._recalculate_totals()

            try:
                self.cart_list_frame._parent_canvas.yview_moveto(0)
            except Exception:
                pass

            if callable(self.on_order_completed):
                self.on_order_completed()
        finally:
            self._checking_out = False
            self._checkout_dialog = None
            if self.checkout_btn.winfo_exists():
                self.checkout_btn.configure(state="normal")

    def update_admin_features(self) -> None:
        """Adjusts sidebar action buttons based on user role, keeping Settings accessible."""
        role = self.controller.current_user_role
        if role == self._last_admin_role:
            return
        self._last_admin_role = role

        self.progress_btn.grid_forget()
        self.settings_btn.grid_forget()
        self.logout_btn.grid_forget()

        row = 9
        if role == "Admin":
            self.progress_btn.grid(row=row, column=0, pady=4, padx=12, sticky="ew")
            row += 1

        self.settings_btn.grid(row=row, column=0, pady=4, padx=12, sticky="ew")
        row += 1
        self.logout_btn.grid(row=row, column=0, pady=(4, 12), padx=12, sticky="ew")

    def apply_theme(self) -> None:
        c = self.controller.colors
        f = self.controller.fonts

        self.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.cart_list_frame.configure(
            fg_color=c["bg_input"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
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
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_color=c["border"],
            text_color=c["text_main"],
        )
        self.logout_btn.configure(fg_color=c["accent_red"], hover_color=c["red_hover"])

        # Re-theme cached cart rows in place instead of destroying and rebuilding them
        for row in self._row_widgets.values():
            row["frame"].configure(fg_color=c["bg_card"])
            row["name_lbl"].configure(text_color=c["text_main"], font=f["small"])
            row["price_lbl"].configure(text_color=c["accent_gold"], font=f["small"])
            row["remove_btn"].configure(
                fg_color=c["accent_red"], hover_color=c["red_hover"], font=f["button"]
            )