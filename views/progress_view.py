import os
import sys
import csv
import shutil
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image


def get_project_root():
    """Returns the writable project/application root directory."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def get_resource_path(relative_path):
    """Resolves asset paths for both standard execution and PyInstaller bundles."""
    if not relative_path:
        return ""
    local_path = os.path.join(get_project_root(), relative_path)
    if os.path.exists(local_path):
        return local_path
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = get_project_root()
    return os.path.join(base_path, relative_path)


class ProgressFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        gold_bg = c.get("accent_gold", c.get("brand_gold", "#FACC15"))
        gold_hv = c.get("gold_hover", c.get("brand_gold_hover", "#EAB308"))

        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller
        self._last_logo_size = None
        self.current_view = "Total Items Ordered Today"

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # --- Row 0: Top Navigation Bar ---
        self.top_bar = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"]
        )
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        ctk.CTkButton(
            self.top_bar,
            text="Back to Cashier",
            width=145,
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda: [
                self.controller.frames["CashierFrame"].load_menu(),
                controller.show_frame("CashierFrame")
            ]
        ).pack(side="left", padx=12, pady=10)

        # Centered Header Container (Logo + Title)
        self.header_center = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.header_center.pack(side="left", expand=True)

        self.logo_label = ctk.CTkLabel(self.header_center, text="")

        self.title_label = ctk.CTkLabel(
            self.header_center,
            text="Daily Progress & Order Logs",
            font=f["header"],
            text_color=c["text_main"]
        )
        self.title_label.pack(side="left", padx=6)

        self._update_logo(44, 44)

        ctk.CTkButton(
            self.top_bar,
            text="Refresh Data",
            width=135,
            height=36,
            font=f["button"],
            fg_color=gold_bg,
            hover_color=gold_hv,
            text_color=c.get("text_on_gold", "#0F172A"),
            command=self.load_daily_data
        ).pack(side="right", padx=12, pady=10)

        # --- Row 1: View Mode Switcher ---
        self.switch_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.switch_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 6))

        self.view_mode_selector = ctk.CTkSegmentedButton(
            self.switch_bar,
            values=["Total Items Ordered Today", "Orders in Sequence"],
            font=f["button"],
            fg_color=c["bg_card"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_card"],
            unselected_hover_color=c["border"],
            text_color="#FFFFFF",
            height=36,
            command=self.switch_view
        )
        self.view_mode_selector.set(self.current_view)
        self.view_mode_selector.pack(pady=2)

        # --- Row 2: Data Display Area ---
        self.data_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Items Ordered Today (Completed)",
            label_font=f["header"],
            label_fg_color=c["border"],
            label_text_color=gold_bg,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"]
        )
        self.data_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=6)
        self.data_frame.grid_columnconfigure(0, weight=1)

        # --- Row 3: Bottom Export, Import & Add Item Bar ---
        self.bottom_bar = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"]
        )
        self.bottom_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(6, 10))

        self.total_items_label = ctk.CTkLabel(
            self.bottom_bar,
            text="Total Items Sold: 0  |  Total Earned: ₱0.00",
            font=f["header"],
            text_color=c.get("text_green", "#4ADE80")
        )
        self.total_items_label.pack(side="left", padx=16, pady=10)

        ctk.CTkButton(
            self.bottom_bar,
            text="Export to CSV",
            height=36,
            font=f["button"],
            fg_color=c["accent_green"],
            hover_color=c["green_hover"],
            text_color="#FFFFFF",
            command=self.export_csv
        ).pack(side="right", padx=(6, 12), pady=10)

        ctk.CTkButton(
            self.bottom_bar,
            text="Import Inventory CSV",
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=self.upload_csv
        ).pack(side="right", padx=6, pady=10)

        self.add_item_btn = ctk.CTkButton(
            self.bottom_bar,
            text="+ Add Menu Item",
            height=36,
            font=f["button"],
            fg_color=gold_bg,
            hover_color=gold_hv,
            text_color=c.get("text_on_gold", "#0F172A"),
            command=self.open_add_item_dialog
        )
        self.add_item_btn.pack(side="right", padx=6, pady=10)

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
        """Fetches and displays aggregated quantities and total earnings of completed items ordered today."""
        c = self.controller.colors
        f = self.controller.fonts
        green_text = c.get("text_green", "#4ADE80")
        gold_text = c.get("accent_gold", c.get("brand_gold", "#FACC15"))

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    inventory.name AS item_name,
                    SUM(order_items.quantity) AS total_qty,
                    SUM(order_items.quantity * COALESCE(order_items.price_per_unit, inventory.price)) AS total_earned
                FROM order_items
                JOIN orders ON order_items.order_id = orders.order_id
                JOIN inventory ON order_items.sku = inventory.sku
                WHERE orders.status = 'COMPLETED' AND orders.order_date LIKE ?
                GROUP BY inventory.name
                ORDER BY total_qty DESC, inventory.name ASC
            """, (today + "%",))
            rows = cursor.fetchall()
            self.daily_tally = [
                (row["item_name"], row["total_qty"], float(row["total_earned"] or 0.0))
                for row in rows
            ]

        if not self.daily_tally:
            ctk.CTkLabel(
                self.data_frame,
                text="No completed item orders recorded today.",
                font=f["body"],
                text_color=c["text_muted"]
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
                fg_color=c.get("bg_input", "#0B1120"),
                corner_radius=8,
                border_width=1,
                border_color=c["border"]
            )
            row_card.grid(row=idx, column=0, sticky="ew", pady=4, padx=8)
            row_card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row_card,
                text=item_name,
                font=f["body"],
                text_color=c["text_main"]
            ).grid(row=0, column=0, sticky="w", padx=14, pady=10)

            metrics_frame = ctk.CTkFrame(row_card, fg_color="transparent")
            metrics_frame.grid(row=0, column=1, sticky="e", padx=14, pady=10)

            ctk.CTkLabel(
                metrics_frame,
                text=f"Quantity Ordered Today: {qty_sold}",
                font=f.get("subheader", f["body"]),
                text_color=green_text
            ).pack(side="left", padx=(0, 14))

            ctk.CTkLabel(
                metrics_frame,
                text="|",
                font=f["body"],
                text_color=c["border"]
            ).pack(side="left", padx=(0, 14))

            ctk.CTkLabel(
                metrics_frame,
                text=f"Total Earned: ₱{item_earned:,.2f}",
                font=f.get("subheader", f["body"]),
                text_color=gold_text
            ).pack(side="left")

        self.total_items_label.configure(
            text=f"Total Items Sold: {total_items}  |  Total Earned: ₱{total_earned_all:,.2f}"
        )

    def _load_orders_in_sequence(self, today):
        """Fetches and displays all orders for today in sequence with their menu item breakdowns."""
        c = self.controller.colors
        f = self.controller.fonts
        green_text = c.get("text_green", "#4ADE80")
        gold_text = c.get("accent_gold", c.get("brand_gold", "#FACC15"))

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
                font=f["body"],
                text_color=c["text_muted"]
            ).grid(row=0, column=0, pady=24, padx=10)
            self.total_items_label.configure(text="Total Orders Today: 0  |  Sales: ₱0.00")
            return

        total_sales = 0.0
        for idx, order in enumerate(self.orders_sequence_data):
            total_sales += order["total_amount"]
            status = order["status"]

            if status == "COMPLETED":
                status_color = green_text
            elif status == "READY":
                status_color = "#60A5FA"
            else:
                status_color = gold_text

            time_str = order["order_date"].split(" ")[-1] if " " in order["order_date"] else order["order_date"]

            card = ctk.CTkFrame(
                self.data_frame,
                fg_color=c.get("bg_input", "#0B1120"),
                corner_radius=10,
                border_width=1,
                border_color=c["border"]
            )
            card.grid(row=idx, column=0, sticky="ew", pady=6, padx=8)
            card.grid_columnconfigure(0, weight=1)

            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
            header_frame.grid_columnconfigure(0, weight=1)

            left_header = f"Order #{order['sequence_number']}   •   {time_str}   •   [{status}]"
            ctk.CTkLabel(
                header_frame,
                text=left_header,
                font=f.get("subheader", f["body"]),
                text_color=status_color
            ).grid(row=0, column=0, sticky="w")

            discount_note = f"  (Discount: {order['discount_applied']})" if order["discount_applied"] != "None" else ""
            ctk.CTkLabel(
                header_frame,
                text=f"Total: ₱{order['total_amount']:.2f}{discount_note}",
                font=f.get("subheader", f["body"]),
                text_color=gold_text if discount_note else c["text_main"]
            ).grid(row=0, column=1, sticky="e")

            divider = ctk.CTkFrame(card, height=1, fg_color=c["border"])
            divider.grid(row=1, column=0, sticky="ew", padx=14, pady=3)

            items_frame = ctk.CTkFrame(card, fg_color="transparent")
            items_frame.grid(row=2, column=0, sticky="ew", padx=18, pady=(4, 10))
            items_frame.grid_columnconfigure(0, weight=1)

            for item_idx, item in enumerate(order["items"]):
                ctk.CTkLabel(
                    items_frame,
                    text=f"•  {item['quantity']}x {item['name']}  ({item['category']})",
                    font=f["body"],
                    text_color=c["text_main"]
                ).grid(row=item_idx, column=0, sticky="w", pady=1)

                ctk.CTkLabel(
                    items_frame,
                    text=f"₱{item['line_total']:.2f}",
                    font=f["body"],
                    text_color=c["text_muted"]
                ).grid(row=item_idx, column=1, sticky="e", pady=1)

        self.total_items_label.configure(
            text=f"Total Orders Today: {len(self.orders_sequence_data)}  |  Total Sales: ₱{total_sales:,.2f}"
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
                    writer.writerow(["Item Name", "Quantity Sold Today", "Total Amount Earned"])
                    for item_name, qty_sold, item_earned in self.daily_tally:
                        writer.writerow([item_name, qty_sold, f"{item_earned:.2f}"])
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
            if "CashierFrame" in self.controller.frames:
                self.controller.frames["CashierFrame"].load_menu()
            messagebox.showinfo("Success", "Inventory successfully updated from CSV.")

    def open_add_item_dialog(self):
        """Opens a scrollable modal dialog to add or update a single menu/inventory item."""
        c = self.controller.colors
        f = self.controller.fonts
        gold_bg = c.get("accent_gold", c.get("brand_gold", "#FACC15"))
        gold_hv = c.get("gold_hover", c.get("brand_gold_hover", "#EAB308"))
        input_bg = c.get("bg_input", "#0B1120")

        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Menu / Inventory Item")
        dialog.configure(fg_color=c["bg_main"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        root = self.winfo_toplevel()
        root.update_idletasks()
        win_w = 500
        win_h = min(560, max(420, root.winfo_height() - 60))
        x = root.winfo_x() + (root.winfo_width() - win_w) // 2
        y = root.winfo_y() + (root.winfo_height() - win_h) // 2
        dialog.geometry(f"{win_w}x{win_h}+{max(0, x)}+{max(0, y)}")
        dialog.minsize(440, 380)
        dialog.resizable(True, True)

        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=0)
        dialog.grid_columnconfigure(0, weight=1)

        # --- Scrollable Form Area ---
        form_scroll = ctk.CTkScrollableFrame(
            dialog,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"]
        )
        form_scroll.grid(row=0, column=0, sticky="nsew", padx=14, pady=(14, 8))
        form_scroll.grid_columnconfigure(0, weight=1)

        def _on_mousewheel(event):
            if form_scroll.winfo_exists():
                form_scroll._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        dialog.bind("<MouseWheel>", _on_mousewheel)

        ctk.CTkLabel(
            form_scroll,
            text="Add New Menu Item",
            font=f["header"],
            text_color=gold_bg
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            form_scroll,
            text="Fill in the product details below. Existing SKUs can be updated.",
            font=f["body"],
            text_color=c["text_muted"],
            wraplength=410,
            justify="left"
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))

        # 1. SKU
        ctk.CTkLabel(
            form_scroll, text="SKU Code *", font=f["body"], text_color=c["text_main"]
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(4, 2))

        sku_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="e.g., SKU01 or DRK-01",
            height=36,
            font=f["body"],
            fg_color=input_bg,
            border_color=c["border"],
            text_color=c["text_main"]
        )
        sku_entry.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))

        # 2. Item Name
        ctk.CTkLabel(
            form_scroll, text="Item Name *", font=f["body"], text_color=c["text_main"]
        ).grid(row=4, column=0, sticky="w", padx=14, pady=(4, 2))

        name_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="e.g., Classic Cheeseburger",
            height=36,
            font=f["body"],
            fg_color=input_bg,
            border_color=c["border"],
            text_color=c["text_main"]
        )
        name_entry.grid(row=5, column=0, sticky="ew", padx=14, pady=(0, 10))

        # 3. Price
        ctk.CTkLabel(
            form_scroll, text="Price (₱) *", font=f["body"], text_color=c["text_main"]
        ).grid(row=6, column=0, sticky="w", padx=14, pady=(4, 2))

        price_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="e.g., 85.00",
            height=36,
            font=f["body"],
            fg_color=input_bg,
            border_color=c["border"],
            text_color=c["text_main"]
        )
        price_entry.grid(row=7, column=0, sticky="ew", padx=14, pady=(0, 10))

        # 4. Category
        ctk.CTkLabel(
            form_scroll, text="Category *", font=f["body"], text_color=c["text_main"]
        ).grid(row=8, column=0, sticky="w", padx=14, pady=(4, 2))

        existing_categories = self.controller.db.get_inventory_categories()
        category_options = existing_categories if existing_categories else ["Meals", "Drinks", "Snacks", "Desserts"]

        category_combo = ctk.CTkComboBox(
            form_scroll,
            values=category_options,
            height=36,
            font=f["body"],
            fg_color=input_bg,
            border_color=c["border"],
            button_color=c["primary"],
            button_hover_color=c["primary_hover"],
            text_color=c["text_main"]
        )
        category_combo.set(category_options[0])
        category_combo.grid(row=9, column=0, sticky="ew", padx=14, pady=(0, 10))

        # 5. Optional Image Picker
        ctk.CTkLabel(
            form_scroll, text="Product Image (Optional)", font=f["body"], text_color=c["text_main"]
        ).grid(row=10, column=0, sticky="w", padx=14, pady=(4, 2))

        img_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        img_row.grid(row=11, column=0, sticky="ew", padx=14, pady=(0, 12))
        img_row.grid_columnconfigure(0, weight=1)

        selected_source_path = {"path": ""}

        image_entry = ctk.CTkEntry(
            img_row,
            placeholder_text="No image selected",
            height=36,
            font=f["body"],
            fg_color=input_bg,
            border_color=c["border"],
            text_color=c["text_muted"]
        )
        image_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        def browse_image():
            file_path = filedialog.askopenfilename(
                parent=dialog,
                title="Select Menu Item Image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp")]
            )
            if file_path:
                selected_source_path["path"] = file_path
                image_entry.delete(0, "end")
                image_entry.insert(0, os.path.basename(file_path))

        ctk.CTkButton(
            img_row,
            text="Browse...",
            width=95,
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=browse_image
        ).grid(row=0, column=1)

        # --- Fixed Bottom Action Bar ---
        footer_bar = ctk.CTkFrame(
            dialog,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"]
        )
        footer_bar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer_bar.grid_columnconfigure((0, 1), weight=1)

        def save_item():
            sku_val = sku_entry.get().strip().upper()
            name_val = name_entry.get().strip()
            price_val = price_entry.get().strip()
            category_val = category_combo.get().strip()

            if not sku_val or not name_val or not price_val or not category_val:
                messagebox.showwarning(
                    "Missing Fields",
                    "Please fill in SKU, Item Name, Price, and Category.",
                    parent=dialog
                )
                return

            try:
                numeric_price = float(price_val)
                if numeric_price < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "Invalid Price",
                    "Please enter a valid non-negative number for the price.",
                    parent=dialog
                )
                return

            if self.controller.db.sku_exists(sku_val):
                confirm = messagebox.askyesno(
                    "SKU Already Exists",
                    f"SKU '{sku_val}' already exists in the menu.\nDo you want to overwrite it with these new details?",
                    parent=dialog
                )
                if not confirm:
                    return

            relative_image_path = ""
            if selected_source_path["path"]:
                try:
                    assets_dir = os.path.join(get_project_root(), "assets")
                    os.makedirs(assets_dir, exist_ok=True)
                    filename = os.path.basename(selected_source_path["path"])
                    dest_path = os.path.join(assets_dir, filename)

                    if os.path.abspath(selected_source_path["path"]) != os.path.abspath(dest_path):
                        shutil.copy2(selected_source_path["path"], dest_path)

                    relative_image_path = f"assets/{filename}"
                except Exception as e:
                    messagebox.showerror(
                        "Image Error",
                        f"Could not copy image to assets folder:\n{e}",
                        parent=dialog
                    )
                    return

            success, msg = self.controller.db.add_inventory_item(
                sku=sku_val,
                name=name_val,
                price=numeric_price,
                category=category_val,
                image_path=relative_image_path
            )

            if success:
                if "CashierFrame" in self.controller.frames:
                    self.controller.frames["CashierFrame"].load_menu()
                messagebox.showinfo("Item Saved", msg, parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Save Failed", msg, parent=dialog)

        ctk.CTkButton(
            footer_bar,
            text="Cancel",
            height=38,
            font=f["button"],
            fg_color=c["border"],
            hover_color=c["text_muted"],
            text_color=c["text_main"],
            command=dialog.destroy
        ).grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=10)

        ctk.CTkButton(
            footer_bar,
            text="Save Menu Item",
            height=38,
            font=f["button"],
            fg_color=gold_bg,
            hover_color=gold_hv,
            text_color=c.get("text_on_gold", "#0F172A"),
            command=save_item
        ).grid(row=0, column=1, sticky="ew", padx=(6, 12), pady=10)

        sku_entry.focus_set()

    def apply_theme(self):
        c = self.controller.colors
        gold_bg = c.get("accent_gold", c.get("brand_gold", "#FACC15"))
        gold_hv = c.get("gold_hover", c.get("brand_gold_hover", "#EAB308"))

        self.configure(fg_color=c["bg_main"])
        self.top_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.bottom_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.title_label.configure(text_color=c["text_main"])
        self.total_items_label.configure(text_color=c["text_green"])
        self.add_item_btn.configure(
            fg_color=gold_bg,
            hover_color=gold_hv,
            text_color=c.get("text_on_gold", "#0F172A")
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
            label_text_color=gold_bg
        )
        self.load_daily_data()