import customtkinter as ctk
from tkinter import messagebox, filedialog
import csv
from datetime import datetime

class ProgressFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.top_bar = ctk.CTkFrame(self)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkButton(self.top_bar, text="Back to Cashier", width=120, command=lambda: controller.show_frame("CashierFrame")).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(self.top_bar, text="Daily Progress & Transaction Log", font=("Arial", 20, "bold")).pack(side="left", expand=True)
        ctk.CTkButton(self.top_bar, text="Refresh Data", width=120, command=self.load_daily_data).pack(side="right", padx=10, pady=10)
        
        self.data_frame = ctk.CTkScrollableFrame(self, label_text="Completed Transactions Today")
        self.data_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.bottom_bar = ctk.CTkFrame(self)
        self.bottom_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self.total_revenue_label = ctk.CTkLabel(self.bottom_bar, text="Total Daily Revenue: ₱0.00", font=("Arial", 18, "bold"))
        self.total_revenue_label.pack(side="left", padx=20, pady=10)
        ctk.CTkButton(self.bottom_bar, text="Export to CSV", fg_color="green", hover_color="darkgreen", command=self.export_csv).pack(side="right", padx=20, pady=10)
        
        self.daily_orders = []

    def load_daily_data(self):
        for widget in self.data_frame.winfo_children():
            widget.destroy()
            
        today = datetime.now().strftime("%Y-%m-%d")
        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT order_id, sequence_number, order_date, total_amount FROM orders WHERE status = 'COMPLETED' AND order_date LIKE ?", (today + '%',))
            self.daily_orders = cursor.fetchall()
            
        total_revenue = 0
        for idx, order in enumerate(self.daily_orders):
            total_revenue += order["total_amount"]
            row_text = f"Seq #{order['sequence_number']} | Time: {order['order_date']} | Total: ₱{order['total_amount']:.2f}"
            ctk.CTkLabel(self.data_frame, text=row_text, font=("Arial", 14)).grid(row=idx, column=0, sticky="w", pady=2, padx=10)
            
        self.total_revenue_label.configure(text=f"Total Daily Revenue: ₱{total_revenue:.2f}")

    def export_csv(self):
        if not self.daily_orders:
            messagebox.showwarning("No Data", "There are no completed transactions to export today.")
            return
            
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"daily_sales_{datetime.now().strftime('%Y%m%d')}.csv")
        if filepath:
            with open(filepath, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Order ID", "Sequence Number", "Date/Time", "Amount"])
                for order in self.daily_orders:
                    writer.writerow([order["order_id"], order["sequence_number"], order["order_date"], order["total_amount"]])
            messagebox.showinfo("Export Successful", f"Transaction log saved to {filepath}")