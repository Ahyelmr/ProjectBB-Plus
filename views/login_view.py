import os
import sys
import customtkinter as ctk
from tkinter import messagebox
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


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        gold_text = c.get("accent_gold", c.get("brand_gold", "#FACC15"))

        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller
        self._last_logo_size = None

        # Responsive centering: weights push the center cell (row 1, column 1) to the middle
        self.grid_rowconfigure((0, 2), weight=1)
        self.grid_columnconfigure((0, 2), weight=1)

        self.login_card = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            border_width=2,
            border_color=c["border"],
            corner_radius=15
        )
        self.login_card.grid(row=1, column=1, padx=20, pady=20, ipadx=40, ipady=30)

        # Logo Label (prominent centerpiece branding)
        self.logo_label = ctk.CTkLabel(self.login_card, text="")

        self.title_label = ctk.CTkLabel(
            self.login_card,
            text="ProjectBB Plus",
            font=f["title"],
            text_color=c["text_main"]
        )
        self.title_label.pack(pady=(5, 2))

        self._update_logo(135, 135)

        self.subtitle_label = ctk.CTkLabel(
            self.login_card,
            text="POS & Kitchen Management",
            font=f["small"],
            text_color=gold_text
        )
        self.subtitle_label.pack(pady=(0, 18))

        self.username_entry = ctk.CTkEntry(
            self.login_card,
            width=280,
            height=45,
            placeholder_text="Username",
            font=f["body"],
            fg_color=c.get("bg_input", "#0B1120"),
            border_width=1,
            border_color=c["border"],
            text_color="#FFFFFF",
            placeholder_text_color=c["text_muted"]
        )
        self.username_entry.pack(pady=8)

        self.password_entry = ctk.CTkEntry(
            self.login_card,
            width=280,
            height=45,
            placeholder_text="Password",
            show="*",
            font=f["body"],
            fg_color=c.get("bg_input", "#0B1120"),
            border_width=1,
            border_color=c["border"],
            text_color="#FFFFFF",
            placeholder_text_color=c["text_muted"]
        )
        self.password_entry.pack(pady=8)

        self.login_button = ctk.CTkButton(
            self.login_card,
            text="Login",
            width=280,
            height=45,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=self.attempt_login
        )
        self.login_button.pack(pady=(20, 10))

        self.exit_button = ctk.CTkButton(
            self.login_card,
            text="Exit App",
            width=280,
            height=45,
            font=f["button"],
            fg_color=c["accent_red"],
            hover_color=c["red_hover"],
            text_color="#FFFFFF",
            command=self.exit_app
        )
        self.exit_button.pack(pady=(0, 15))

        self.username_entry.bind("<Return>", lambda _event: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda _event: self.attempt_login())
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """Scales the login logo proportionally to window height while staying within bounds."""
        if event.height > 100:
            target = max(100, min(165, int(event.height * 0.18)))
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
                    self.logo_label.pack(before=self.title_label, pady=(15, 5))
        except Exception as e:
            print(f"Logo load error (LoginFrame): {e}")

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password.")
            return

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role FROM users WHERE username = ? AND password_hash = ?",
                (username, password)
            )
            user = cursor.fetchone()

        if user:
            self.controller.current_user_role = user["role"]
            self.username_entry.delete(0, "end")
            self.password_entry.delete(0, "end")

            self.controller.frames["CashierFrame"].update_admin_features()
            self.controller.frames["CashierFrame"].load_menu()
            self.controller.show_frame("CashierFrame")
        else:
            messagebox.showerror("Authentication Failed", "Invalid username or password.")

    def exit_app(self):
        """Terminates the main loop, destroys the window, and exits the process completely."""
        self.controller.quit()
        self.controller.destroy()
        sys.exit(0)

    def apply_theme(self):
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        self.login_card.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.title_label.configure(text_color=c["text_main"])
        self.subtitle_label.configure(text_color=c["accent_gold"])
        for entry in (self.username_entry, self.password_entry):
            entry.configure(
                fg_color=c["bg_input"],
                border_color=c["border"],
                text_color=c["text_main"],
                placeholder_text_color=c["text_muted"],
            )
        self.login_button.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.exit_button.configure(fg_color=c["accent_red"], hover_color=c["red_hover"])