import sys
import customtkinter as ctk
from tkinter import messagebox
from components.logo_widget import LogoLabel


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller
        self._mode = "login"
        self._muted_labels = []
        self._entries = []

        self.grid_rowconfigure((0, 2), weight=1)
        self.grid_columnconfigure((0, 2), weight=1)

        self.login_card = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            border_width=2,
            border_color=c["border"],
            corner_radius=15,
        )
        self.login_card.grid(row=1, column=1, padx=20, pady=20, ipadx=40, ipady=25)

        self.logo = LogoLabel(self.login_card, initial_size=(115, 115))
        if self.logo.has_logo:
            self.logo.pack(pady=(8, 4))

        self.title_label = ctk.CTkLabel(
            self.login_card, text="ProjectBB Plus", font=f["title"], text_color=c["text_main"]
        )
        self.title_label.pack(pady=(5, 2))

        self.subtitle_label = ctk.CTkLabel(
            self.login_card,
            text="POS & Kitchen Management",
            font=f["small"],
            text_color=c["accent_gold"],
        )
        self.subtitle_label.pack(pady=(0, 12))

        self._build_login_form()
        self._build_register_form()
        self.login_form_frame.pack()

        self.bind("<Configure>", self._on_resize)

    def _add_field(self, parent, label_text: str, height: int = 40, show: str = "", pady_bottom: int = 8):
        c = self.controller.colors
        f = self.controller.fonts

        lbl = ctk.CTkLabel(parent, text=label_text, font=f["small"], text_color=c["text_muted"])
        lbl.pack(anchor="w", pady=(2, 2))
        self._muted_labels.append(lbl)

        entry = ctk.CTkEntry(
            parent,
            width=280,
            height=height,
            show=show,
            font=f["body"],
            fg_color=c["bg_input"],
            border_width=1,
            border_color=c["border"],
            text_color=c["text_main"],
        )
        entry.pack(pady=(0, pady_bottom))
        self._entries.append(entry)
        return entry

    def _build_login_form(self):
        c = self.controller.colors
        f = self.controller.fonts
        self.login_form_frame = ctk.CTkFrame(self.login_card, fg_color="transparent")

        self.username_entry = self._add_field(self.login_form_frame, "Username", height=42)
        self.password_entry = self._add_field(
            self.login_form_frame, "Password", height=42, show="*", pady_bottom=4
        )

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
            command=self._toggle_login_password,
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
            command=self.attempt_login,
        )
        self.login_button.pack(pady=(4, 10))

        self.create_account_nav_btn = ctk.CTkButton(
            self.login_form_frame,
            text="Create Account",
            width=280,
            height=42,
            font=f["button"],
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_width=1,
            border_color=c["accent_gold"],
            text_color=c["accent_gold"],
            command=self.show_register_mode,
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
            command=self.exit_app,
        )
        self.exit_button.pack(pady=(0, 8))

        self.username_entry.bind("<Return>", lambda _e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda _e: self.attempt_login())

    def _build_register_form(self):
        c = self.controller.colors
        f = self.controller.fonts
        self.register_form_frame = ctk.CTkFrame(self.login_card, fg_color="transparent")

        role_lbl = ctk.CTkLabel(
            self.register_form_frame, text="Account Type", font=f["small"], text_color=c["text_muted"]
        )
        role_lbl.pack(anchor="w", pady=(2, 3))
        self._muted_labels.append(role_lbl)

        self.role_selector = ctk.CTkSegmentedButton(
            self.register_form_frame,
            values=["Staff", "Admin"],
            width=280,
            height=36,
            font=f["button"],
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color=c["text_main"],
        )
        self.role_selector.set("Staff")
        self.role_selector.pack(pady=(0, 8))

        self.reg_username_entry = self._add_field(
            self.register_form_frame, "Username (min. 3 characters)", height=38, pady_bottom=6
        )
        self.reg_password_entry = self._add_field(
            self.register_form_frame, "Password (min. 6 characters)", height=38, show="*", pady_bottom=6
        )
        self.reg_confirm_entry = self._add_field(
            self.register_form_frame, "Confirm Password", height=38, show="*", pady_bottom=4
        )

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
            command=self._toggle_register_passwords,
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
            command=self.attempt_register,
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
            command=self.show_login_mode,
        )
        self.back_to_login_btn.pack(pady=(0, 6))

        self.reg_username_entry.bind("<Return>", lambda _e: self.reg_password_entry.focus_set())
        self.reg_password_entry.bind("<Return>", lambda _e: self.reg_confirm_entry.focus_set())
        self.reg_confirm_entry.bind("<Return>", lambda _e: self.attempt_register())

    def _toggle_login_password(self):
        self.password_entry.configure(show="" if self.login_show_pw_var.get() else "*")

    def _toggle_register_passwords(self):
        mask = "" if self.show_password_var.get() else "*"
        self.reg_password_entry.configure(show=mask)
        self.reg_confirm_entry.configure(show=mask)

    def show_register_mode(self):
        self._mode = "register"
        self.login_form_frame.pack_forget()
        self.subtitle_label.configure(text="Create New User Account")
        self.role_selector.set("Staff")
        for entry in (self.reg_username_entry, self.reg_password_entry, self.reg_confirm_entry):
            entry.delete(0, "end")
        self.show_password_var.set(False)
        self._toggle_register_passwords()
        self.register_form_frame.pack()
        self.reg_username_entry.focus_set()

    def show_login_mode(self, prefill_username: str = ""):
        self._mode = "login"
        self.register_form_frame.pack_forget()
        self.subtitle_label.configure(text="POS & Kitchen Management")
        self.login_show_pw_var.set(False)
        self._toggle_login_password()
        self.login_form_frame.pack()
        if prefill_username:
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, prefill_username)
            self.password_entry.delete(0, "end")
            self.password_entry.focus_set()
        else:
            self.username_entry.focus_set()

    def _on_resize(self, event):
        if event.height > 100 and self.logo.has_logo:
            max_cap = 110 if self._mode == "register" else 155
            target = max(80, min(max_cap, int(event.height * 0.15)))
            self.logo.set_max_size(target, target)

    def attempt_register(self):
        role = self.role_selector.get()
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()

        if not username or not password or not confirm:
            messagebox.showwarning("Input Error", "Please complete all fields.")
            return
        if password != confirm:
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
            self._toggle_login_password()

            cashier = self.controller.frames["CashierFrame"]
            cashier.update_admin_features()
            cashier.load_menu()
            self.controller.show_frame("CashierFrame")
        else:
            messagebox.showerror("Authentication Failed", "Invalid username or password.")

    def exit_app(self):
        self.controller.quit()
        self.controller.destroy()
        sys.exit(0)

    def apply_theme(self):
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        self.login_card.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.title_label.configure(text_color=c["text_main"])
        self.subtitle_label.configure(text_color=c["accent_gold"])

        for lbl in self._muted_labels:
            lbl.configure(text_color=c["text_muted"])
        for entry in self._entries:
            entry.configure(fg_color=c["bg_input"], border_color=c["border"], text_color=c["text_main"])
        for chk in (self.login_show_pw_checkbox, self.show_password_checkbox):
            chk.configure(
                text_color=c["text_muted"],
                fg_color=c["primary"],
                hover_color=c["primary_hover"],
                border_color=c["border"],
            )

        self.role_selector.configure(
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color=c["text_main"],
        )
        self.login_button.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.submit_register_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.create_account_nav_btn.configure(
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_color=c["accent_gold"],
            text_color=c["accent_gold"],
        )
        self.back_to_login_btn.configure(
            hover_color=c["border"], border_color=c["border"], text_color=c["text_main"]
        )
        self.exit_button.configure(fg_color=c["accent_red"], hover_color=c["red_hover"])