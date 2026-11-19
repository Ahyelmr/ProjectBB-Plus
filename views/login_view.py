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
        self._mode = "login"

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
        self.login_card.grid(row=1, column=1, padx=20, pady=20, ipadx=40, ipady=25)

        # Logo Label (prominent centerpiece branding)
        self.logo_label = ctk.CTkLabel(self.login_card, text="")

        self.title_label = ctk.CTkLabel(
            self.login_card,
            text="ProjectBB Plus",
            font=f["title"],
            text_color=c["text_main"]
        )
        self.title_label.pack(pady=(5, 2))

        self._update_logo(115, 115)

        self.subtitle_label = ctk.CTkLabel(
            self.login_card,
            text="POS & Kitchen Management",
            font=f["small"],
            text_color=gold_text
        )
        self.subtitle_label.pack(pady=(0, 12))

        # --- Container 1: Login Form ---
        self.login_form_frame = ctk.CTkFrame(self.login_card, fg_color="transparent")

        self.username_label = ctk.CTkLabel(
            self.login_form_frame,
            text="Username",
            font=f["small"],
            text_color=c["text_muted"]
        )
        self.username_label.pack(anchor="w", pady=(2, 2))

        self.username_entry = ctk.CTkEntry(
            self.login_form_frame,
            width=280,
            height=42,
            font=f["body"],
            fg_color=c.get("bg_input", "#0B1120"),
            border_width=1,
            border_color=c["border"],
            text_color=c.get("text_main", "#FFFFFF"),
        )
        self.username_entry.pack(pady=(0, 8))

        self.password_label = ctk.CTkLabel(
            self.login_form_frame,
            text="Password",
            font=f["small"],
            text_color=c["text_muted"]
        )
        self.password_label.pack(anchor="w", pady=(2, 2))

        self.password_entry = ctk.CTkEntry(
            self.login_form_frame,
            width=280,
            height=42,
            show="*",
            font=f["body"],
            fg_color=c.get("bg_input", "#0B1120"),
            border_width=1,
            border_color=c["border"],
            text_color=c.get("text_main", "#FFFFFF"),
        )
        self.password_entry.pack(pady=(0, 4))

        self.login_show_pw_var = ctk.BooleanVar(value=False)
        self.login_show_pw_checkbox = ctk.CTkCheckBox(
            self.login_form_frame,
            text="Show Password",
            variable=self.login_show_pw_var,
            font=f["small"],
            text_color=c["text_muted"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            border_color=c["border"],
            command=self._toggle_login_password_visibility
        )
        self.login_show_pw_checkbox.pack(anchor="w", pady=(4, 12))

        self.login_button = ctk.CTkButton(
            self.login_form_frame,
            text="Login",
            width=280,
            height=44,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=self.attempt_login
        )
        self.login_button.pack(pady=(4, 10))

        self.create_account_nav_btn = ctk.CTkButton(
            self.login_form_frame,
            text="Create Account",
            width=280,
            height=42,
            font=f["button"],
            fg_color=c.get("bg_input", "#0B1120"),
            hover_color=c["border"],
            border_width=1,
            border_color=gold_text,
            text_color=gold_text,
            command=self.show_register_mode
        )
        self.create_account_nav_btn.pack(pady=(0, 10))

        self.exit_button = ctk.CTkButton(
            self.login_form_frame,
            text="Exit App",
            width=280,
            height=42,
            font=f["button"],
            fg_color=c["accent_red"],
            hover_color=c["red_hover"],
            text_color="#FFFFFF",
            command=self.exit_app
        )
        self.exit_button.pack(pady=(0, 8))

        # --- Container 2: User Account Creation Form ---
        self.register_form_frame = ctk.CTkFrame(self.login_card, fg_color="transparent")

        self.role_label = ctk.CTkLabel(
            self.register_form_frame,
            text="Account Type",
            font=f["small"],
            text_color=c["text_muted"]
        )
        self.role_label.pack(anchor="w", pady=(2, 3))

        self.role_selector = ctk.CTkSegmentedButton(
            self.register_form_frame,
            values=["Staff", "Admin"],
            width=280,
            height=36,
            font=f["button"],
            fg_color=c.get("bg_input", "#0B1120"),
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c.get("bg_input", "#0B1120"),
            unselected_hover_color=c["border"],
            text_color="#FFFFFF"
        )
        self.role_selector.set("Staff")
        self.role_selector.pack(pady=(0, 8))

        self.reg_username_label = ctk.CTkLabel(
            self.register_form_frame,
            text="Username (min. 3 characters)",
            font=f["small"],
            text_color=c["text_muted"]
        )
        self.reg_username_label.pack(anchor="w", pady=(2, 2))

        self.reg_username_entry = ctk.CTkEntry(
            self.register_form_frame,
            width=280,
            height=38,
            font=f["body"],
            fg_color=c.get("bg_input", "#0B1120"),
            border_width=1,
            border_color=c["border"],
            text_color=c.get("text_main", "#FFFFFF"),
        )
        self.reg_username_entry.pack(pady=(0, 6))

        self.reg_password_label = ctk.CTkLabel(
            self.register_form_frame,
            text="Password (min. 6 characters)",
            font=f["small"],
            text_color=c["text_muted"]
        )
        self.reg_password_label.pack(anchor="w", pady=(2, 2))

        self.reg_password_entry = ctk.CTkEntry(
            self.register_form_frame,
            width=280,
            height=38,
            show="*",
            font=f["body"],
            fg_color=c.get("bg_input", "#0B1120"),
            border_width=1,
            border_color=c["border"],
            text_color=c.get("text_main", "#FFFFFF"),
        )
        self.reg_password_entry.pack(pady=(0, 6))

        self.reg_confirm_label = ctk.CTkLabel(
            self.register_form_frame,
            text="Confirm Password",
            font=f["small"],
            text_color=c["text_muted"]
        )
        self.reg_confirm_label.pack(anchor="w", pady=(2, 2))

        self.reg_confirm_entry = ctk.CTkEntry(
            self.register_form_frame,
            width=280,
            height=38,
            show="*",
            font=f["body"],
            fg_color=c.get("bg_input", "#0B1120"),
            border_width=1,
            border_color=c["border"],
            text_color=c.get("text_main", "#FFFFFF"),
        )
        self.reg_confirm_entry.pack(pady=(0, 4))

        self.show_password_var = ctk.BooleanVar(value=False)
        self.show_password_checkbox = ctk.CTkCheckBox(
            self.register_form_frame,
            text="Show Passwords",
            variable=self.show_password_var,
            font=f["small"],
            text_color=c["text_muted"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            border_color=c["border"],
            command=self._toggle_password_visibility
        )
        self.show_password_checkbox.pack(anchor="w", pady=(4, 10))

        self.submit_register_btn = ctk.CTkButton(
            self.register_form_frame,
            text="Save Account",
            width=280,
            height=42,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=self.attempt_register
        )
        self.submit_register_btn.pack(pady=(2, 8))

        self.back_to_login_btn = ctk.CTkButton(
            self.register_form_frame,
            text="Back to Login",
            width=280,
            height=38,
            font=f["button"],
            fg_color="transparent",
            hover_color=c["border"],
            border_width=1,
            border_color=c["border"],
            text_color=c["text_main"],
            command=self.show_login_mode
        )
        self.back_to_login_btn.pack(pady=(0, 6))

        # Show default login form
        self.login_form_frame.pack()

        # Key bindings
        self.username_entry.bind("<Return>", lambda _event: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda _event: self.attempt_login())
        self.reg_username_entry.bind("<Return>", lambda _event: self.reg_password_entry.focus_set())
        self.reg_password_entry.bind("<Return>", lambda _event: self.reg_confirm_entry.focus_set())
        self.reg_confirm_entry.bind("<Return>", lambda _event: self.attempt_register())
        self.bind("<Configure>", self._on_resize)

    def _toggle_login_password_visibility(self):
        mask = "" if self.login_show_pw_var.get() else "*"
        self.password_entry.configure(show=mask)

    def _toggle_password_visibility(self):
        mask = "" if self.show_password_var.get() else "*"
        self.reg_password_entry.configure(show=mask)
        self.reg_confirm_entry.configure(show=mask)

    def show_register_mode(self):
        """Switches the card view to user account creation."""
        self._mode = "register"
        self.login_form_frame.pack_forget()
        self.subtitle_label.configure(text="Create New User Account")
        self.role_selector.set("Staff")
        self.reg_username_entry.delete(0, "end")
        self.reg_password_entry.delete(0, "end")
        self.reg_confirm_entry.delete(0, "end")
        self.show_password_var.set(False)
        self._toggle_password_visibility()
        self.register_form_frame.pack()
        self.reg_username_entry.focus_set()

    def show_login_mode(self, prefill_username: str = ""):
        """Switches the card view back to standard login."""
        self._mode = "login"
        self.register_form_frame.pack_forget()
        self.subtitle_label.configure(text="POS & Kitchen Management")
        self.login_show_pw_var.set(False)
        self._toggle_login_password_visibility()
        self.login_form_frame.pack()
        if prefill_username:
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, prefill_username)
            self.password_entry.delete(0, "end")
            self.password_entry.focus_set()
        else:
            self.username_entry.focus_set()

    def _on_resize(self, event):
        """Scales the login logo proportionally to window height while staying within bounds."""
        if event.height > 100:
            max_cap = 110 if self._mode == "register" else 155
            target = max(80, min(max_cap, int(event.height * 0.15)))
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
                    self.logo_label.pack(before=self.title_label, pady=(8, 4))
        except Exception as e:
            print(f"Logo load error (LoginFrame): {e}")

    def attempt_register(self):
        role = self.role_selector.get()
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get()
        confirm_password = self.reg_confirm_entry.get()

        if not username or not password or not confirm_password:
            messagebox.showwarning("Input Error", "Please complete all fields.")
            return

        if password != confirm_password:
            messagebox.showerror("Password Mismatch", "Passwords do not match. Please re-enter.")
            self.reg_password_entry.delete(0, "end")
            self.reg_confirm_entry.delete(0, "end")
            self.reg_password_entry.focus_set()
            return

        success, message = self.controller.db.create_user(username, password, role)
        if success:
            messagebox.showinfo("Account Created", message)
            self.show_login_mode(prefill_username=username)
        else:
            messagebox.showerror("Account Creation Failed", message)

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password.")
            return

        role = self.controller.db.authenticate_user(username, password)

        if role:
            self.controller.current_user_role = role
            self.username_entry.delete(0, "end")
            self.password_entry.delete(0, "end")
            self.login_show_pw_var.set(False)
            self._toggle_login_password_visibility()

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
        gold_text = c.get("accent_gold", c.get("brand_gold", "#FACC15"))

        self.configure(fg_color=c["bg_main"])
        self.login_card.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.title_label.configure(text_color=c["text_main"])
        self.subtitle_label.configure(text_color=gold_text)

        for lbl in (
            self.username_label,
            self.password_label,
            self.role_label,
            self.reg_username_label,
            self.reg_password_label,
            self.reg_confirm_label,
        ):
            lbl.configure(text_color=c["text_muted"])

        for entry in (
            self.username_entry,
            self.password_entry,
            self.reg_username_entry,
            self.reg_password_entry,
            self.reg_confirm_entry,
        ):
            entry.configure(
                fg_color=c["bg_input"],
                border_color=c["border"],
                text_color=c["text_main"],
            )

        self.role_selector.configure(
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color=c["text_main"],
        )

        for chk in (self.login_show_pw_checkbox, self.show_password_checkbox):
            chk.configure(
                text_color=c["text_muted"],
                fg_color=c["primary"],
                hover_color=c["primary_hover"],
                border_color=c["border"],
            )

        self.login_button.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.submit_register_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.create_account_nav_btn.configure(
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_color=gold_text,
            text_color=gold_text,
        )
        self.back_to_login_btn.configure(
            hover_color=c["border"],
            border_color=c["border"],
            text_color=c["text_main"],
        )
        self.exit_button.configure(fg_color=c["accent_red"], hover_color=c["red_hover"])