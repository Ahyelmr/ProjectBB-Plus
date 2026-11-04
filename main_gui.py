import customtkinter as ctk
from database.db_manager import DatabaseManager
from queue_manager import QueueManager

from views.login_view import LoginFrame
from views.cashier_view import CashierFrame
from views.kitchen_view import KitchenFrame
from views.progress_view import ProgressFrame

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ProjectBBApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ProjectBB Plus - POS System")
        self.geometry("1280x720")
        
        self.db = DatabaseManager()
        self.queue = QueueManager(self.db, printer_name="POS-58")
        self.current_user_role = None
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        for F in (LoginFrame, CashierFrame, KitchenFrame, ProgressFrame):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("LoginFrame")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

if __name__ == "__main__":
    app = ProjectBBApp()
    app.mainloop()