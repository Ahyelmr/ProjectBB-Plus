import os
import customtkinter as ctk
from PIL import Image
from core.paths import get_resource_path
from components.logo_widget import LogoLabel


class MenuPanel(ctk.CTkFrame):
    """Left Cashier workspace containing sort/category filters, global search, view switcher, and menu grid."""

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
        self._empty_state_frame = None
        self._empty_state_lbl = None
        self._empty_clear_btn = None
        self._icon_cache = {}
        self._top_bar_compact = None
        self._search_debounce_job = None
        self._last_search_query = ""

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
        self.top_bar.pack(fill="x", padx=2, pady=(0, 6))

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
            command=lambda _choice: self.load_menu(refresh_cats=False),
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
            command=self._on_category_selected,
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

        # --- Global Search Bar (Searches Across All Categories) ---
        self.search_bar = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=c["border"],
        )
        self.search_bar.pack(fill="x", padx=2, pady=(0, 8))

        self.search_lbl = ctk.CTkLabel(
            self.search_bar,
            text="Search:",
            font=f["small"],
            text_color=c["text_main"],
        )
        self.search_lbl.pack(side="left", padx=(10, 6), pady=6)

        self.search_entry = ctk.CTkEntry(
            self.search_bar,
            placeholder_text="Find item, menu category, or SKU across all categories...",
            font=f["small"],
            height=30,
            fg_color=c["bg_input"],
            border_color=c["border"],
            text_color=c["text_main"],
            placeholder_text_color=c["text_muted"],
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=6)
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)
        self.search_entry.bind("<Return>", self._on_search_submit)
        self.search_entry.bind("<Escape>", lambda _e: self.clear_search())

        self.search_status_lbl = ctk.CTkLabel(
            self.search_bar,
            text="",
            font=f["small"],
            text_color=c["text_muted"],
        )

        self.clear_search_btn = ctk.CTkButton(
            self.search_bar,
            text="Clear",
            width=58,
            height=28,
            font=f["small"],
            fg_color=c["accent_red"],
            hover_color=c["red_hover"],
            text_color="#FFFFFF",
            command=self.clear_search,
        )

        # --- Scrollable Menu Grid ---
        self.menu_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.menu_frame.pack(fill="both", expand=True)

    @staticmethod
    def _item_field(item, key: str, default: str = "") -> str:
        try:
            val = item[key]
            return default if val is None else str(val)
        except (KeyError, IndexError, TypeError):
            return default

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

    def _on_category_selected(self, _choice: str) -> None:
        """Clears active search when the user manually switches categories."""
        if self._search_debounce_job is not None:
            self.after_cancel(self._search_debounce_job)
            self._search_debounce_job = None

        if self.search_entry.get():
            self.search_entry.delete(0, "end")
        self._last_search_query = ""
        self._update_search_controls(raw_text="", match_count=None)
        self.load_menu(refresh_cats=True)

    def _on_search_key_release(self, _event) -> None:
        raw_text = self.search_entry.get()
        normalized = raw_text.strip().lower()

        # Toggle Clear button immediately based on input presence
        self._toggle_clear_button(bool(raw_text))

        if normalized == self._last_search_query:
            return

        if self._search_debounce_job is not None:
            self.after_cancel(self._search_debounce_job)
        self._search_debounce_job = self.after(120, self._run_search_refresh)

    def _on_search_submit(self, _event) -> None:
        if self._search_debounce_job is not None:
            self.after_cancel(self._search_debounce_job)
            self._search_debounce_job = None
        self._run_search_refresh()

    def _run_search_refresh(self) -> None:
        self._search_debounce_job = None
        self._last_search_query = self.search_entry.get().strip().lower()
        self.load_menu(refresh_cats=False)

    def clear_search(self) -> None:
        if self._search_debounce_job is not None:
            self.after_cancel(self._search_debounce_job)
            self._search_debounce_job = None

        had_text = bool(self.search_entry.get())
        had_query = bool(self._last_search_query)

        if had_text:
            self.search_entry.delete(0, "end")
        self._last_search_query = ""
        self._update_search_controls(raw_text="", match_count=None)

        if had_query:
            self.load_menu(refresh_cats=False)

    def _toggle_clear_button(self, visible: bool) -> None:
        if visible:
            if not self.clear_search_btn.winfo_ismapped():
                self.clear_search_btn.pack(side="right", padx=(4, 8), pady=6)
        else:
            if self.clear_search_btn.winfo_ismapped():
                self.clear_search_btn.pack_forget()

    def _update_search_controls(self, raw_text: str, match_count: int | None) -> None:
        self._toggle_clear_button(bool(raw_text))
        query = raw_text.strip()

        if query and match_count is not None:
            noun = "item" if match_count == 1 else "items"
            self.search_status_lbl.configure(text=f"All menus • {match_count} {noun}")
            if not self.search_status_lbl.winfo_ismapped():
                self.search_status_lbl.pack(side="right", padx=(2, 4), pady=6)
        else:
            if self.search_status_lbl.winfo_ismapped():
                self.search_status_lbl.pack_forget()

    def _matches_search(self, item, query: str) -> bool:
        """Matches all space-separated search terms across item name, category, and SKU."""
        tokens = query.split()
        if not tokens:
            return True
        haystack = " ".join(
            (
                self._item_field(item, "name"),
                self._item_field(item, "category"),
                self._item_field(item, "sku"),
            )
        ).lower()
        return all(token in haystack for token in tokens)

    def _load_item_icon(self, raw_path: str, default_img_path: str):
        candidate = (
            raw_path if raw_path.startswith("assets") else os.path.join("assets", raw_path) if raw_path else ""
        )
        img_path = get_resource_path(candidate) if candidate else ""

        for path in (img_path, default_img_path):
            if not path:
                continue
            if path in self._icon_cache:
                return self._icon_cache[path]
            if os.path.exists(path):
                try:
                    with Image.open(path) as pil_img:
                        copy_img = pil_img.copy()
                    icon = ctk.CTkImage(light_image=copy_img, dark_image=copy_img, size=(52, 52))
                    self._icon_cache[path] = icon
                    return icon
                except Exception:
                    continue
        return None

    def _show_empty_state(self, query: str) -> None:
        c = self.controller.colors
        f = self.controller.fonts

        for idx in range(4):
            self.menu_frame.grid_columnconfigure(idx, weight=1 if idx == 0 else 0, uniform="")

        self._empty_state_frame = ctk.CTkFrame(
            self.menu_frame,
            fg_color=c["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=c["border"],
        )
        self._empty_state_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=12, pady=24)

        message = (
            f'No items or menus matched "{query}".'
            if query
            else "No menu items available in this category."
        )
        self._empty_state_lbl = ctk.CTkLabel(
            self._empty_state_frame,
            text=message,
            font=f["body"],
            text_color=c["text_muted"],
        )
        self._empty_state_lbl.pack(pady=(18, 10), padx=16)

        if query:
            self._empty_clear_btn = ctk.CTkButton(
                self._empty_state_frame,
                text="Clear Search",
                height=32,
                font=f["small"],
                fg_color=c["primary"],
                hover_color=c["primary_hover"],
                text_color="#FFFFFF",
                command=self.clear_search,
            )
            self._empty_clear_btn.pack(pady=(0, 18))

    def load_menu(self, *_args, refresh_cats: bool = True) -> None:
        if refresh_cats:
            self.refresh_categories()

        c = self.controller.colors
        f = self.controller.fonts
        show_icons = self.controller.settings.get("show_menu_icons", True)

        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        self._menu_buttons = []
        self._empty_state_frame = None
        self._empty_state_lbl = None
        self._empty_clear_btn = None

        raw_search = self.search_entry.get()
        query = raw_search.strip().lower()
        self._last_search_query = query

        # When searching, always pull from all categories so any item/menu can be pinpointed
        target_category = "All Categories" if query else self.category_var.get()
        items = self.controller.db.get_menu_items(
            category=target_category,
            sort_by=self.sort_var.get(),
        )

        if query:
            items = [item for item in items if self._matches_search(item, query)]

        self._update_search_controls(raw_text=raw_search, match_count=len(items) if query else None)

        try:
            self.menu_frame._parent_canvas.yview_moveto(0)
        except Exception:
            pass

        if not items:
            self._show_empty_state(raw_search.strip())
            self.update_top_bar_layout()
            return

        default_img_path = get_resource_path("assets/default.png")

        for item in items:
            btn_text = f"{item['name']}\n₱{item['price']:.2f}\n({item['category']})"
            btn_image = (
                self._load_item_icon(self._item_field(item, "image_path"), default_img_path)
                if show_icons
                else None
            )

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
        self.search_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.search_entry.configure(
            fg_color=c["bg_input"],
            border_color=c["border"],
            text_color=c["text_main"],
            placeholder_text_color=c["text_muted"],
        )
        self.search_status_lbl.configure(text_color=c["text_muted"])
        self.clear_search_btn.configure(fg_color=c["accent_red"], hover_color=c["red_hover"])

        for lbl in (self.sort_lbl, self.cat_lbl, self.search_lbl):
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
        self.menu_frame.configure(
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        for btn in self._menu_buttons:
            btn.configure(
                fg_color=c["bg_card"],
                hover_color=c["primary"],
                border_color=c["border"],
                text_color=c["text_main"],
            )
        if self._empty_state_frame is not None and self._empty_state_frame.winfo_exists():
            self._empty_state_frame.configure(fg_color=c["bg_card"], border_color=c["border"])
        if self._empty_state_lbl is not None and self._empty_state_lbl.winfo_exists():
            self._empty_state_lbl.configure(text_color=c["text_muted"])
        if self._empty_clear_btn is not None and self._empty_clear_btn.winfo_exists():
            self._empty_clear_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])