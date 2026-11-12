import customtkinter as ctk

# --- Global UI & Window Scaling ---
UI_SCALING = 1.0       # Adjusts the size of all widgets/text globally (e.g., 1.25 for touchscreens)
WINDOW_SCALING = 1.0   # Adjusts the window scaling factor
DEFAULT_GEOMETRY = "1280x720"
MIN_GEOMETRY = "1024x576"

APPEARANCE_MODE = "Dark"
COLOR_THEME = "blue"

# --- Central Color Palette ---
COLORS = {
    "bg_main": "#fdc30d",
    "bg_card": "#16213E",
    "primary": "#0F3460",
    "primary_hover": "#1A4B84",
    "accent_green": "#2E7D32",
    "green_hover": "#1B5E20",
    "accent_red": "#C62828",
    "red_hover": "#8E0000",
    "accent_gold": "#b8860b",
    "gold_hover": "#8b6508",
    "text_main": "#FFFFFF",
    "text_muted": "#A0AAB2",
    "border": "#2A3B5C"
}

# --- Reusable Font Factory ---
def get_fonts():
    # Must be called after initializing ctk.CTk() in main_gui.py
    return {
        "title": ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
        "header": ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
        "subheader": ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
        "body": ctk.CTkFont(family="Segoe UI", size=15),
        "button": ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        "menu_item": ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        "small": ctk.CTkFont(family="Segoe UI", size=12)
    }