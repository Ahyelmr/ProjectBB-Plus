import os
import customtkinter as ctk
from PIL import Image
from core.paths import get_resource_path
from components.logo_widget import LogoLabel


class MenuPanel(ctk.CTkFrame):
    """Left Cashier workspace containing sort/category filters, view switcher, and menu grid."""

    SNAP_TO_UI = {
        "Auto-Snap": "Auto",
        "3-Column Wide": "3-Col",
        "2-Column Split": "Split",
        "Focus Menu": "Focus",
    }

    def __init__(self, parent, controller, on_add_item, on_snap_select):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.on_add_item = on_add_item
        self.on_snap_select = on_snap_select

        self._menu_buttons = []
        self._top_bar_compact = None

        c = controller.colors
        f = controller.fonts

        # --- Top Filter & View Switcher Bar ---
        self.top_bar = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=c["border"],
        )
        self.top_bar.pack(fill="x", padx=2, pady=(0, 8))

        self.top_bar_filters = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.top_bar_filters.pack(side="left", fill="x", expand=True)

        self.logo = LogoLabel(self.top_bar_filters, initial_size=(38, 38))
        if self.logo.has_logo:
            self.logo.pack(side="left", padx=(6, 4))

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
            command=self.on_snap_select,
        )
        self.quick_snap.set("Auto")
        self.quick_snap.pack(side="right", padx=8, pady=8)

        # --- Scrollable Menu Grid ---
        self.menu_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.menu_frame.pack(fill="both", expand=True)

    def scale_logo_for_height(self, height: int) -> None:
        if height > 100 and self.logo.has_logo:
            target = max(32, min(44, int(height * 0.05)))
            self.logo.set_max_size(target, target)

    def set_snap_from_layout(self, layout_name: str) -> None:
        self.quick_snap.set(self.SNAP_TO_UI.get(layout_name, "Auto"))

    def refresh_categories(self) -> None:
        categories = self.controller.db.get_inventory_categories()
        options = ["All Categories"] + categories
        self.category_menu.configure(values=options)
        if self.category_var.get() not in options:
            self.category_var.set("All Categories")

    def _load_item_icon(self, raw_path: str, default_img_path: str):
        candidate = (
            raw_path if raw_path.startswith("assets") else os.path.join("assets", raw_path) if raw_path else ""
        )
        img_path = get_resource_path(candidate) if candidate else ""

        for path in (img_path, default_img_path):
            if path and os.path.exists(path):
                try:
                    with Image.open(path) as pil_img:
                        copy_img = pil_img.copy()
                    return ctk.CTkImage(light_image=copy_img, dark_image=copy_img, size=(52, 52))
                except Exception:
                    continue
        return None

    def load_menu(self, *_args) -> None:
        self.refresh_categories()
        c = self.controller.colors
        f = self.controller.fonts
        show_icons = self.controller.settings.get("show_menu_icons", True)

        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        self._menu_buttons = []

        items = self.controller.db.get_menu_items(
            category=self.category_var.get(),
            sort_by=self.sort_var.get(),
        )
        default_img_path = get_resource_path("assets/default.png")

        for item in items:
            btn_text = f"{item['name']}\n₱{item['price']:.2f}\n({item['category']})"
            btn_image = self._load_item_icon(item["image_path"] or "", default_img_path) if show_icons else None

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
                command=lambda i=item: self.on_add_item(i),
            )
            self._menu_buttons.append(btn)

        self.reflow_grid()

    def update_top_bar_layout(self) -> None:
        """Prevents top_bar controls from clipping when the menu panel is slid narrow."""
        panel_w = self.winfo_width()
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

    def reflow_grid(self) -> None:
        """Snaps menu cards into 2, 3, or 4 columns to fit panel width and active font size."""
        self.update_top_bar_layout()
        if not self._menu_buttons:
            return

        col_pref = str(self.controller.settings.get("menu_columns", "Auto"))
        panel_w = self.winfo_width()
        if panel_w <= 1:
            panel_w = 540

        if col_pref in ("2", "3", "4"):
            cols = int(col_pref)
        elif panel_w >= 720:
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

    def apply_theme(self) -> None:
        c = self.controller.colors
        self.top_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        for lbl in (self.sort_lbl, self.cat_lbl):
            lbl.configure(text_color=c["text_main"])
        for menu in (self.sort_menu, self.category_menu):
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
        for btn in self._menu_buttons:
            btn.configure(
                fg_color=c["bg_card"],
                hover_color=c["primary"],
                border_color=c["border"],
                text_color=c["text_main"],
            )