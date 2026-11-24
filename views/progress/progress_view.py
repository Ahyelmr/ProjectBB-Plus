import csv
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog
from components.page_header import PageHeader
from views.progress.add_item_dialog import AddItemDialog


class ProgressFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller
        self.current_view = "Total Items Ordered Today"
        self.daily_tally = []
        self.orders_sequence_data = []

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Row 0: Header
        self.header = PageHeader(
            self,
            controller=controller,
            title="Daily Progress & Order Logs",
            back_command=self._go_back,
            logo_size=44,
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        self.refresh_btn = ctk.CTkButton(
            self.header.right_slot,
            text="Refresh Data",
            width=135,
            height=36,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=self.load_daily_data,
        )
        self.refresh_btn.pack()

        # Row 1: View Mode Switcher
        switch_bar = ctk.CTkFrame(self, fg_color="transparent")
        switch_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 6))

        self.view_mode_selector = ctk.CTkSegmentedButton(
            switch_bar,
            values=["Total Items Ordered Today", "Orders in Sequence"],
            font=f["button"],
            fg_color=c["bg_card"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_card"],
            unselected_hover_color=c["border"],
            text_color="#FFFFFF",
            height=36,
            command=self.switch_view,
        )
        self.view_mode_selector.set(self.current_view)
        self.view_mode_selector.pack(pady=2)

        # Row 2: Data Display Area
        self.data_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Items Ordered Today (Completed)",
            label_font=f["header"],
            label_fg_color=c["border"],
            label_text_color=c["accent_gold"],
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.data_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=6)
        self.data_frame.grid_columnconfigure(0, weight=1)

        # Row 3: Bottom Bar
        self.bottom_bar = ctk.CTkFrame(
            self, fg_color=c["bg_card"], corner_radius=12, border_width=1, border_color=c["border"]
        )
        self.bottom_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(6, 10))

        self.total_items_label = ctk.CTkLabel(
            self.bottom_bar,
            text="Total Items Sold: 0  |  Total Earned: ₱0.00",
            font=f["header"],
            text_color=c["text_green"],
        )
        self.total_items_label.pack(side="left", padx=16, pady=10)

        self.export_btn = ctk.CTkButton(
            self.bottom_bar,
            text="Export to CSV",
            height=36,
            font=f["button"],
            fg_color=c["accent_green"],
            hover_color=c["green_hover"],
            text_color="#FFFFFF",
            command=self.export_csv,
        )
        self.export_btn.pack(side="right", padx=(6, 12), pady=10)

        self.import_btn = ctk.CTkButton(
            self.bottom_bar,
            text="Import Inventory CSV",
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=self.upload_csv,
        )
        self.import_btn.pack(side="right", padx=6, pady=10)

        self.add_item_btn = ctk.CTkButton(
            self.bottom_bar,
            text="+ Add Menu Item",
            height=36,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=self.open_add_item_dialog,
        )
        self.add_item_btn.pack(side="right", padx=6, pady=10)

        self.bind("<Configure>", lambda e: self.header.scale_logo_for_height(e.height, 38, 54, 0.06))

    def _go_back(self):
        self.controller.frames["CashierFrame"].load_menu()
        self.controller.show_frame("CashierFrame")

    def on_show(self):
        self.load_daily_data()

    def switch_view(self, selected_mode: str):
        self.current_view = selected_mode
        label = (
            "Items Ordered Today (Completed)"
            if selected_mode == "Total Items Ordered Today"
            else "All Orders in Sequence (Today)"
        )
        self.data_frame.configure(label_text=label)
        self.load_daily_data()

    def load_daily_data(self):
        for widget in self.data_frame.winfo_children():
            widget.destroy()

        today = datetime.now().strftime("%Y-%m-%d")
        if self.current_view == "Total Items Ordered Today":
            self._render_item_tally(today)
        else:
            self._render_orders_sequence(today)

    def _render_item_tally(self, today: str):
        c = self.controller.colors
        f = self.controller.fonts
        self.daily_tally = self.controller.db.get_daily_item_tally(today)

        if not self.daily_tally:
            ctk.CTkLabel(
                self.data_frame,
                text="No completed item orders recorded today.",
                font=f["body"],
                text_color=c["text_muted"],
            ).grid(row=0, column=0, pady=24, padx=10)
            self.total_items_label.configure(text="Total Items Sold: 0  |  Total Earned: ₱0.00")
            return

        total_items = 0
        total_earned_all = 0.0

        for idx, (item_name, qty_sold, item_earned) in enumerate(self.daily_tally):
            total_items += qty_sold
            total_earned_all += item_earned

            row_card = ctk.CTkFrame(
                self.data_frame,
                fg_color=c["bg_input"],
                corner_radius=8,
                border_width=1,
                border_color=c["border"],
            )
            row_card.grid(row=idx, column=0, sticky="ew", pady=4, padx=8)
            row_card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row_card, text=item_name, font=f["body"], text_color=c["text_main"]).grid(
                row=0, column=0, sticky="w", padx=14, pady=10
            )

            metrics = ctk.CTkFrame(row_card, fg_color="transparent")
            metrics.grid(row=0, column=1, sticky="e", padx=14, pady=10)

            ctk.CTkLabel(
                metrics, text=f"Quantity Ordered Today: {qty_sold}", font=f["subheader"], text_color=c["text_green"]
            ).pack(side="left", padx=(0, 14))
            ctk.CTkLabel(metrics, text="|", font=f["body"], text_color=c["border"]).pack(side="left", padx=(0, 14))
            ctk.CTkLabel(
                metrics, text=f"Total Earned: ₱{item_earned:,.2f}", font=f["subheader"], text_color=c["accent_gold"]
            ).pack(side="left")

        self.total_items_label.configure(
            text=f"Total Items Sold: {total_items}  |  Total Earned: ₱{total_earned_all:,.2f}"
        )

    def _render_orders_sequence(self, today: str):
        c = self.controller.colors
        f = self.controller.fonts
        self.orders_sequence_data = self.controller.db.get_daily_orders_sequence(today)

        if not self.orders_sequence_data:
            ctk.CTkLabel(
                self.data_frame, text="No orders recorded today.", font=f["body"], text_color=c["text_muted"]
            ).grid(row=0, column=0, pady=24, padx=10)
            self.total_items_label.configure(text="Total Orders Today: 0  |  Sales: ₱0.00")
            return

        total_sales = 0.0
        for idx, order in enumerate(self.orders_sequence_data):
            total_sales += order["total_amount"]
            status = order["status"]
            status_color = (
                c["text_green"] if status == "COMPLETED" else "#60A5FA" if status == "READY" else c["accent_gold"]
            )
            time_str = order["order_date"].split(" ")[-1] if " " in order["order_date"] else order["order_date"]

            card = ctk.CTkFrame(
                self.data_frame,
                fg_color=c["bg_input"],
                corner_radius=10,
                border_width=1,
                border_color=c["border"],
            )
            card.grid(row=idx, column=0, sticky="ew", pady=6, padx=8)
            card.grid_columnconfigure(0, weight=1)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
            hdr.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                hdr,
                text=f"Order #{order['sequence_number']}   •   {time_str}   •   [{status}]",
                font=f["subheader"],
                text_color=status_color,
            ).grid(row=0, column=0, sticky="w")

            discount_note = f"  (Discount: {order['discount_applied']})" if order["discount_applied"] != "None" else ""
            ctk.CTkLabel(
                hdr,
                text=f"Total: ₱{order['total_amount']:.2f}{discount_note}",
                font=f["subheader"],
                text_color=c["accent_gold"] if discount_note else c["text_main"],
            ).grid(row=0, column=1, sticky="e")

            ctk.CTkFrame(card, height=1, fg_color=c["border"]).grid(row=1, column=0, sticky="ew", padx=14, pady=3)

            items_frame = ctk.CTkFrame(card, fg_color="transparent")
            items_frame.grid(row=2, column=0, sticky="ew", padx=18, pady=(4, 10))
            items_frame.grid_columnconfigure(0, weight=1)

            for item_idx, item in enumerate(order["items"]):
                ctk.CTkLabel(
                    items_frame,
                    text=f"•  {item['quantity']}x {item['name']}  ({item['category']})",
                    font=f["body"],
                    text_color=c["text_main"],
                ).grid(row=item_idx, column=0, sticky="w", pady=1)
                ctk.CTkLabel(
                    items_frame,
                    text=f"₱{item['line_total']:.2f}",
                    font=f["body"],
                    text_color=c["text_muted"],
                ).grid(row=item_idx, column=1, sticky="e", pady=1)

        self.total_items_label.configure(
            text=f"Total Orders Today: {len(self.orders_sequence_data)}  |  Total Sales: ₱{total_sales:,.2f}"
        )

    def export_csv(self):
        date_stamp = datetime.now().strftime("%Y%m%d")

        if self.current_view == "Total Items Ordered Today":
            if not self.daily_tally:
                messagebox.showwarning("No Data", "There are no completed item orders to export today.")
                return
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv", initialfile=f"daily_item_tally_{date_stamp}.csv"
            )
            if filepath:
                with open(filepath, mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Item Name", "Quantity Sold Today", "Total Amount Earned"])
                    for item_name, qty_sold, item_earned in self.daily_tally:
                        writer.writerow([item_name, qty_sold, f"{item_earned:.2f}"])
                messagebox.showinfo("Export Successful", f"Daily item tally saved to {filepath}")
        else:
            if not self.orders_sequence_data:
                messagebox.showwarning("No Data", "There are no sequential orders to export today.")
                return
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv", initialfile=f"daily_orders_sequence_{date_stamp}.csv"
            )
            if filepath:
                with open(filepath, mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        "Sequence #", "Order Date/Time", "Status",
                        "Item Name", "Category", "Quantity",
                        "Unit Price", "Line Total", "Discount Applied", "Order Total",
                    ])
                    for order in self.orders_sequence_data:
                        for item in order["items"]:
                            writer.writerow([
                                order["sequence_number"], order["order_date"], order["status"],
                                item["name"], item["category"], item["quantity"],
                                f"{item['unit_price']:.2f}", f"{item['line_total']:.2f}",
                                order["discount_applied"], f"{order['total_amount']:.2f}",
                            ])
                messagebox.showinfo("Export Successful", f"Sequential orders log saved to {filepath}")

    def upload_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            self.controller.db.import_inventory_from_csv(filepath)
            if "CashierFrame" in self.controller.frames:
                self.controller.frames["CashierFrame"].load_menu()
            messagebox.showinfo("Success", "Inventory successfully updated from CSV.")

    def open_add_item_dialog(self):
        def _refresh_cashier():
            if "CashierFrame" in self.controller.frames:
                self.controller.frames["CashierFrame"].load_menu()

        AddItemDialog(self, self.controller, on_saved=_refresh_cashier)

    def apply_theme(self):
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        self.header.apply_theme()
        self.bottom_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.total_items_label.configure(text_color=c["text_green"])
        self.refresh_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.export_btn.configure(fg_color=c["accent_green"], hover_color=c["green_hover"])
        self.import_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.add_item_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.view_mode_selector.configure(
            fg_color=c["bg_card"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_card"],
            unselected_hover_color=c["border"],
        )
        self.data_frame.configure(
            fg_color=c["bg_card"],
            border_color=c["border"],
            label_fg_color=c["border"],
            label_text_color=c["accent_gold"],
        )
        self.load_daily_data()