import customtkinter as ctk
from tkinter import messagebox

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.center_frame = ctk.CTkFrame(self, width=400, height=400)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_label = ctk.CTkLabel(self.center_frame, text="ProjectBB Plus", font=("Arial", 28, "bold"))
        self.title_label.pack(pady=(40, 20))
        
        self.username_entry = ctk.CTkEntry(self.center_frame, width=250, placeholder_text="Username")
        self.username_entry.pack(pady=10)
        
        self.password_entry = ctk.CTkEntry(self.center_frame, width=250, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)
        
        self.login_button = ctk.CTkButton(self.center_frame, text="Login", width=250, command=self.attempt_login)
        self.login_button.pack(pady=(20, 40))
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
            
            self.controller.frames["CashierFrame"].update_admin_features()
            self.controller.show_frame("CashierFrame")
        else:
            messagebox.showerror("Authentication Failed", "Invalid username or password.")