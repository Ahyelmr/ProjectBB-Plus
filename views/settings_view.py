import os
import sys
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import theme


def get_resource_path(relative_path):
    if not relative_path:
        return ""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller
        self._last_logo_size = None

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # --- Top Navigation Bar ---
        self.top_bar = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        self.back_btn = ctk.CTkButton(
            self.top_bar,
            text="Back to Cashier",
            width=145,
            height=38,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda: controller.show_frame("CashierFrame"),
        )
        self.back_btn.pack(side="left", padx=12, pady=10)

        self.header_center = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.header_center.pack(side="left", expand=True)

        self.logo_label = ctk.CTkLabel(self.header_center, text="")

        self.title_label = ctk.CTkLabel(
            self.header_center,
            text="System Display & Usability Settings",
            font=f["header"],
            text_color=c["text_main"],
        )
        self.title_label.pack(side="left", padx=6)

        self._update_logo(42, 42)

        self.status_badge = ctk.CTkLabel(
            self.top_bar,
            text="",
            font=f["small"],
            text_color=c["text_green"],
        )
        self.status_badge.pack(side="right", padx=14)

        # --- Scrollable Settings Content ---
        self.scroll_body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.scroll_body.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        self.scroll_body.grid_columnconfigure((0, 1), weight=1, uniform="settings_cols")

        # ================= CARD 1: Typography & Readability =================
        self.typo_card = self._make_section_card(self.scroll_body, row=0, col=0)

        self.typo_heading = ctk.CTkLabel(
            self.typo_card,
            text="1. Text Size & Readability",
            font=f["header"],
            text_color=c["accent_gold"],
            anchor="w",
        )
        self.typo_heading.pack(fill="x", padx=16, pady=(14, 4))

        self.typo_desc = ctk.CTkLabel(
            self.typo_card,
            text="Adjust system-wide font sizes across Menu Cards, Cart Totals, and Kitchen Tickets.",
            font=f["small"],
            text_color=c["text_muted"],
            wraplength=460,
            justify="left",
            anchor="w",
        )
        self.typo_desc.pack(fill="x", padx=16, pady=(0, 10))

        # Font Size Selector (Small / Medium / Large)
        self.font_row = ctk.CTkFrame(self.typo_card, fg_color="transparent")
        self.font_row.pack(fill="x", padx=16, pady=6)

        self.font_lbl = ctk.CTkLabel(
            self.font_row, text="Font Size Preset:", font=f["body"], text_color=c["text_main"]
        )
        self.font_lbl.pack(side="left")

        self.font_selector = ctk.CTkSegmentedButton(
            self.font_row,
            values=["Small", "Medium", "Large"],
            font=f["button"],
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color="#FFFFFF",
            height=36,
            command=self._on_live_preview_change,
        )
        self.font_selector.pack(side="right")

        # Live Typography Preview Box
        self.preview_box = ctk.CTkFrame(
            self.typo_card,
            fg_color=c["bg_input"],
            corner_radius=10,
            border_width=1,
            border_color=c["border"],
        )
        self.preview_box.pack(fill="x", padx=16, pady=10)

        self.preview_title = ctk.CTkLabel(
            self.preview_box,
            text="Live Text Preview — Order #104",
            font=f["subheader"],
            text_color=c["accent_gold"],
            anchor="w",
        )
        self.preview_title.pack(fill="x", padx=12, pady=(10, 2))

        self.preview_body = ctk.CTkLabel(
            self.preview_box,
            text="2x Beef Shawarma Rice (Rice Meals)  —  ₱258.00",
            font=f["body"],
            text_color=c["text_main"],
            anchor="w",
        )
        self.preview_body.pack(fill="x", padx=12, pady=2)

        self.preview_sub = ctk.CTkLabel(
            self.preview_box,
            text="Subtotal & modifier note readability sample",
            font=f["small"],
            text_color=c["text_muted"],
            anchor="w",
        )
        self.preview_sub.pack(fill="x", padx=12, pady=(0, 10))

        # UI Touch Target Scaling
        self.scale_row = ctk.CTkFrame(self.typo_card, fg_color="transparent")
        self.scale_row.pack(fill="x", padx=16, pady=6)

        self.scale_lbl = ctk.CTkLabel(
            self.scale_row, text="Touchscreen UI Scale:", font=f["body"], text_color=c["text_main"]
        )
        self.scale_lbl.pack(side="left")

        self.scale_selector = ctk.CTkSegmentedButton(
            self.scale_row,
            values=["90%", "100%", "115%"],
            font=f["small"],
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color="#FFFFFF",
            height=34,
        )
        self.scale_selector.pack(side="right")

        # Contrast & Color Theme
        self.theme_row = ctk.CTkFrame(self.typo_card, fg_color="transparent")
        self.theme_row.pack(fill="x", padx=16, pady=(6, 16))

        self.theme_lbl = ctk.CTkLabel(
            self.theme_row, text="Color Contrast Mode:", font=f["body"], text_color=c["text_main"]
        )
        self.theme_lbl.pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            self.theme_row,
            values=list(theme.THEME_PRESETS.keys()),
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            width=180,
        )
        self.theme_menu.pack(side="right")

        # ================= CARD 2: Cashier Grid & Snapping =================
        self.layout_card = self._make_section_card(self.scroll_body, row=0, col=1)

        self.layout_heading = ctk.CTkLabel(
            self.layout_card,
            text="2. Cashier Grid & Window Snapping",
            font=f["header"],
            text_color=c["accent_gold"],
            anchor="w",
        )
        self.layout_heading.pack(fill="x", padx=16, pady=(14, 4))

        self.layout_desc = ctk.CTkLabel(
            self.layout_card,
            text="Control how Cashier panels snap into place when resizing or snapping windows.",
            font=f["small"],
            text_color=c["text_muted"],
            wraplength=460,
            justify="left",
            anchor="w",
        )
        self.layout_desc.pack(fill="x", padx=16, pady=(0, 10))

        # Layout Snap Mode
        self.snap_row = ctk.CTkFrame(self.layout_card, fg_color="transparent")
        self.snap_row.pack(fill="x", padx=16, pady=6)

        self.snap_lbl = ctk.CTkLabel(
            self.snap_row, text="Window Snap Mode:", font=f["body"], text_color=c["text_main"]
        )
        self.snap_lbl.pack(side="left")

        self.snap_menu = ctk.CTkOptionMenu(
            self.snap_row,
            values=["Auto-Snap", "3-Column Wide", "2-Column Split", "Focus Menu"],
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            width=180,
        )
        self.snap_menu.pack(side="right")

        # Menu Grid Columns
        self.cols_row = ctk.CTkFrame(self.layout_card, fg_color="transparent")
        self.cols_row.pack(fill="x", padx=16, pady=6)

        self.cols_lbl = ctk.CTkLabel(
            self.cols_row, text="Menu Grid Columns:", font=f["body"], text_color=c["text_main"]
        )
        self.cols_lbl.pack(side="left")

        self.cols_selector = ctk.CTkSegmentedButton(
            self.cols_row,
            values=["Auto", "2", "3", "4"],
            font=f["small"],
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color="#FFFFFF",
            height=34,
        )
        self.cols_selector.pack(side="right")

        # Show/Hide Menu Icons Switch
        self.icons_row = ctk.CTkFrame(self.layout_card, fg_color="transparent")
        self.icons_row.pack(fill="x", padx=16, pady=10)

        self.icons_lbl = ctk.CTkLabel(
            self.icons_row,
            text="Show Menu Item Icons (Disable for larger text):",
            font=f["body"],
            text_color=c["text_main"],
        )
        self.icons_lbl.pack(side="left")

        self.icons_switch = ctk.CTkSwitch(
            self.icons_row,
            text="",
            onvalue=True,
            offvalue=False,
            progress_color=c["accent_green"],
        )
        self.icons_switch.pack(side="right")

        # ================= CARD 3: Kitchen Sync & Voice Paging =================
        self.ops_card = self._make_section_card(self.scroll_body, row=1, col=0, colspan=2)

        self.ops_heading = ctk.CTkLabel(
            self.ops_card,
            text="3. Kitchen Queue & Voice Paging Usability",
            font=f["header"],
            text_color=c["accent_gold"],
            anchor="w",
        )
        self.ops_heading.pack(fill="x", padx=16, pady=(14, 6))

        self.ops_row = ctk.CTkFrame(self.ops_card, fg_color="transparent")
        self.ops_row.pack(fill="x", padx=16, pady=(4, 14))

        self.refresh_lbl = ctk.CTkLabel(
            self.ops_row,
            text="Live Queue Auto-Refresh Interval:",
            font=f["body"],
            text_color=c["text_main"],
        )
        self.refresh_lbl.pack(side="left")

        self.refresh_selector = ctk.CTkSegmentedButton(
            self.ops_row,
            values=["3s", "5s", "10s", "Manual"],
            font=f["small"],
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color="#FFFFFF",
            height=34,
        )
        self.refresh_selector.pack(side="left", padx=14)

        self.tts_test_btn = ctk.CTkButton(
            self.ops_row,
            text="Test Voice Paging (TTS)",
            height=36,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=self._test_tts,
        )
        self.tts_test_btn.pack(side="right")

        # --- Bottom Save / Reset Bar ---
        self.bottom_bar = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        self.bottom_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(6, 10))

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

        self.bind("<Configure>", self._on_resize)
        self.on_show()

    def _make_section_card(self, parent, row, col, colspan=1):
        c = self.controller.colors
        card = ctk.CTkFrame(
            parent,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        card.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=6, pady=6)
        return card

    def on_show(self):
        """Syncs controls with currently active controller settings."""
        s = self.controller.settings
        self.font_selector.set(s.get("font_size", "Medium"))

        scale_pct = f"{int(round(float(s.get('ui_scaling', 1.0)) * 100))}%"
        if scale_pct not in ("90%", "100%", "115%"):
            scale_pct = "100%"
        self.scale_selector.set(scale_pct)

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

    def _on_live_preview_change(self, selected_size):
        """Immediately previews font preset across the entire app when clicked."""
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
        self.controller.frames["CashierFrame"].announce_order(1)

    def apply_theme(self):
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        for bar in (self.top_bar, self.bottom_bar, self.typo_card, self.layout_card, self.ops_card):
            bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.preview_box.configure(fg_color=c["bg_input"], border_color=c["border"])

        for lbl in (
            self.title_label, self.font_lbl, self.scale_lbl, self.theme_lbl,
            self.snap_lbl, self.cols_lbl, self.icons_lbl, self.refresh_lbl, self.preview_body
        ):
            lbl.configure(text_color=c["text_main"])

        for muted in (self.typo_desc, self.layout_desc, self.preview_sub):
            muted.configure(text_color=c["text_muted"])

        for gold in (self.typo_heading, self.layout_heading, self.ops_heading, self.preview_title):
            gold.configure(text_color=c["accent_gold"])

        self.status_badge.configure(text_color=c["text_green"])
        self.back_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.apply_btn.configure(fg_color=c["accent_green"], hover_color=c["green_hover"])
        self.reset_btn.configure(fg_color=c["accent_red"], hover_color=c["red_hover"])
        self.tts_test_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )

        for seg in (self.font_selector, self.scale_selector, self.cols_selector, self.refresh_selector):
            seg.configure(
                fg_color=c["bg_input"],
                selected_color=c["primary"],
                selected_hover_color=c["primary_hover"],
                unselected_color=c["bg_input"],
                unselected_hover_color=c["border"],
            )

        for menu in (self.theme_menu, self.snap_menu):
            menu.configure(
                fg_color=c["primary"],
                button_color=c["primary_hover"],
                button_hover_color=c["primary_hover"],
            )

    def _on_resize(self, event):
        if event.height > 100:
            target = max(36, min(50, int(event.height * 0.055)))
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
            print(f"Logo load error (SettingsFrame): {e}")