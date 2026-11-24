import customtkinter as ctk
from tkinter import messagebox
from core import theme
from components.page_header import PageHeader


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller

        self._cards = []
        self._main_labels = []
        self._muted_labels = []
        self._gold_labels = []
        self._seg_buttons = []
        self._option_menus = []

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # --- Top Navigation Bar ---
        self.header = PageHeader(
            self,
            controller=controller,
            title="System Display & Usability Settings",
            back_command=lambda: controller.show_frame("CashierFrame"),
            logo_size=42,
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        self.status_badge = ctk.CTkLabel(
            self.header.right_slot, text="", font=f["small"], text_color=c["text_green"]
        )
        self.status_badge.pack(padx=4)

        # --- Scrollable Content ---
        self.scroll_body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.scroll_body.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        self.scroll_body.grid_columnconfigure((0, 1), weight=1, uniform="settings_cols")

        self._build_typography_card()
        self._build_layout_card()
        self._build_operations_card()
        self._build_bottom_bar()

        self.bind("<Configure>", lambda e: self.header.scale_logo_for_height(e.height, 36, 50, 0.055))
        self.on_show()

    def _make_card(self, row: int, col: int, title: str, desc: str = "", colspan: int = 1):
        c = self.controller.colors
        f = self.controller.fonts

        card = ctk.CTkFrame(
            self.scroll_body,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        card.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=6, pady=6)
        self._cards.append(card)

        heading = ctk.CTkLabel(card, text=title, font=f["header"], text_color=c["accent_gold"], anchor="w")
        heading.pack(fill="x", padx=16, pady=(14, 4))
        self._gold_labels.append(heading)

        if desc:
            desc_lbl = ctk.CTkLabel(
                card,
                text=desc,
                font=f["small"],
                text_color=c["text_muted"],
                wraplength=460,
                justify="left",
                anchor="w",
            )
            desc_lbl.pack(fill="x", padx=16, pady=(0, 10))
            self._muted_labels.append(desc_lbl)

        return card

    def _add_row(self, parent, label_text: str, pady: int | tuple[int, int] = 6):
        c = self.controller.colors
        f = self.controller.fonts
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=pady)
        lbl = ctk.CTkLabel(row, text=label_text, font=f["body"], text_color=c["text_main"])
        lbl.pack(side="left")
        self._main_labels.append(lbl)
        return row

    def _add_segmented(self, parent, values: list[str], font_key: str = "small", height: int = 34, command=None):
        c = self.controller.colors
        f = self.controller.fonts
        seg = ctk.CTkSegmentedButton(
            parent,
            values=values,
            font=f[font_key],
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color="#FFFFFF",
            height=height,
            command=command,
        )
        self._seg_buttons.append(seg)
        return seg

    def _add_option_menu(self, parent, values: list[str], width: int = 180):
        c = self.controller.colors
        f = self.controller.fonts
        menu = ctk.CTkOptionMenu(
            parent,
            values=values,
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            width=width,
        )
        self._option_menus.append(menu)
        return menu

    def _build_typography_card(self):
        c = self.controller.colors
        f = self.controller.fonts
        card = self._make_card(
            0,
            0,
            "1. Text Size & Readability",
            "Adjust system-wide font sizes across Menu Cards, Cart Totals, and Kitchen Tickets.",
        )

        font_row = self._add_row(card, "Font Size Preset:")
        self.font_selector = self._add_segmented(
            font_row, ["Small", "Medium", "Large"], font_key="button", height=36, command=self._on_live_preview_change
        )
        self.font_selector.pack(side="right")

        # Live Typography Preview Box
        self.preview_box = ctk.CTkFrame(
            card, fg_color=c["bg_input"], corner_radius=10, border_width=1, border_color=c["border"]
        )
        self.preview_box.pack(fill="x", padx=16, pady=10)

        preview_title = ctk.CTkLabel(
            self.preview_box,
            text="Live Text Preview — Order #104",
            font=f["subheader"],
            text_color=c["accent_gold"],
            anchor="w",
        )
        preview_title.pack(fill="x", padx=12, pady=(10, 2))
        self._gold_labels.append(preview_title)

        preview_body = ctk.CTkLabel(
            self.preview_box,
            text="2x Beef Shawarma Rice (Rice Meals)  —  ₱258.00",
            font=f["body"],
            text_color=c["text_main"],
            anchor="w",
        )
        preview_body.pack(fill="x", padx=12, pady=2)
        self._main_labels.append(preview_body)

        preview_sub = ctk.CTkLabel(
            self.preview_box,
            text="Subtotal & modifier note readability sample",
            font=f["small"],
            text_color=c["text_muted"],
            anchor="w",
        )
        preview_sub.pack(fill="x", padx=12, pady=(0, 10))
        self._muted_labels.append(preview_sub)

        scale_row = self._add_row(card, "Touchscreen UI Scale:")
        self.scale_selector = self._add_segmented(scale_row, ["90%", "100%", "115%"])
        self.scale_selector.pack(side="right")

        theme_row = self._add_row(card, "Color Contrast Mode:", pady=(6, 16))
        self.theme_menu = self._add_option_menu(theme_row, list(theme.THEME_PRESETS.keys()))
        self.theme_menu.pack(side="right")

    def _build_layout_card(self):
        c = self.controller.colors
        card = self._make_card(
            0,
            1,
            "2. Cashier Grid & Window Snapping",
            "Control how Cashier panels snap into place when resizing or snapping windows.",
        )

        snap_row = self._add_row(card, "Window Snap Mode:")
        self.snap_menu = self._add_option_menu(
            snap_row, ["Auto-Snap", "3-Column Wide", "2-Column Split", "Focus Menu"]
        )
        self.snap_menu.pack(side="right")

        cols_row = self._add_row(card, "Menu Grid Columns:")
        self.cols_selector = self._add_segmented(cols_row, ["Auto", "2", "3", "4"])
        self.cols_selector.pack(side="right")

        icons_row = self._add_row(card, "Show Menu Item Icons (Disable for larger text):", pady=10)
        self.icons_switch = ctk.CTkSwitch(
            icons_row, text="", onvalue=True, offvalue=False, progress_color=c["accent_green"]
        )
        self.icons_switch.pack(side="right")

    def _build_operations_card(self):
        c = self.controller.colors
        f = self.controller.fonts
        card = self._make_card(1, 0, "3. Kitchen Queue & Voice Paging Usability", colspan=2)

        ops_row = self._add_row(card, "Live Queue Auto-Refresh Interval:", pady=(4, 14))
        self.refresh_selector = self._add_segmented(ops_row, ["3s", "5s", "10s", "Manual"])
        self.refresh_selector.pack(side="left", padx=14)

        self.tts_test_btn = ctk.CTkButton(
            ops_row,
            text="Test Voice Paging (TTS)",
            height=36,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=self._test_tts,
        )
        self.tts_test_btn.pack(side="right")

    def _build_bottom_bar(self):
        c = self.controller.colors
        f = self.controller.fonts
        self.bottom_bar = ctk.CTkFrame(
            self, fg_color=c["bg_card"], corner_radius=12, border_width=1, border_color=c["border"]
        )
        self.bottom_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(6, 10))
        self._cards.append(self.bottom_bar)

        self.reset_btn = ctk.CTkButton(
            self.bottom_bar,
            text="Reset to Defaults",
            height=38,
            font=f["button"],
            fg_color=c["accent_red"],
            hover_color=c["red_hover"],
            text_color="#FFFFFF",
            command=self._reset_defaults,
        )
        self.reset_btn.pack(side="left", padx=14, pady=10)

        self.apply_btn = ctk.CTkButton(
            self.bottom_bar,
            text="Apply & Save Settings",
            height=38,
            width=210,
            font=f["button"],
            fg_color=c["accent_green"],
            hover_color=c["green_hover"],
            text_color="#FFFFFF",
            command=self._save_and_apply,
        )
        self.apply_btn.pack(side="right", padx=14, pady=10)

    def on_show(self):
        s = self.controller.settings
        self.font_selector.set(s.get("font_size", "Medium"))

        scale_pct = f"{int(round(float(s.get('ui_scaling', 1.0)) * 100))}%"
        self.scale_selector.set(scale_pct if scale_pct in ("90%", "100%", "115%") else "100%")

        self.theme_menu.set(s.get("theme_name", "Dark Slate"))
        self.snap_menu.set(s.get("cashier_layout", "Auto-Snap"))
        self.cols_selector.set(str(s.get("menu_columns", "Auto")))

        if s.get("show_menu_icons", True):
            self.icons_switch.select()
        else:
            self.icons_switch.deselect()

        sec = int(s.get("queue_refresh_sec", 5))
        self.refresh_selector.set("Manual" if sec == 0 else f"{sec}s")
        self.status_badge.configure(text="")

    def _on_live_preview_change(self, selected_size: str):
        theme.apply_font_preset(self.controller.fonts, selected_size)
        self.controller.font_metrics = theme.FONT_PRESETS[selected_size]

    def _save_and_apply(self):
        scale_map = {"90%": 0.9, "100%": 1.0, "115%": 1.15}
        refresh_map = {"3s": 3, "5s": 5, "10s": 10, "Manual": 0}

        new_settings = {
            "font_size": self.font_selector.get(),
            "ui_scaling": scale_map.get(self.scale_selector.get(), 1.0),
            "theme_name": self.theme_menu.get(),
            "cashier_layout": self.snap_menu.get(),
            "menu_columns": self.cols_selector.get(),
            "show_menu_icons": bool(self.icons_switch.get()),
            "queue_refresh_sec": refresh_map.get(self.refresh_selector.get(), 5),
        }
        self.controller.apply_preferences(new_settings)
        self.status_badge.configure(text="✓ Settings Saved & Applied")

    def _reset_defaults(self):
        if messagebox.askyesno("Reset Settings", "Restore all display and usability settings to defaults?"):
            self.controller.apply_preferences(theme.DEFAULT_SETTINGS.copy())
            self.on_show()
            self.status_badge.configure(text="✓ Restored Defaults")

    def _test_tts(self):
        self.controller.tts.announce_order(1)

    def apply_theme(self):
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        self.header.apply_theme()
        self.preview_box.configure(fg_color=c["bg_input"], border_color=c["border"])

        for card in self._cards:
            card.configure(fg_color=c["bg_card"], border_color=c["border"])
        for lbl in self._main_labels:
            lbl.configure(text_color=c["text_main"])
        for lbl in self._muted_labels:
            lbl.configure(text_color=c["text_muted"])
        for lbl in self._gold_labels:
            lbl.configure(text_color=c["accent_gold"])

        self.status_badge.configure(text_color=c["text_green"])
        self.apply_btn.configure(fg_color=c["accent_green"], hover_color=c["green_hover"])
        self.reset_btn.configure(fg_color=c["accent_red"], hover_color=c["red_hover"])
        self.tts_test_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.icons_switch.configure(progress_color=c["accent_green"])

        for seg in self._seg_buttons:
            seg.configure(
                fg_color=c["bg_input"],
                selected_color=c["primary"],
                selected_hover_color=c["primary_hover"],
                unselected_color=c["bg_input"],
                unselected_hover_color=c["border"],
            )
        for menu in self._option_menus:
            menu.configure(
                fg_color=c["primary"],
                button_color=c["primary_hover"],
                button_hover_color=c["primary_hover"],
            )