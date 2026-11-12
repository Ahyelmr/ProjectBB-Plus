import customtkinter as ctk
from tkinter import messagebox

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        # Inherit the main background color from the centralized theme
        super().__init__(parent, fg_color=controller.colors["bg_main"])
        self.controller = controller
        
        # Responsive centering: weights push the center cell (row 1, column 1) to the middle
        self.grid_rowconfigure((0, 2), weight=1)
        self.grid_columnconfigure((0, 2), weight=1)
        
        # Replaces center_frame with a styled card container
        self.login_card = ctk.CTkFrame(
            self, 
            fg_color=controller.colors["bg_card"],
            border_width=2,
            border_color=controller.colors["border"],
            corner_radius=15
        )
        self.login_card.grid(row=1, column=1, padx=20, pady=20, ipadx=40, ipady=40)
        
        self.title_label = ctk.CTkLabel(
            self.login_card, 
            text="ProjectBB Plus", 
            font=self.controller.fonts["title"],
            text_color=self.controller.colors["text_main"]
        )
        self.title_label.pack(pady=(20, 20))
        
        self.username_entry = ctk.CTkEntry(
            self.login_card, 
            width=280, 
            height=45, 
            placeholder_text="Username",
            font=self.controller.fonts["body"]
        )
        self.username_entry.pack(pady=10)
        
        self.password_entry = ctk.CTkEntry(
            self.login_card, 
            width=280, 
            height=45, 
            placeholder_text="Password", 
            show="*",
            font=self.controller.fonts["body"]
        )
        self.password_entry.pack(pady=10)
        
        self.login_button = ctk.CTkButton(
            self.login_card, 
            text="Login", 
            width=280, 
            height=45, 
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=self.attempt_login
        )
        self.login_button.pack(pady=(20, 20))
        
        self.password_entry.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password.")
            return
            
        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username = ? AND password_hash = ?", (username, password))
            user = cursor.fetchone()
            
        if user:
            self.controller.current_user_role = user["role"]
            self.username_entry.delete(0, 'end')
            self.password_entry.delete(0, 'end')
            
            # Dynamically adjusts layout based on the active role
            self.controller.frames["CashierFrame"].update_admin_features()
            self.controller.show_frame("CashierFrame")
        else:
            messagebox.showerror("Authentication Failed", "Invalid username or password.")