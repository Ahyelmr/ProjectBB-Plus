import customtkinter as ctk
from components.split_pane import VerticalSplitter
from views.cashier.menu_panel import MenuPanel
from views.cashier.cart_panel import CartPanel
from views.cashier.live_queue_panel import LiveQueuePanel


class CashierFrame(ctk.CTkFrame):
    """Main POS Cashier screen orchestrating MenuPanel, CartPanel, and LiveQueuePanel."""

    SNAP_FROM_UI = {
        "Auto": "Auto-Snap",
        "3-Col": "3-Column Wide",
        "Split": "2-Column Split",
        "Focus": "Focus Menu",
    }

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=controller.colors["bg_main"])
        self.controller = controller
        self._active_snap_mode = None
        self._resize_debounce_job = None

        # 3-Column main weights (sum = 100)
        self._menu_weight = 48
        self._cart_weight = 25
        self._queue_weight = 27

        # 2-Column / Focus split weights (sum = 100)
        self._split_left_weight = 60
        self._split_right_weight = 40

        self.cart_panel = CartPanel(
            self,
            controller=controller,
            on_order_completed=lambda: self.refresh_kitchen_queue(force=True),
        )
        self.menu_panel = MenuPanel(
            self,
            controller=controller,
            on_add_item=self.cart_panel.add_item,
            on_snap_select=self._on_quick_snap_select,
        )
        self.queue_panel = LiveQueuePanel(self, controller=controller)

        self.splitter_menu_cart = VerticalSplitter(
            self,
            colors=controller.colors,
            on_drag=self._on_menu_cart_drag,
            on_release=lambda _e: self.menu_panel.reflow_grid(),
        )
        self.splitter_cart_queue = VerticalSplitter(
            self,
            colors=controller.colors,
            on_drag=self._on_cart_queue_drag,
            on_release=lambda _e: self.menu_panel.reflow_grid(),
        )

        self.bind("<Configure>", self._on_configure)
        self._apply_responsive_layout(1280)
        self.load_menu()
        self.refresh_kitchen_queue(force=True)

    @property
    def cart(self) -> dict:
        return self.cart_panel.cart

    # =========================================================================
    # RESPONSIVE GRID & MULTI-SPLITTER ENGINE
    # =========================================================================
    def _on_quick_snap_select(self, choice: str) -> None:
        self.controller.settings["cashier_layout"] = self.SNAP_FROM_UI.get(choice, "Auto-Snap")
        self._active_snap_mode = None
        self._apply_responsive_layout(self.winfo_width() or 1280)

    def _on_menu_cart_drag(self, _event) -> None:
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

        self.menu_panel.update_top_bar_layout()

    def _on_cart_queue_drag(self, _event) -> None:
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

    def _on_configure(self, event) -> None:
        if event.widget is not self:
            return
        self.menu_panel.scale_logo_for_height(event.height)

        if self._resize_debounce_job is not None:
            self.after_cancel(self._resize_debounce_job)
        self._resize_debounce_job = self.after(
            60, lambda w=event.width: self._apply_responsive_layout(w)
        )

    def _apply_responsive_layout(self, width: int) -> None:
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

            for widget in (
                self.menu_panel,
                self.splitter_menu_cart,
                self.cart_panel,
                self.splitter_cart_queue,
                self.queue_panel,
            ):
                widget.grid_forget()

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

                self.menu_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 2), pady=10)
                self.splitter_menu_cart.grid(row=0, column=1, sticky="ns", pady=18)
                self.cart_panel.grid(row=0, column=2, sticky="nsew", padx=2, pady=10)
                self.splitter_cart_queue.grid(row=0, column=3, sticky="ns", pady=18)
                self.queue_panel.grid(row=0, column=4, sticky="nsew", padx=(2, 10), pady=10)

            elif target_mode == "2-Column Split":
                self.grid_rowconfigure(0, weight=3)
                self.grid_rowconfigure(1, weight=2, minsize=210)
                self.grid_columnconfigure(0, weight=self._split_left_weight, minsize=320)
                self.grid_columnconfigure(1, weight=0, minsize=8)
                self.grid_columnconfigure(2, weight=self._split_right_weight, minsize=260)

                self.menu_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 2), pady=(10, 5))
                self.splitter_menu_cart.grid(row=0, column=1, sticky="ns", pady=(18, 10))
                self.cart_panel.grid(row=0, column=2, sticky="nsew", padx=(2, 10), pady=(10, 5))
                self.queue_panel.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=(5, 10))

            else:  # Focus Menu
                self.grid_rowconfigure(0, weight=1)
                self.grid_columnconfigure(0, weight=self._split_left_weight, minsize=300)
                self.grid_columnconfigure(1, weight=0, minsize=8)
                self.grid_columnconfigure(2, weight=self._split_right_weight, minsize=250)

                self.menu_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 2), pady=10)
                self.splitter_menu_cart.grid(row=0, column=1, sticky="ns", pady=18)
                self.cart_panel.grid(row=0, column=2, sticky="nsew", padx=(2, 10), pady=10)

        self.after_idle(self.menu_panel.reflow_grid)

    # =========================================================================
    # PUBLIC CONTROLLER & VIEW HOOKS
    # =========================================================================
    def on_show(self) -> None:
        self.refresh_kitchen_queue(force=True)

    def load_menu(self, *_args) -> None:
        self.menu_panel.load_menu()

    def refresh_kitchen_queue(self, force: bool = False) -> None:
        self.queue_panel.refresh(force=force)

    def update_admin_features(self) -> None:
        self.cart_panel.update_admin_features()

    def update_cart_display(self) -> None:
        self.cart_panel.update_display()

    def announce_order(self, seq_num: int | str, order_type: str | None = None) -> None:
        self.controller.tts.announce_order(seq_num, order_type=order_type)

    def apply_theme(self) -> None:
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        self.splitter_menu_cart.apply_theme(c)
        self.splitter_cart_queue.apply_theme(c)
        self.menu_panel.apply_theme()
        self.cart_panel.apply_theme()
        self.queue_panel.apply_theme()

    def on_settings_updated(self) -> None:
        self.menu_panel.set_snap_from_layout(self.controller.settings.get("cashier_layout", "Auto-Snap"))
        self._active_snap_mode = None
        self._apply_responsive_layout(self.winfo_width() or 1280)
        self.load_menu()
        self.update_cart_display()
        self.refresh_kitchen_queue(force=True)