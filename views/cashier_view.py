import os
import sys
import threading
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

        self._splitter_idle_color = c["border"]
        self._splitter_hover_color = c["primary"]

        # Grid & Resizable Panel Weights
        self._active_snap_mode = None
        self._menu_buttons = []
        self._top_bar_compact = None

        # 3-Column main weights (sum = 100)
        self._menu_weight = 48
        self._cart_weight = 25
        self._queue_weight = 27

        # 2-Column / Focus split weights (sum = 100)
        self._split_left_weight = 60
        self._split_right_weight = 40

        # Inner Live Kitchen Queue column weights (sum = 100)
        self._prep_weight = 50
        self._ready_weight = 50

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

        self.top_bar_filters = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.top_bar_filters.pack(side="left", fill="x", expand=True)

        self.logo_label = ctk.CTkLabel(self.top_bar_filters, text="")
        self._update_logo(38, 38)

        self.sort_lbl = ctk.CTkLabel(
            self.top_bar_filters, text="Sort:", font=f["small"], text_color=c["text_main"]
        )
        self.sort_lbl.pack(side="left", padx=(6, 4), pady=8)

        self.sort_var = ctk.StringVar(value="Name (Asc)")
        self.sort_menu = ctk.CTkOptionMenu(
            self.top_bar_filters,
            variable=self.sort_var,
            width=115,
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
            self.top_bar_filters, text="Category:", font=f["small"], text_color=c["text_main"]
        )
        self.cat_lbl.pack(side="left", padx=(0, 4), pady=8)

        self.category_var = ctk.StringVar(value="All Categories")
        self.category_menu = ctk.CTkOptionMenu(
            self.top_bar_filters,
            variable=self.category_var,
            width=130,
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

        # Quick-Snap View Switcher
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

        # --- Splitter 1: Between Menu Workspace and Current Order ---
        self.splitter_menu_cart = self._create_splitter(
            self,
            on_drag=self._on_menu_cart_drag,
            on_release=self._on_main_splitter_release,
        )

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

        # --- Splitter 2: Right Side of Current Order (Between Cart & Live Kitchen Queue) ---
        self.splitter_cart_queue = self._create_splitter(
            self,
            on_drag=self._on_cart_queue_drag,
            on_release=self._on_main_splitter_release,
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
        self.kitchen_container.grid_columnconfigure(0, weight=self._prep_weight, minsize=120)
        self.kitchen_container.grid_columnconfigure(1, weight=0, minsize=8)
        self.kitchen_container.grid_columnconfigure(2, weight=self._ready_weight, minsize=120)

        self.queue_header = ctk.CTkLabel(
            self.kitchen_container,
            text="Live Kitchen Queue",
            font=f["header"],
            text_color=c["text_main"],
        )
        self.queue_header.grid(row=0, column=0, columnspan=3, pady=(10, 4))

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
        self.prep_column.grid(row=1, column=0, sticky="nsew", padx=(8, 2), pady=(0, 8))

        # --- Splitter 3: Inside Live Kitchen Queue (Between Preparing & Ready for Pickup) ---
        self.splitter_kitchen = self._create_splitter(
            self.kitchen_container,
            on_drag=self._on_kitchen_splitter_drag,
            on_release=None,
        )
        self.splitter_kitchen.grid(row=1, column=1, sticky="ns", pady=(4, 12))

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
        self.ready_column.grid(row=1, column=2, sticky="nsew", padx=(2, 8), pady=(0, 8))

        self.bind("<Configure>", self._on_configure)
        self.update_admin_features()
        self._apply_responsive_layout(1280)
        self.load_menu()
        self.refresh_kitchen_queue()

    def _create_splitter(self, parent, on_drag, on_release=None):
        """Creates a styled, hover-highlighted vertical splitter handle."""
        bar = ctk.CTkFrame(
            parent,
            width=6,
            fg_color=self._splitter_idle_color,
            corner_radius=3,
            cursor="sb_h_double_arrow",
        )
        bar.bind("<Enter>", lambda _e, b=bar: b.configure(fg_color=self._splitter_hover_color))
        bar.bind("<Leave>", lambda _e, b=bar: b.configure(fg_color=self._splitter_idle_color))
        bar.bind("<B1-Motion>", on_drag)
        if on_release:
            bar.bind("<ButtonRelease-1>", on_release)
        return bar

    # =========================================================================
    # GRID & MULTI-SPLITTER LAYOUT ENGINE
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

    def _on_menu_cart_drag(self, _event):
        """Slides the boundary between the Menu workspace and Current Order panel."""
        total_w = max(1, self.winfo_width())
        pointer_x = self.winfo_pointerx() - self.winfo_rootx()

        if self._active_snap_mode == "3-Column Wide":
            avail = 100 - self._queue_weight
            desired_menu = int(round((pointer_x / total_w) * 100))
            min_menu = 26
            max_menu = max(min_menu, avail - 20)
            self._menu_weight = max(min_menu, min(max_menu, desired_menu))
            self._cart_weight = avail - self._menu_weight

            self.grid_columnconfigure(0, weight=self._menu_weight, minsize=280)
            self.grid_columnconfigure(2, weight=self._cart_weight, minsize=240)
            self.grid_columnconfigure(4, weight=self._queue_weight, minsize=280)
        else:
            desired_left = int(round((pointer_x / total_w) * 100))
            self._split_left_weight = max(32, min(74, desired_left))
            self._split_right_weight = 100 - self._split_left_weight

            self.grid_columnconfigure(0, weight=self._split_left_weight, minsize=300)
            self.grid_columnconfigure(2, weight=self._split_right_weight, minsize=250)

        self._update_top_bar_layout()

    def _on_cart_queue_drag(self, _event):
        """Slides the boundary between Current Order and Live Kitchen Queue."""
        if self._active_snap_mode != "3-Column Wide":
            return

        total_w = max(1, self.winfo_width())
        pointer_x = self.winfo_pointerx() - self.winfo_rootx()

        avail = 100 - self._menu_weight
        boundary_pct = int(round((pointer_x / total_w) * 100))
        desired_cart = boundary_pct - self._menu_weight

        min_cart = 20
        max_cart = max(min_cart, avail - 22)
        self._cart_weight = max(min_cart, min(max_cart, desired_cart))
        self._queue_weight = avail - self._cart_weight

        self.grid_columnconfigure(0, weight=self._menu_weight, minsize=280)
        self.grid_columnconfigure(2, weight=self._cart_weight, minsize=240)
        self.grid_columnconfigure(4, weight=self._queue_weight, minsize=280)

    def _on_kitchen_splitter_drag(self, _event):
        """Slides the divider between Preparing and Ready for Pickup inside Live Kitchen Queue."""
        container_w = max(1, self.kitchen_container.winfo_width())
        rel_x = self.winfo_pointerx() - self.kitchen_container.winfo_rootx()

        ratio = max(0.25, min(0.75, rel_x / container_w))
        self._prep_weight = int(round(ratio * 100))
        self._ready_weight = 100 - self._prep_weight

        self.kitchen_container.grid_columnconfigure(0, weight=self._prep_weight, minsize=120)
        self.kitchen_container.grid_columnconfigure(2, weight=self._ready_weight, minsize=120)

    def _on_main_splitter_release(self, _event):
        """Reflows menu columns and top bar controls after dragging completes."""
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
        """Snaps Cashier panels into 3-Column, 2-Column Split, or Focus grid with draggable dividers."""
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

            self.left_workspace.grid_forget()
            self.splitter_menu_cart.grid_forget()
            self.sidebar_frame.grid_forget()
            self.splitter_cart_queue.grid_forget()
            self.kitchen_container.grid_forget()

            for r in range(3):
                self.grid_rowconfigure(r, weight=0, minsize=0)
            for c_idx in range(5):
                self.grid_columnconfigure(c_idx, weight=0, minsize=0)

            if target_mode == "3-Column Wide":
                self.grid_rowconfigure(0, weight=1)
                self.grid_columnconfigure(0, weight=self._menu_weight, minsize=280)
                self.grid_columnconfigure(1, weight=0, minsize=8)
                self.grid_columnconfigure(2, weight=self._cart_weight, minsize=240)
                self.grid_columnconfigure(3, weight=0, minsize=8)
                self.grid_columnconfigure(4, weight=self._queue_weight, minsize=280)

                self.left_workspace.grid(row=0, column=0, sticky="nsew", padx=(10, 2), pady=10)
                self.splitter_menu_cart.grid(row=0, column=1, sticky="ns", pady=18)
                self.sidebar_frame.grid(row=0, column=2, sticky="nsew", padx=2, pady=10)
                self.splitter_cart_queue.grid(row=0, column=3, sticky="ns", pady=18)
                self.kitchen_container.grid(row=0, column=4, sticky="nsew", padx=(2, 10), pady=10)

            elif target_mode == "2-Column Split":
                self.grid_rowconfigure(0, weight=3)
                self.grid_rowconfigure(1, weight=2, minsize=210)
                self.grid_columnconfigure(0, weight=self._split_left_weight, minsize=320)
                self.grid_columnconfigure(1, weight=0, minsize=8)
                self.grid_columnconfigure(2, weight=self._split_right_weight, minsize=260)

                self.left_workspace.grid(row=0, column=0, sticky="nsew", padx=(10, 2), pady=(10, 5))
                self.splitter_menu_cart.grid(row=0, column=1, sticky="ns", pady=(18, 10))
                self.sidebar_frame.grid(row=0, column=2, sticky="nsew", padx=(2, 10), pady=(10, 5))
                self.kitchen_container.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=(5, 10))

            else:  # Focus Menu
                self.grid_rowconfigure(0, weight=1)
                self.grid_columnconfigure(0, weight=self._split_left_weight, minsize=300)
                self.grid_columnconfigure(1, weight=0, minsize=8)
                self.grid_columnconfigure(2, weight=self._split_right_weight, minsize=250)

                self.left_workspace.grid(row=0, column=0, sticky="nsew", padx=(10, 2), pady=10)
                self.splitter_menu_cart.grid(row=0, column=1, sticky="ns", pady=18)
                self.sidebar_frame.grid(row=0, column=2, sticky="nsew", padx=(2, 10), pady=10)

        self.after_idle(self._reflow_menu_grid)

    def _update_top_bar_layout(self):
        """Prevents top_bar controls from clipping when the menu panel is slid narrow."""
        panel_w = self.left_workspace.winfo_width()
        if panel_w <= 1:
            panel_w = 560

        compact = panel_w < 610
        if compact == self._top_bar_compact:
            return
        self._top_bar_compact = compact

        self.top_bar_filters.pack_forget()
        self.quick_snap.pack_forget()

        if compact:
            self.top_bar_filters.pack(side="top", fill="x", padx=2, pady=(2, 0))
            self.quick_snap.pack(side="top", anchor="w", padx=8, pady=(0, 8))
        else:
            self.top_bar_filters.pack(side="left", fill="x", expand=True)
            self.quick_snap.pack(side="right", padx=8, pady=8)

    def _reflow_menu_grid(self):
        """Snaps menu cards into 2, 3, or 4 columns to fit panel width and active font size."""
        self._update_top_bar_layout()
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
            elif panel_w >= 460:
                cols = 3
            else:
                cols = 2

        metrics = self.controller.font_metrics
        show_icons = self.controller.settings.get("show_menu_icons", True)
        card_height = metrics["menu_card_height"] if show_icons else max(82, metrics["menu_card_height"] - 44)
        card_width = max(110, (panel_w - 36) // cols)
        wrap_len = max(95, card_width - 20)

        for idx in range(4):
            self.menu_frame.grid_columnconfigure(
                idx,
                weight=1 if idx < cols else 0,
                uniform="menu_cols" if idx < cols else "",
            )

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
        self._splitter_idle_color = c["border"]
        self._splitter_hover_color = c["primary"]

        self.configure(fg_color=c["bg_main"])
        self.top_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.sidebar_frame.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.kitchen_container.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.cart_list_frame.configure(fg_color=c["bg_input"])

        for bar in (self.splitter_menu_cart, self.splitter_cart_queue, self.splitter_kitchen):
            bar.configure(fg_color=c["border"])

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
                    children = self.top_bar_filters.winfo_children()
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

    def announce_order(self, seq_num):
        """Triggers voice paging (TTS) for a given order sequence number."""
        if hasattr(self.controller, "queue") and self.controller.queue:
            if hasattr(self.controller.queue, "announce_order"):
                self.controller.queue.announce_order(seq_num)
            elif hasattr(self.controller.queue, "_play_announcement"):
                self.controller.queue._play_announcement(seq_num)
            return

        def _speak():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(f"Order number {seq_num}, please proceed to the counter.")
                engine.runAndWait()
            except Exception as e:
                print(f"TTS announcement error: {e}")

        threading.Thread(target=_speak, daemon=True).start()

    def refresh_kitchen_queue(self, force=False):
        if self._queue_refresh_job is not None:
            self.after_cancel(self._queue_refresh_job)
            self._queue_refresh_job = None

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    orders.order_id,
                    orders.sequence_number,
                    orders.status,
                    order_items.quantity,
                    inventory.name AS item_name
                FROM orders
                JOIN order_items ON orders.order_id = order_items.order_id
                JOIN inventory ON order_items.sku = inventory.sku
                WHERE orders.status IN ('PREPARING', 'READY')
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
            orders_map[oid]["items"].append((row["quantity"], row["item_name"]))

        snapshot = tuple(
            (o["order_id"], o["status"], tuple(o["items"]))
            for o in orders_map.values()
        )

        if force or snapshot != self._last_queue_snapshot:
            self._last_queue_snapshot = snapshot
            self._render_kitchen_columns(list(orders_map.values()))

        self._queue_refresh_job = self.after(5000, self.refresh_kitchen_queue)

    def _render_kitchen_columns(self, orders):
        c = self.controller.colors
        f = self.controller.fonts

        for widget in self.prep_column.winfo_children():
            widget.destroy()
        for widget in self.ready_column.winfo_children():
            widget.destroy()

        prep_orders = [o for o in orders if o["status"] == "PREPARING"]
        ready_orders = [o for o in orders if o["status"] == "READY"]

        if not prep_orders:
            ctk.CTkLabel(
                self.prep_column,
                text="No orders preparing",
                font=f["small"],
                text_color=c["text_muted"],
            ).pack(pady=16)
        else:
            for order in prep_orders:
                self._create_prep_card(order["order_id"], order["sequence_number"], order["items"])

        if not ready_orders:
            ctk.CTkLabel(
                self.ready_column,
                text="No orders ready",
                font=f["small"],
                text_color=c["text_muted"],
            ).pack(pady=16)
        else:
            for order in ready_orders:
                self._create_ready_card(order["order_id"], order["sequence_number"], order["items"])

    def _create_prep_card(self, order_id, seq_num, items):
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
            card,
            text=f"Order #{seq_num}",
            font=f["subheader"],
            text_color=c["accent_gold"],
        ).pack(anchor="w", padx=8, pady=(6, 2))

        items_text = "\n".join(f"• {qty}x {name}" for qty, name in items)
        ctk.CTkLabel(
            card,
            text=items_text,
            font=f["small"],
            text_color=c["text_main"],
            justify="left",
            anchor="w",
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
                self.refresh_kitchen_queue(force=True),
            ],
        ).pack(fill="x", padx=8, pady=(0, 8))

    def _create_ready_card(self, order_id, seq_num, items):
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
            card,
            text=f"Order #{seq_num}",
            font=f["subheader"],
            text_color=c["text_green"],
        ).pack(anchor="w", padx=8, pady=(6, 2))

        items_text = "\n".join(f"• {qty}x {name}" for qty, name in items)
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
            command=lambda seq=seq_num: self.announce_order(seq),
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
                self.refresh_kitchen_queue(force=True),
            ],
        ).grid(row=0, column=1, sticky="ew", padx=(3, 0))