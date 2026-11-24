import os
import json
import customtkinter as ctk
from core.paths import get_project_root

DEFAULT_GEOMETRY = "1280x720"
MIN_GEOMETRY = "820x560"

FONT_PRESETS = {
    "Small": {
        "title": 24,
        "header": 17,
        "subheader": 13,
        "body": 12,
        "button": 12,
        "menu_item": 11,
        "small": 10,
        "menu_card_height": 116,
        "menu_wrap": 120,
        "queue_wrap": 150,
    },
    "Medium": {
        "title": 28,
        "header": 20,
        "subheader": 15,
        "body": 14,
        "button": 14,
        "menu_item": 12,
        "small": 12,
        "menu_card_height": 132,
        "menu_wrap": 135,
        "queue_wrap": 170,
    },
    "Large": {
        "title": 32,
        "header": 23,
        "subheader": 17,
        "body": 16,
        "button": 16,
        "menu_item": 14,
        "small": 13,
        "menu_card_height": 152,
        "menu_wrap": 150,
        "queue_wrap": 195,
    },
}

THEME_PRESETS = {
    "Dark Slate": {
        "appearance": "Dark",
        "bg_main": "#0F172A",
        "bg_card": "#1E293B",
        "bg_input": "#0B1120",
        "border": "#334155",
        "primary": "#1D4ED8",
        "primary_hover": "#2563EB",
        "accent_gold": "#FACC15",
        "gold_hover": "#EAB308",
        "text_on_gold": "#0F172A",
        "accent_green": "#16A34A",
        "green_hover": "#15803D",
        "text_green": "#4ADE80",
        "accent_red": "#DC2626",
        "red_hover": "#B91C1C",
        "text_red": "#F87171",
        "text_main": "#F8FAFC",
        "text_muted": "#94A3B8",
    },
    "High-Contrast Dark": {
        "appearance": "Dark",
        "bg_main": "#000000",
        "bg_card": "#111827",
        "bg_input": "#030712",
        "border": "#64748B",
        "primary": "#2563EB",
        "primary_hover": "#3B82F6",
        "accent_gold": "#FDE047",
        "gold_hover": "#FACC15",
        "text_on_gold": "#000000",
        "accent_green": "#22C55E",
        "green_hover": "#16A34A",
        "text_green": "#86EFAC",
        "accent_red": "#EF4444",
        "red_hover": "#DC2626",
        "text_red": "#FCA5A5",
        "text_main": "#FFFFFF",
        "text_muted": "#CBD5E1",
    },
    "Daylight Light": {
        "appearance": "Light",
        "bg_main": "#F1F5F9",
        "bg_card": "#FFFFFF",
        "bg_input": "#E2E8F0",
        "border": "#94A3B8",
        "primary": "#1E3A8A",
        "primary_hover": "#1D4ED8",
        "accent_gold": "#F59E0B",
        "gold_hover": "#D97706",
        "text_on_gold": "#0F172A",
        "accent_green": "#15803D",
        "green_hover": "#166534",
        "text_green": "#15803D",
        "accent_red": "#B91C1C",
        "red_hover": "#991B1B",
        "text_red": "#B91C1C",
        "text_main": "#0F172A",
        "text_muted": "#475569",
    },
}

DEFAULT_SETTINGS = {
    "font_size": "Medium",          # "Small", "Medium", "Large"
    "ui_scaling": 1.0,              # 0.9, 1.0, 1.15
    "theme_name": "Dark Slate",     # "Dark Slate", "High-Contrast Dark", "Daylight Light"
    "cashier_layout": "Auto-Snap",  # "Auto-Snap", "3-Column Wide", "2-Column Split", "Focus Menu"
    "menu_columns": "Auto",         # "Auto", "2", "3", "4"
    "show_menu_icons": True,        # True / False
    "queue_refresh_sec": 5,         # 3, 5, 10, 0 (Manual)
}


def get_settings_path() -> str:
    """Stores settings.json in the project root (or next to the .exe when frozen)."""
    return os.path.join(get_project_root(), "settings.json")


def load_settings() -> dict:
    settings = DEFAULT_SETTINGS.copy()
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                settings.update(saved)
        except Exception as e:
            print(f"Settings load warning: {e}")

    if settings.get("font_size") not in FONT_PRESETS:
        settings["font_size"] = "Medium"
    if settings.get("theme_name") not in THEME_PRESETS:
        settings["theme_name"] = "Dark Slate"
    return settings


def save_settings(settings: dict) -> None:
    path = get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Settings save warning: {e}")


# Active mutable color dictionary initialized from Default Theme
COLORS = THEME_PRESETS["Dark Slate"].copy()


def apply_color_preset(colors_dict: dict, theme_name: str) -> None:
    preset = THEME_PRESETS.get(theme_name, THEME_PRESETS["Dark Slate"])
    colors_dict.clear()
    colors_dict.update(preset)
    ctk.set_appearance_mode(preset["appearance"])


def get_fonts(size_preset: str = "Medium") -> dict:
    p = FONT_PRESETS.get(size_preset, FONT_PRESETS["Medium"])
    return {
        "title": ctk.CTkFont(family="Segoe UI", size=p["title"], weight="bold"),
        "header": ctk.CTkFont(family="Segoe UI", size=p["header"], weight="bold"),
        "subheader": ctk.CTkFont(family="Segoe UI", size=p["subheader"], weight="bold"),
        "body": ctk.CTkFont(family="Segoe UI", size=p["body"]),
        "button": ctk.CTkFont(family="Segoe UI", size=p["button"], weight="bold"),
        "menu_item": ctk.CTkFont(family="Segoe UI", size=p["menu_item"], weight="bold"),
        "small": ctk.CTkFont(family="Segoe UI", size=p["small"]),
    }


def apply_font_preset(fonts_dict: dict, size_preset: str) -> None:
    """Mutates existing CTkFont instances in-place so all bound widgets update immediately."""
    p = FONT_PRESETS.get(size_preset, FONT_PRESETS["Medium"])
    for key in ("title", "header", "subheader", "body", "button", "menu_item", "small"):
        if key in fonts_dict:
            fonts_dict[key].configure(size=p[key])