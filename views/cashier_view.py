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
        c = controller.colors
        f = controller.fonts

        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller
        self.cart = {}
        self.current_total = 0.0
        self._last_logo_size = None
        self._queue_refresh_job = None
        self._last_queue_snapshot = None
        self._resize_debounce_job = None

        # Grid & Snap state
        self._active_snap_mode = None
        self._menu_buttons = []
        self._current_menu_cols = 3
        self._menu_weight = 48  # Snaps to detents: 45, 52, 60
        self._cart_weight = 26
        self._queue_weight = 26

        # --- Left Workspace Container (Top Bar + Menu Grid) ---
        self.left_workspace = ctk.CTkFrame(self, fg_color="transparent")

        self.top_bar = ctk.CTkFrame(
            self.left_workspace,
            fg_color=c["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=c["border"],
        )
        self.top_bar.pack(fill="x", padx=2, pady=(0, 8))

        self.logo_label = ctk.CTkLabel(self.top_bar, text="")
        self._update_logo(38, 38)

        self.sort_lbl = ctk.CTkLabel(
            self.top_bar, text="Sort:", font=f["small"], text_color=c["text_main"]
        )
        self.sort_lbl.pack(side="left", padx=(6, 4), pady=8)

        self.sort_var = ctk.StringVar(value="Name (Asc)")
        self.sort_menu = ctk.CTkOptionMenu(
            self.top_bar,
            variable=self.sort_var,
            width=120,
            height=30,
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            values=["Name (Asc)", "Name (Desc)", "Price (Asc)", "Price (Desc)", "SKU Number"],
            command=self.load_menu,
        )
        self.sort_menu.pack(side="left", padx=(0, 8), pady=8)

        self.cat_lbl = ctk.CTkLabel(
            self.top_bar, text="Category:", font=f["small"], text_color=c["text_main"]
        )
        self.cat_lbl.pack(side="left", padx=(0, 4), pady=8)

        self.category_var = ctk.StringVar(value="All Categories")
        self.category_menu = ctk.CTkOptionMenu(
            self.top_bar,
            variable=self.category_var,
            width=135,
            height=30,
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            values=["All Categories"],
            command=self.load_menu,
        )
        self.category_menu.pack(side="left", padx=(0, 8), pady=8)

        # Quick-Snap View Switcher on Right of Top Bar
        self.quick_snap = ctk.CTkSegmentedButton(
            self.top_bar,
            values=["Auto", "3-Col", "Split", "Focus"],
            font=f["small"],
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color="#FFFFFF",
            height=28,
            command=self._on_quick_snap_select,
        )
        self.quick_snap.set("Auto")
        self.quick_snap.pack(side="right", padx=8, pady=8)

        # Menu Scrollable Grid
        self.menu_frame = ctk.CTkScrollableFrame(
            self.left_workspace,
            fg_color="transparent",
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.menu_frame.pack(fill="both", expand=True)

        # --- Draggable Snap-to-Detent Splitter ---
        self.splitter = ctk.CTkFrame(
            self,
            width=6,
            fg_color=c["border"],
            corner_radius=3,
            cursor="sb_h_double_arrow",
        )
        self.splitter.bind("<B1-Motion>", self._on_splitter_drag)
        self.splitter.bind("<ButtonRelease-1>", self._on_splitter_release)

        # --- Center: Cart & Checkout Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        self.order_header = ctk.CTkLabel(
            self.sidebar_frame,
            text="Current Order",
            font=f["header"],
            text_color=c["text_main"],
        )
        self.order_header.grid(row=0, column=0, pady=(10, 4))

        self.cart_list_frame = ctk.CTkScrollableFrame(
            self.sidebar_frame,
            fg_color=c["bg_input"],
            corner_radius=8,
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.cart_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=4)

        self.discount_var = ctk.StringVar(value="None")
        self.discount_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            variable=self.discount_var,
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            values=["None", "PWD (20%)", "Free Sandwich Coupon", "Free Meal Coupon"],
            command=lambda _: self.update_cart_display(),
        )
        self.discount_menu.grid(row=3, column=0, pady=5, padx=12, sticky="ew")

        self.subtotal_label = ctk.CTkLabel(
            self.sidebar_frame, text="Subtotal: ₱0.00", font=f["body"], text_color=c["text_muted"]
        )
        self.subtotal_label.grid(row=4, column=0, pady=(6, 0), padx=14, sticky="e")

        self.discount_label = ctk.CTkLabel(
            self.sidebar_frame, text="Discount: -₱0.00", font=f["body"], text_color=c["text_red"]
        )
        self.discount_label.grid(row=5, column=0, pady=1, padx=14, sticky="e")

        self.total_label = ctk.CTkLabel(
            self.sidebar_frame, text="Total: ₱0.00", font=f["header"], text_color=c["text_green"]
        )
        self.total_label.grid(row=6, column=0, pady=(2, 8), padx=14, sticky="e")

        self.checkout_btn = ctk.CTkButton(
            self.sidebar_frame,
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
            self.sidebar_frame,
            text="Full Kitchen View",
            height=34,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda: [
                self.controller.frames["KitchenFrame"].load_orders(),
                controller.show_frame("KitchenFrame"),
            ],
        )
        self.kitchen_btn.grid(row=8, column=0, pady=4, padx=12, sticky="ew")

        self.progress_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Daily Progress",
            height=34,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=lambda: [
                self.controller.frames["ProgressFrame"].load_daily_data(),
                self.controller.show_frame("ProgressFrame"),
            ],
        )

        self.settings_btn = ctk.CTkButton(
            self.sidebar_frame,
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
            self.sidebar_frame,
            text="Logout",
            height=34,
            font=f["button"],
            fg_color=c["accent_red"],
            hover_color=c["red_hover"],
            text_color="#FFFFFF",
            command=lambda: controller.show_frame("LoginFrame"),
        )

        # --- Right / Docked: Live Kitchen Queue ---
        self.kitchen_container = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        self.kitchen_container.grid_rowconfigure(0, weight=0)
        self.kitchen_container.grid_rowconfigure(1, weight=1)
        self.kitchen_container.grid_columnconfigure((0, 1), weight=1, uniform="kitchen_cols")

        self.queue_header = ctk.CTkLabel(
            self.kitchen_container,
            text="Live Kitchen Queue",
            font=f["header"],
            text_color=c["text_main"],
        )
        self.queue_header.grid(row=0, column=0, columnspan=2, pady=(10, 4))

        self.prep_column = ctk.CTkScrollableFrame(
            self.kitchen_container,
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
        self.prep_column.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))

        self.ready_column = ctk.CTkScrollableFrame(
            self.kitchen_container,
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
        self.ready_column.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(0, 8))

        self.bind("<Configure>", self._on_configure)
        self.update_admin_features()
        self._apply_responsive_layout(1280)
        self.load_menu()
        self.refresh_kitchen_queue()

    # =========================================================================
    # GRID & SNAP LAYOUT ENGINE
    # =========================================================================
    def _on_quick_snap_select(self, choice):
        mapping = {
            "Auto": "Auto-Snap",
            "3-Col": "3-Column Wide",
            "Split": "2-Column Split",
            "Focus": "Focus Menu",
        }
        self.controller.settings["cashier_layout"] = mapping.get(choice, "Auto-Snap")
        self._active_snap_mode = None
        self._apply_responsive_layout(self.winfo_width() or 1280)

    def _on_splitter_drag(self, event):
        if self._active_snap_mode != "3-Column Wide":
            return
        total_w = max(1, self.winfo_width())
        pointer_x = self.winfo_pointerx() - self.winfo_rootx()
        ratio = max(0.38, min(0.64, pointer_x / total_w))
        self._menu_weight = int(ratio * 100)
        rem = 100 - self._menu_weight
        self._cart_weight = rem // 2
        self._queue_weight = rem - self._cart_weight
        self.grid_columnconfigure(0, weight=self._menu_weight, minsize=340)
        self.grid_columnconfigure(2, weight=self._cart_weight, minsize=270)
        self.grid_columnconfigure(3, weight=self._queue_weight, minsize=340)

    def _on_splitter_release(self, _event):
        """Snaps the dragged column divider cleanly onto nearest preset detent."""
        if self._active_snap_mode != "3-Column Wide":
            return
        detents = [44, 50, 58]
        snapped = min(detents, key=lambda d: abs(d - self._menu_weight))
        self._menu_weight = snapped
        rem = 100 - snapped
        self._cart_weight = rem // 2
        self._queue_weight = rem - self._cart_weight
        self.grid_columnconfigure(0, weight=self._menu_weight, minsize=340)
        self.grid_columnconfigure(2, weight=self._cart_weight, minsize=270)
        self.grid_columnconfigure(3, weight=self._queue_weight, minsize=340)
        self._reflow_menu_grid()

    def _on_configure(self, event):
        if event.widget is not self:
            return
        if event.height > 100:
            target = max(32, min(44, int(event.height * 0.05)))
            self._update_logo(target, target)

        if self._resize_debounce_job is not None:
            self.after_cancel(self._resize_debounce_job)
        self._resize_debounce_job = self.after(60, lambda w=event.width: self._apply_responsive_layout(w))

    def _apply_responsive_layout(self, width):
        """Snaps Cashier panels into 3-Column, 2-Column Split, or Focus grid based on width/setting."""
        if width <= 1:
            width = 1280

        pref = self.controller.settings.get("cashier_layout", "Auto-Snap")
        if pref == "Auto-Snap":
            if width >= 1080:
                target_mode = "3-Column Wide"
            elif width >= 760:
                target_mode = "2-Column Split"
            else:
                target_mode = "Focus Menu"
        else:
            target_mode = pref

        if target_mode != self._active_snap_mode:
            self._active_snap_mode = target_mode

            # Clear previous grid assignments without destroying widgets
            self.left_workspace.grid_forget()
            self.splitter.grid_forget()
            self.sidebar_frame.grid_forget()
            self.kitchen_container.grid_forget()

            # Reset weights
            for r in range(3):
                self.grid_rowconfigure(r, weight=0, minsize=0)
            for c_idx in range(4):
                self.grid_columnconfigure(c_idx, weight=0, minsize=0)

            if target_mode == "3-Column Wide":
                self.grid_rowconfigure(0, weight=1)
                self.grid_columnconfigure(0, weight=self._menu_weight, minsize=340)
                self.grid_columnconfigure(1, weight=0, minsize=8)
                self.grid_columnconfigure(2, weight=self._cart_weight, minsize=270)
                self.grid_columnconfigure(3, weight=self._queue_weight, minsize=340)

                self.left_workspace.grid(row=0, column=0, sticky="nsew", padx=(10, 2), pady=10)
                self.splitter.grid(row=0, column=1, sticky="ns", pady=18)
                self.sidebar_frame.grid(row=0, column=2, sticky="nsew", padx=4, pady=10)
                self.kitchen_container.grid(row=0, column=3, sticky="nsew", padx=(4, 10), pady=10)

            elif target_mode == "2-Column Split":
                # Top Row: Menu Grid (left) + Cart (right) | Bottom Row: Live Kitchen Queue docked full width
                self.grid_rowconfigure(0, weight=3)
                self.grid_rowconfigure(1, weight=2, minsize=210)
                self.grid_columnconfigure(0, weight=3, minsize=360)
                self.grid_columnconfigure(1, weight=2, minsize=280)

                self.left_workspace.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=(10, 5))
                self.sidebar_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(10, 5))
                self.kitchen_container.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(5, 10))

            else:  # Focus Menu (Menu + Cart side-by-side; Queue hidden to prevent cramping)
                self.grid_rowconfigure(0, weight=1)
                self.grid_columnconfigure(0, weight=3, minsize=320)
                self.grid_columnconfigure(1, weight=2, minsize=260)

                self.left_workspace.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
                self.sidebar_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        self.after_idle(self._reflow_menu_grid)

    def _reflow_menu_grid(self):
        """Snaps menu cards into 2, 3, or 4 columns to fit panel width and active font size."""
        if not self._menu_buttons:
            return

        col_pref = str(self.controller.settings.get("menu_columns", "Auto"))
        panel_w = self.left_workspace.winfo_width()
        if panel_w <= 1:
            panel_w = 540

        if col_pref in ("2", "3", "4"):
            cols = int(col_pref)
        else:
            if panel_w >= 720:
                cols = 4
            elif panel_w >= 470:
                cols = 3
            else:
                cols = 2

        metrics = self.controller.font_metrics
        show_icons = self.controller.settings.get("show_menu_icons", True)
        card_height = metrics["menu_card_height"] if show_icons else max(82, metrics["menu_card_height"] - 44)
        card_width = max(110, (panel_w - 36) // cols)
        wrap_len = max(95, card_width - 20)

        for idx in range(4):
            self.menu_frame.grid_columnconfigure(idx, weight=1 if idx < cols else 0, uniform="menu_cols" if idx < cols else "")

        for idx, btn in enumerate(self._menu_buttons):
            r, c_idx = divmod(idx, cols)
            btn.configure(height=card_height)
            try:
                btn._text_label.configure(wraplength=wrap_len, justify="center")
            except AttributeError:
                pass
            btn.grid(row=r, column=c_idx, padx=5, pady=5, sticky="nsew")

    # =========================================================================
    # THEME & SETTINGS SYNCHRONIZATION
    # =========================================================================
    def apply_theme(self):
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        self.top_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.sidebar_frame.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.kitchen_container.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.cart_list_frame.configure(fg_color=c["bg_input"])
        self.splitter.configure(fg_color=c["border"])

        for lbl in (self.sort_lbl, self.cat_lbl, self.order_header, self.queue_header):
            lbl.configure(text_color=c["text_main"])
        self.subtotal_label.configure(text_color=c["text_muted"])
        self.discount_label.configure(text_color=c["text_red"])
        self.total_label.configure(text_color=c["text_green"])

        self.checkout_btn.configure(fg_color=c["accent_green"], hover_color=c["green_hover"])
        self.kitchen_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.progress_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.settings_btn.configure(
            fg_color=c["bg_input"], hover_color=c["border"], border_color=c["border"], text_color=c["text_main"]
        )
        self.logout_btn.configure(fg_color=c["accent_red"], hover_color=c["red_hover"])

        for menu in (self.sort_menu, self.category_menu, self.discount_menu):
            menu.configure(
                fg_color=c["primary"],
                button_color=c["primary_hover"],
                button_hover_color=c["primary_hover"],
            )

        self.quick_snap.configure(
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
        )
        self.prep_column.configure(
            fg_color=c["bg_input"], label_fg_color=c["border"], label_text_color=c["accent_gold"], border_color=c["border"]
        )
        self.ready_column.configure(
            fg_color=c["bg_input"], label_fg_color=c["border"], label_text_color=c["text_green"], border_color=c["border"]
        )

    def on_settings_updated(self):
        rev_map = {
            "Auto-Snap": "Auto",
            "3-Column Wide": "3-Col",
            "2-Column Split": "Split",
            "Focus Menu": "Focus",
        }
        self.quick_snap.set(rev_map.get(self.controller.settings.get("cashier_layout", "Auto-Snap"), "Auto"))
        self._active_snap_mode = None
        self._apply_responsive_layout(self.winfo_width() or 1280)
        self.load_menu()
        self.update_cart_display()
        self.refresh_kitchen_queue(force=True)

    # =========================================================================
    # MENU, CART & QUEUE OPERATIONS
    # =========================================================================
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
                        self.logo_label.pack(side="left", before=first_other, padx=(6, 4))
                    else:
                        self.logo_label.pack(side="left", padx=(6, 4))
        except Exception as e:
            print(f"Logo load error (CashierFrame): {e}")

    def update_admin_features(self):
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

    def refresh_categories(self):
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
        self.refresh_categories()
        c = self.controller.colors
        f = self.controller.fonts
        show_icons = self.controller.settings.get("show_menu_icons", True)

        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        self._menu_buttons = []

        sort_map = {
            "Name (Asc)": "name ASC",
            "Name (Desc)": "name DESC",
            "Price (Asc)": "price ASC",
            "Price (Desc)": "price DESC",
            "SKU Number": "sku ASC",
        }
        order_clause = sort_map.get(self.sort_var.get(), "name ASC")
        selected_category = self.category_var.get()

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            if selected_category == "All Categories":
                cursor.execute(f"SELECT sku, name, price, category, image_path FROM inventory ORDER BY {order_clause}")
            else:
                cursor.execute(
                    f"SELECT sku, name, price, category, image_path FROM inventory WHERE category = ? ORDER BY {order_clause}",
                    (selected_category,),
                )
            items = cursor.fetchall()

        default_img_path = get_resource_path("assets/default.png")

        for item in items:
            btn_text = f"{item['name']}\n₱{item['price']:.2f}\n({item['category']})"
            btn_image = None

            if show_icons:
                raw_path = item["image_path"] or ""
                candidate_path = (
                    raw_path if raw_path.startswith("assets") else os.path.join("assets", raw_path) if raw_path else ""
                )
                img_path = get_resource_path(candidate_path) if candidate_path else ""

                if img_path and os.path.exists(img_path):
                    try:
                        pil_img = Image.open(img_path)
                        btn_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(52, 52))
                    except Exception:
                        pass

                if btn_image is None and os.path.exists(default_img_path):
                    try:
                        pil_img = Image.open(default_img_path)
                        btn_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(52, 52))
                    except Exception:
                        pass

            btn = ctk.CTkButton(
                self.menu_frame,
                text=btn_text,
                font=f["menu_item"],
                fg_color=c["bg_card"],
                hover_color=c["primary"],
                border_width=1,
                border_color=c["border"],
                text_color=c["text_main"],
                image=btn_image,
                compound="top" if btn_image else "none",
                corner_radius=10,
                command=lambda i=item: self.add_to_cart(i),
            )
            self._menu_buttons.append(btn)

        self._reflow_menu_grid()

    def add_to_cart(self, item):
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
        self.update_cart_display()

    def remove_from_cart(self, sku):
        if sku in self.cart:
            self.cart[sku]["qty"] -= 1
            if self.cart[sku]["qty"] <= 0:
                del self.cart[sku]
        self.update_cart_display()

    def update_cart_display(self):
        c = self.controller.colors
        f = self.controller.fonts

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
                command=lambda s=sku: self.remove_from_cart(s),
            ).pack(side="right", padx=(2, 6), pady=4)

            ctk.CTkLabel(
                item_frame,
                text=f"₱{line_total:.2f}",
                font=f["small"],
                text_color=c["accent_gold"],
            ).pack(side="right", padx=4, pady=4)

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
        seq, order_id = self.controller.db.create_order(self.cart, self.current_total, discount_name)

        cart_list = [
            {"sku": sku, "name": data["name"], "price": data["price"], "quantity": data["qty"]}
            for sku, data in self.cart.items()
        ]

        if hasattr(self.controller, "queue") and self.controller.queue:
            self.controller.queue.printer.print_receipt(seq, cart_list, self.current_total)
        else:
            from printer_manager import PrinterManager
            PrinterManager(printer_name="POS-58").print_receipt(seq, cart_list, self.current_total)

        self.cart.clear()
        self.discount_var.set("None")
        self.update_cart_display()
        self.refresh_kitchen_queue(force=True)

    def refresh_kitchen_queue(self, force=False):
        if self._queue_refresh_job is not None:
            self.after_cancel(self._queue_refresh_job)
            self._queue_refresh_job = None

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT order_id, sequence_number, status
                FROM orders
                WHERE status IN ('PREPARING', 'PENDING', 'READY')
                ORDER BY sequence_number ASC
            """)
            orders = cursor.fetchall()
            snapshot = [(o["order_id"], o["sequence_number"], o["status"]) for o in orders]

            if force or snapshot != self._last_queue_snapshot:
                self._last_queue_snapshot = snapshot

                for widget in self.prep_column.winfo_children():
                    widget.destroy()
                for widget in self.ready_column.winfo_children():
                    widget.destroy()

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

        interval_sec = int(self.controller.settings.get("queue_refresh_sec", 5))
        if interval_sec > 0:
            self._queue_refresh_job = self.after(interval_sec * 1000, self.refresh_kitchen_queue)

    def _create_prep_card(self, order_id, seq_num, item_text):
        c = self.controller.colors
        f = self.controller.fonts
        wrap = self.controller.font_metrics.get("queue_wrap", 165)

        card = ctk.CTkFrame(
            self.prep_column, border_width=1, corner_radius=8, fg_color=c["bg_card"], border_color=c["accent_gold"]
        )
        card.pack(fill="x", padx=4, pady=5)

        ctk.CTkLabel(card, text=f"Order #{seq_num}", font=f["subheader"], text_color=c["accent_gold"]).pack(pady=(6, 2))
        if item_text:
            ctk.CTkLabel(
                card, text=item_text, justify="left", wraplength=wrap, font=f["small"], text_color=c["text_main"]
            ).pack(pady=3, padx=8, anchor="w")

        ctk.CTkButton(
            card,
            text="Move to Ready",
            height=28,
            font=f["small"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda o=order_id, s=seq_num: self.move_to_ready(o, s),
        ).pack(pady=(6, 8), padx=8, fill="x")

    def _create_ready_card(self, order_id, seq_num, item_text):
        c = self.controller.colors
        f = self.controller.fonts
        wrap = self.controller.font_metrics.get("queue_wrap", 165)

        card = ctk.CTkFrame(
            self.ready_column, border_width=1, corner_radius=8, fg_color=c["bg_card"], border_color=c["text_green"]
        )
        card.pack(fill="x", padx=4, pady=5)

        ctk.CTkLabel(card, text=f"Order #{seq_num}", font=f["subheader"], text_color=c["text_green"]).pack(pady=(6, 2))
        if item_text:
            ctk.CTkLabel(
                card, text=item_text, justify="left", wraplength=wrap, font=f["small"], text_color=c["text_main"]
            ).pack(pady=3, padx=8, anchor="w")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=(6, 8), padx=6, fill="x")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame,
            text="Call",
            height=28,
            font=f["small"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda s=seq_num: self.announce_order(s),
        ).grid(row=0, column=0, padx=2, sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="Done",
            height=28,
            font=f["small"],
            fg_color=c["accent_green"],
            hover_color=c["green_hover"],
            text_color="#FFFFFF",
            command=lambda o=order_id: self.complete_order(o),
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
        self.refresh_kitchen_queue(force=True)

    def complete_order(self, order_id):
        if hasattr(self.controller, "queue") and self.controller.queue:
            self.controller.queue.complete_order(order_id)
        else:
            with self.controller.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = 'COMPLETED' WHERE order_id = ?", (order_id,))
                conn.commit()
        self.refresh_kitchen_queue(force=True)

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