import os
import sys
import csv
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog
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


class ProgressFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=controller.colors["bg_main"])
        self.controller = controller
        self._last_logo_size = None
        self.current_view = "Total Items Ordered Today"

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # --- Row 0: Top Navigation Bar ---
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkButton(
            self.top_bar,
            text="Back to Cashier",
            width=130,
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=lambda: [
                self.controller.frames["CashierFrame"].load_menu(),
                controller.show_frame("CashierFrame")
            ]
        ).pack(side="left", padx=10, pady=8)

        # Centered Header Container (Logo + Title)
        self.header_center = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.header_center.pack(side="left", expand=True)

        self.logo_label = ctk.CTkLabel(self.header_center, text="")
        self._update_logo(44, 44)

        self.title_label = ctk.CTkLabel(
            self.header_center,
            text="Daily Progress & Order Logs",
            font=self.controller.fonts["title"],
            text_color=self.controller.colors["text_main"]
        )
        self.title_label.pack(side="left", padx=6)

        ctk.CTkButton(
            self.top_bar,
            text="Refresh Data",
            width=130,
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=self.load_daily_data
        ).pack(side="right", padx=10, pady=8)

        # --- Row 1: View Mode Switcher ---
        self.switch_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.switch_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))

        self.view_mode_selector = ctk.CTkSegmentedButton(
            self.switch_bar,
            values=["Total Items Ordered Today", "Orders in Sequence"],
            font=self.controller.fonts["button"],
            selected_color=self.controller.colors["primary"],
            selected_hover_color=self.controller.colors["primary_hover"],
            command=self.switch_view
        )
        self.view_mode_selector.set(self.current_view)
        self.view_mode_selector.pack(pady=2)

        # --- Row 2: Data Display Area ---
        self.data_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Items Ordered Today",
            label_font=self.controller.fonts["header"],
            label_text_color=self.controller.colors["text_main"],
            fg_color=self.controller.colors["bg_card"]
        )
        self.data_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=6)
        self.data_frame.grid_columnconfigure(0, weight=1)

        # --- Row 3: Bottom Export & Import Bar ---
        self.bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(6, 10))

        self.total_items_label = ctk.CTkLabel(
            self.bottom_bar,
            text="Total Items Sold: 0",
            font=self.controller.fonts["header"],
            text_color=self.controller.colors["text_main"]
        )
        self.total_items_label.pack(side="left", padx=20, pady=8)

        ctk.CTkButton(
            self.bottom_bar,
            text="Export to CSV",
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["accent_green"],
            hover_color=self.controller.colors["green_hover"],
            command=self.export_csv
        ).pack(side="right", padx=10, pady=8)

        ctk.CTkButton(
            self.bottom_bar,
            text="Import Inventory CSV",
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=self.upload_csv
        ).pack(side="right", padx=10, pady=8)

        self.daily_tally = []
        self.orders_sequence_data = []
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """Scales the Progress header logo proportionally to window height."""
        if event.height > 100:
            target = max(38, min(54, int(event.height * 0.06)))
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
                    self.logo_label.pack(side="left", before=self.title_label, padx=(0, 8))
        except Exception as e:
            print(f"Logo load error (ProgressFrame): {e}")

    def switch_view(self, selected_mode):
        """Switches between aggregated daily item tally and sequential order breakdown."""
        self.current_view = selected_mode
        if selected_mode == "Total Items Ordered Today":
            self.data_frame.configure(label_text="Items Ordered Today (Completed)")
        else:
            self.data_frame.configure(label_text="All Orders in Sequence (Today)")
        self.load_daily_data()

    def load_daily_data(self):
        """Loads either the daily item tally or the sequential order breakdown based on active mode."""
        for widget in self.data_frame.winfo_children():
            widget.destroy()

        today = datetime.now().strftime("%Y-%m-%d")

        if self.current_view == "Total Items Ordered Today":
            self._load_item_tally(today)
        else:
            self._load_orders_in_sequence(today)

    def _load_item_tally(self, today):
        """Fetches and displays aggregated quantities of completed items ordered today."""
        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT inventory.name AS item_name, SUM(order_items.quantity) AS total_qty
                FROM order_items
                JOIN orders ON order_items.order_id = orders.order_id
                JOIN inventory ON order_items.sku = inventory.sku
                WHERE orders.status = 'COMPLETED' AND orders.order_date LIKE ?
                GROUP BY inventory.name
                ORDER BY total_qty DESC, inventory.name ASC
            """, (today + "%",))
            rows = cursor.fetchall()
            self.daily_tally = [(row["item_name"], row["total_qty"]) for row in rows]

        if not self.daily_tally:
            ctk.CTkLabel(
                self.data_frame,
                text="No completed item orders recorded today.",
                font=self.controller.fonts["body"],
                text_color=self.controller.colors["text_muted"]
            ).grid(row=0, column=0, pady=20, padx=10)
            self.total_items_label.configure(text="Total Items Sold: 0")
            return

        total_items = 0
        for idx, (item_name, qty_sold) in enumerate(self.daily_tally):
            total_items += qty_sold

            row_card = ctk.CTkFrame(
                self.data_frame,
                fg_color=self.controller.colors["bg_main"],
                corner_radius=8,
                border_width=1,
                border_color=self.controller.colors["border"]
            )
            row_card.grid(row=idx, column=0, sticky="ew", pady=4, padx=8)
            row_card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row_card,
                text=item_name,
                font=self.controller.fonts["body"],
                text_color=self.controller.colors["text_main"]
            ).grid(row=0, column=0, sticky="w", padx=14, pady=8)

            ctk.CTkLabel(
                row_card,
                text=f"Quantity Ordered Today: {qty_sold}",
                font=self.controller.fonts["subheader"],
                text_color=self.controller.colors["accent_green"]
            ).grid(row=0, column=1, sticky="e", padx=14, pady=8)

        self.total_items_label.configure(text=f"Total Items Sold: {total_items}")

    def _load_orders_in_sequence(self, today):
        """Fetches and displays all orders for today in sequence with their menu item breakdowns."""
        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    orders.order_id,
                    orders.sequence_number,
                    orders.order_date,
                    orders.total_amount,
                    COALESCE(orders.discount_applied, 'None') AS discount_applied,
                    orders.status,
                    inventory.name AS item_name,
                    inventory.category AS category,
                    order_items.quantity,
                    COALESCE(order_items.price_per_unit, inventory.price) AS unit_price
                FROM orders
                JOIN order_items ON orders.order_id = order_items.order_id
                JOIN inventory ON order_items.sku = inventory.sku
                WHERE orders.order_date LIKE ?
                ORDER BY orders.sequence_number ASC, orders.order_id ASC, order_items.item_id ASC
            """, (today + "%",))
            rows = cursor.fetchall()

        orders_map = {}
        self.orders_sequence_data = []

        for row in rows:
            oid = row["order_id"]
            if oid not in orders_map:
                orders_map[oid] = {
                    "order_id": oid,
                    "sequence_number": row["sequence_number"],
                    "order_date": row["order_date"],
                    "total_amount": row["total_amount"],
                    "discount_applied": row["discount_applied"],
                    "status": row["status"],
                    "items": []
                }
            orders_map[oid]["items"].append({
                "name": row["item_name"],
                "category": row["category"],
                "quantity": row["quantity"],
                "unit_price": row["unit_price"],
                "line_total": row["quantity"] * row["unit_price"]
            })

        self.orders_sequence_data = list(orders_map.values())

        if not self.orders_sequence_data:
            ctk.CTkLabel(
                self.data_frame,
                text="No orders recorded today.",
                font=self.controller.fonts["body"],
                text_color=self.controller.colors["text_muted"]
            ).grid(row=0, column=0, pady=20, padx=10)
            self.total_items_label.configure(text="Total Orders Today: 0 | Sales: ₱0.00")
            return

        total_sales = 0.0
        for idx, order in enumerate(self.orders_sequence_data):
            total_sales += order["total_amount"]
            status = order["status"]

            if status == "COMPLETED":
                status_color = self.controller.colors["accent_green"]
            elif status == "READY":
                status_color = self.controller.colors["primary_hover"]
            else:
                status_color = self.controller.colors["accent_gold"]

            # Extract time portion (HH:MM:SS) if full timestamp is stored
            time_str = order["order_date"].split(" ")[-1] if " " in order["order_date"] else order["order_date"]

            card = ctk.CTkFrame(
                self.data_frame,
                fg_color=self.controller.colors["bg_main"],
                corner_radius=10,
                border_width=1,
                border_color=self.controller.colors["border"]
            )
            card.grid(row=idx, column=0, sticky="ew", pady=6, padx=8)
            card.grid_columnconfigure(0, weight=1)

            # Card Header: Sequence #, Time, Status, and Order Total
            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))
            header_frame.grid_columnconfigure(0, weight=1)

            left_header = f"Order #{order['sequence_number']}   •   {time_str}   •   [{status}]"
            ctk.CTkLabel(
                header_frame,
                text=left_header,
                font=self.controller.fonts["subheader"],
                text_color=status_color
            ).grid(row=0, column=0, sticky="w")

            discount_note = f"  (Discount: {order['discount_applied']})" if order["discount_applied"] != "None" else ""
            ctk.CTkLabel(
                header_frame,
                text=f"Total: ₱{order['total_amount']:.2f}{discount_note}",
                font=self.controller.fonts["subheader"],
                text_color=self.controller.colors["text_main"]
            ).grid(row=0, column=1, sticky="e")

            # Subtle divider between header and item breakdown
            divider = ctk.CTkFrame(card, height=1, fg_color=self.controller.colors["border"])
            divider.grid(row=1, column=0, sticky="ew", padx=12, pady=2)

            # Item Breakdown List
            items_frame = ctk.CTkFrame(card, fg_color="transparent")
            items_frame.grid(row=2, column=0, sticky="ew", padx=18, pady=(4, 8))
            items_frame.grid_columnconfigure(0, weight=1)

            for item_idx, item in enumerate(order["items"]):
                ctk.CTkLabel(
                    items_frame,
                    text=f"•  {item['quantity']}x {item['name']}  ({item['category']})",
                    font=self.controller.fonts["body"],
                    text_color=self.controller.colors["text_main"]
                ).grid(row=item_idx, column=0, sticky="w", pady=1)

                ctk.CTkLabel(
                    items_frame,
                    text=f"₱{item['line_total']:.2f}",
                    font=self.controller.fonts["body"],
                    text_color=self.controller.colors["text_muted"]
                ).grid(row=item_idx, column=1, sticky="e", pady=1)

        self.total_items_label.configure(
            text=f"Total Orders Today: {len(self.orders_sequence_data)}  |  Total Sales: ₱{total_sales:.2f}"
        )

    def export_csv(self):
        """Exports the active view (either daily item tally or sequential order breakdown) to CSV."""
        date_stamp = datetime.now().strftime("%Y%m%d")

        if self.current_view == "Total Items Ordered Today":
            if not self.daily_tally:
                messagebox.showwarning("No Data", "There are no completed item orders to export today.")
                return

            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                initialfile=f"daily_item_tally_{date_stamp}.csv"
            )
            if filepath:
                with open(filepath, mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Item Name", "Quantity Sold Today"])
                    for item_name, qty_sold in self.daily_tally:
                        writer.writerow([item_name, qty_sold])
                messagebox.showinfo("Export Successful", f"Daily item tally saved to {filepath}")
        else:
            if not self.orders_sequence_data:
                messagebox.showwarning("No Data", "There are no sequential orders to export today.")
                return

            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                initialfile=f"daily_orders_sequence_{date_stamp}.csv"
            )
            if filepath:
                with open(filepath, mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        "Sequence #", "Order Date/Time", "Status",
                        "Item Name", "Category", "Quantity",
                        "Unit Price", "Line Total", "Discount Applied", "Order Total"
                    ])
                    for order in self.orders_sequence_data:
                        for item in order["items"]:
                            writer.writerow([
                                order["sequence_number"],
                                order["order_date"],
                                order["status"],
                                item["name"],
                                item["category"],
                                item["quantity"],
                                f"{item['unit_price']:.2f}",
                                f"{item['line_total']:.2f}",
                                order["discount_applied"],
                                f"{order['total_amount']:.2f}"
                            ])
                messagebox.showinfo("Export Successful", f"Sequential orders log saved to {filepath}")

    def upload_csv(self):
        """Opens a file dialog, imports the inventory CSV, and refreshes the Cashier menu."""
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            self.controller.db.import_inventory_from_csv(filepath)
            self.controller.frames["CashierFrame"].load_menu()
            messagebox.showinfo("Success", "Inventory successfully updated from CSV.")