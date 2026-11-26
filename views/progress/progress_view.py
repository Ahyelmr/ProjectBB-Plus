import csv
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog
from components.page_header import PageHeader
from views.progress.add_item_dialog import AddItemDialog
from views.progress.delete_item_dialog import DeleteItemDialog


class ProgressFrame(ctk.CTkFrame):
    RENDER_BATCH_SIZE = 15
    RENDER_DELAY_MS = 10

    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller
        self.current_view = "Items Sold Summary"
        self.daily_tally = []
        self.orders_sequence_data = []
        self._available_dates = []

        self._render_job = None
        self._render_token = 0
        self._inventory_dirty = False
        self._theme_dirty = False

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Row 0: Header
        self.header = PageHeader(
            self,
            controller=controller,
            title="Sales, Orders & Inventory",
            back_command=self._go_back,
            logo_size=44,
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        self.inventory_btn = ctk.CTkButton(
            self.header.right_slot,
            text="View Inventory & Menu List",
            width=210,
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=self._open_inventory_view,
        )
        self.inventory_btn.pack(side="left", padx=(0, 8))

        self.refresh_btn = ctk.CTkButton(
            self.header.right_slot,
            text="Refresh Data",
            width=130,
            height=36,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=lambda: self.load_daily_data(keep_selected_date=True),
        )
        self.refresh_btn.pack(side="left")

        # Row 1: View Mode Switcher & Historical Date Selector
        self.switch_bar = ctk.CTkFrame(
            self, fg_color=c["bg_card"], corner_radius=12, border_width=1, border_color=c["border"]
        )
        self.switch_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 6))

        self.view_mode_selector = ctk.CTkSegmentedButton(
            self.switch_bar,
            values=["Items Sold Summary", "Orders in Sequence"],
            font=f["button"],
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
            text_color="#FFFFFF",
            height=36,
            command=self.switch_view,
        )
        self.view_mode_selector.set(self.current_view)
        self.view_mode_selector.pack(side="left", padx=12, pady=8)

        date_controls = ctk.CTkFrame(self.switch_bar, fg_color="transparent")
        date_controls.pack(side="right", padx=12, pady=8)

        self.date_label = ctk.CTkLabel(
            date_controls, text="Record Date:", font=f["body"], text_color=c["text_main"]
        )
        self.date_label.pack(side="left", padx=(0, 8))

        self.prev_date_btn = ctk.CTkButton(
            date_controls,
            text="< Prev",
            width=68,
            height=34,
            font=f["small"],
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_width=1,
            border_color=c["border"],
            text_color=c["text_main"],
            command=self._select_previous_date,
        )
        self.prev_date_btn.pack(side="left", padx=(0, 6))

        today_str = datetime.now().strftime("%Y-%m-%d")
        self.date_var = ctk.StringVar(value=f"{today_str} (Today)")
        self.date_menu = ctk.CTkOptionMenu(
            date_controls,
            variable=self.date_var,
            values=[f"{today_str} (Today)"],
            width=190,
            height=34,
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda _: self._on_date_changed(),
        )
        self.date_menu.pack(side="left", padx=(0, 6))

        self.next_date_btn = ctk.CTkButton(
            date_controls,
            text="Next >",
            width=68,
            height=34,
            font=f["small"],
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_width=1,
            border_color=c["border"],
            text_color=c["text_main"],
            command=self._select_next_date,
        )
        self.next_date_btn.pack(side="left")

        self.delete_date_btn = ctk.CTkButton(
            date_controls,
            text="Delete Date",
            width=98,
            height=34,
            font=f["small"],
            fg_color=c["border"],
            hover_color=c.get("danger_hover", "#B91C1C"),
            text_color=c["text_muted"],
            state="disabled",
            command=self._delete_selected_date_records,
        )
        self.delete_date_btn.pack(side="left", padx=(8, 0))

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

        self.delete_item_btn = ctk.CTkButton(
            self.bottom_bar,
            text="- Delete Menu Item",
            height=36,
            font=f["button"],
            fg_color=c.get("danger", "#DC2626"),
            hover_color=c.get("danger_hover", "#B91C1C"),
            text_color="#FFFFFF",
            command=self.open_delete_item_dialog,
        )
        self.delete_item_btn.pack(side="right", padx=6, pady=10)

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

        self.bind("<Configure>", self._on_configure)

    @staticmethod
    def _normalize_order_type(order_type: str | None) -> str:
        norm = " ".join(
            (order_type or "DINE IN").strip().upper().replace("-", " ").replace("_", " ").split()
        )
        if norm in ("TAKE OUT", "TAKEOUT", "TO", "TO GO", "TOGO", "TAKEAWAY", "TAKE AWAY"):
            return "TAKE OUT"
        return "DINE IN"

    @classmethod
    def _format_order_code(cls, order_type: str, seq_num: int) -> str:
        prefix = "TO" if cls._normalize_order_type(order_type) == "TAKE OUT" else "DI"
        return f"{prefix} {int(seq_num):03d}"

    @classmethod
    def _format_order_type_label(cls, order_type: str) -> str:
        return "Take Out" if cls._normalize_order_type(order_type) == "TAKE OUT" else "Dine In"
    def _on_configure(self, event) -> None:
        if event.widget is self:
            self.header.scale_logo_for_height(event.height, 38, 54, 0.06)

    def _cancel_pending_render(self) -> None:
        self._render_token += 1
        if self._render_job is not None:
            try:
                self.after_cancel(self._render_job)
            except Exception:
                pass
            self._render_job = None

    def _clear_data_frame(self) -> None:
        for widget in self.data_frame.winfo_children():
            widget.destroy()
        try:
            self.data_frame._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _go_back(self):
        self._cancel_pending_render()
        if self._inventory_dirty and "CashierFrame" in self.controller.frames:
            self.controller.frames["CashierFrame"].load_menu()
            self._inventory_dirty = False
        self.controller.show_frame("CashierFrame")

    def _open_inventory_view(self):
        self._cancel_pending_render()
        self.controller.show_frame("InventoryFrame")

    def _format_date_option(self, date_str: str) -> str:
        today_str = datetime.now().strftime("%Y-%m-%d")
        return f"{date_str} (Today)" if date_str == today_str else date_str

    def _get_selected_date(self) -> str:
        raw = self.date_var.get().strip()
        return raw.split(" ")[0] if raw else datetime.now().strftime("%Y-%m-%d")

    def _update_delete_date_button_state(self) -> None:
        c = self.controller.colors
        selected_date = self._get_selected_date()
        today_str = datetime.now().strftime("%Y-%m-%d")
        can_delete = selected_date < today_str and selected_date in self._available_dates

        if can_delete:
            self.delete_date_btn.configure(
                state="normal",
                fg_color=c.get("danger", "#DC2626"),
                hover_color=c.get("danger_hover", "#B91C1C"),
                text_color="#FFFFFF",
            )
        else:
            self.delete_date_btn.configure(
                state="disabled",
                fg_color=c["border"],
                hover_color=c["border"],
                text_color=c["text_muted"],
            )

    def _refresh_date_options(self, keep_selected: bool = False) -> None:
        previous_date = self._get_selected_date() if keep_selected else None
        self._available_dates = self.controller.db.get_available_order_dates()
        formatted_values = [self._format_date_option(d) for d in self._available_dates]
        self.date_menu.configure(values=formatted_values)

        if previous_date and previous_date in self._available_dates:
            self.date_var.set(self._format_date_option(previous_date))
        else:
            self.date_var.set(formatted_values[0])

        self._update_delete_date_button_state()

    def _select_previous_date(self) -> None:
        if not self._available_dates:
            return
        current = self._get_selected_date()
        if current in self._available_dates:
            idx = self._available_dates.index(current)
            if idx + 1 < len(self._available_dates):
                self.date_var.set(self._format_date_option(self._available_dates[idx + 1]))
                self._on_date_changed()

    def _select_next_date(self) -> None:
        if not self._available_dates:
            return
        current = self._get_selected_date()
        if current in self._available_dates:
            idx = self._available_dates.index(current)
            if idx - 1 >= 0:
                self.date_var.set(self._format_date_option(self._available_dates[idx - 1]))
                self._on_date_changed()

    def _delete_selected_date_records(self) -> None:
        selected_date = self._get_selected_date()
        today_str = datetime.now().strftime("%Y-%m-%d")

        if selected_date >= today_str:
            messagebox.showwarning(
                "Action Not Allowed",
                "Today's sales records cannot be deleted. Select a previous date instead.",
            )
            return

        confirmed = messagebox.askyesno(
            "Delete Sales Record Date",
            f"Are you sure you want to permanently delete all sales and order records for {selected_date}?\n\n"
            "This action cannot be undone.",
        )
        if not confirmed:
            return

        success, msg = self.controller.db.delete_sales_records_by_date(selected_date)
        if success:
            messagebox.showinfo("Records Deleted", msg)
            self.load_daily_data(keep_selected_date=False)
        else:
            messagebox.showerror("Delete Failed", msg)

    def _update_section_header(self) -> None:
        selected_date = self._get_selected_date()
        is_today = selected_date == datetime.now().strftime("%Y-%m-%d")
        if self.current_view == "Items Sold Summary":
            label = (
                "Items Ordered Today (Completed)"
                if is_today
                else f"Items Sold on {selected_date} (Completed)"
            )
        else:
            label = (
                "All Orders in Sequence (Today)"
                if is_today
                else f"All Orders in Sequence ({selected_date})"
            )
        self.data_frame.configure(label_text=label)

    def _on_date_changed(self) -> None:
        self._update_delete_date_button_state()
        self._update_section_header()
        self.load_daily_data(keep_selected_date=True)

    def on_show(self):
        self._theme_dirty = False
        self.load_daily_data(keep_selected_date=False)

    def switch_view(self, selected_mode: str):
        if selected_mode == self.current_view:
            return
        self.current_view = selected_mode
        self._update_section_header()
        self.load_daily_data(keep_selected_date=True)

    def load_daily_data(self, keep_selected_date: bool = False):
        self._cancel_pending_render()
        self._refresh_date_options(keep_selected=keep_selected_date)
        self._update_section_header()
        self._clear_data_frame()

        token = self._render_token
        target_date = self._get_selected_date()
        if self.current_view == "Items Sold Summary":
            self._render_item_tally(target_date, token)
        else:
            self._render_orders_sequence(target_date, token)

    def _render_item_tally(self, target_date: str, token: int = None):
        if token is None:
            token = self._render_token

        c = self.controller.colors
        f = self.controller.fonts
        is_today = target_date == datetime.now().strftime("%Y-%m-%d")
        date_prefix = "" if is_today else f"[{target_date}]  "
        self.daily_tally = self.controller.db.get_daily_item_tally(target_date)

        if not self.daily_tally:
            empty_msg = (
                "No completed item orders recorded today."
                if is_today
                else f"No completed item orders recorded on {target_date}."
            )
            ctk.CTkLabel(
                self.data_frame,
                text=empty_msg,
                font=f["body"],
                text_color=c["text_muted"],
            ).grid(row=0, column=0, pady=24, padx=10)
            self.total_items_label.configure(
                text=f"{date_prefix}Total Items Sold: 0  |  Total Earned: ₱0.00"
            )
            return

        total_items = sum(row[1] for row in self.daily_tally)
        total_earned_all = sum(row[2] for row in self.daily_tally)
        self.total_items_label.configure(
            text=f"{date_prefix}Total Items Sold: {total_items}  |  Total Earned: ₱{total_earned_all:,.2f}"
        )

        self._render_tally_batch(0, target_date, token)

    def _render_tally_batch(self, start_idx: int, target_date: str, token: int) -> None:
        self._render_job = None
        if token != self._render_token or not self.winfo_exists():
            return

        c = self.controller.colors
        f = self.controller.fonts
        is_today = target_date == datetime.now().strftime("%Y-%m-%d")
        qty_prefix = "Quantity Ordered Today" if is_today else f"Quantity Sold ({target_date})"
        end_idx = min(start_idx + self.RENDER_BATCH_SIZE, len(self.daily_tally))

        for idx in range(start_idx, end_idx):
            item_name, qty_sold, item_earned = self.daily_tally[idx]

            row_card = ctk.CTkFrame(
                self.data_frame,
                fg_color=c["bg_input"],
                corner_radius=8,
                border_width=1,
                border_color=c["border"],
            )
            row_card.grid(row=idx, column=0, sticky="ew", pady=4, padx=8)
            row_card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row_card, text=item_name, font=f["body"], text_color=c["text_main"]
            ).grid(row=0, column=0, sticky="w", padx=14, pady=10)

            ctk.CTkLabel(
                row_card,
                text=f"{qty_prefix}: {qty_sold}",
                font=f["subheader"],
                text_color=c["text_green"],
            ).grid(row=0, column=1, sticky="e", padx=(8, 12), pady=10)

            ctk.CTkLabel(
                row_card,
                text=f"|   Total Earned: ₱{item_earned:,.2f}",
                font=f["subheader"],
                text_color=c["accent_gold"],
            ).grid(row=0, column=2, sticky="e", padx=(0, 14), pady=10)

        if end_idx < len(self.daily_tally):
            self._render_job = self.after(
                self.RENDER_DELAY_MS, lambda: self._render_tally_batch(end_idx, target_date, token)
            )

    def _render_orders_sequence(self, target_date: str, token: int = None):
        if token is None:
            token = self._render_token

        c = self.controller.colors
        f = self.controller.fonts
        is_today = target_date == datetime.now().strftime("%Y-%m-%d")
        date_label = "Today" if is_today else f"({target_date})"
        self.orders_sequence_data = self.controller.db.get_daily_orders_sequence(target_date)

        if not self.orders_sequence_data:
            empty_msg = (
                "No orders recorded today."
                if is_today
                else f"No orders recorded on {target_date}."
            )
            ctk.CTkLabel(
                self.data_frame, text=empty_msg, font=f["body"], text_color=c["text_muted"]
            ).grid(row=0, column=0, pady=24, padx=10)
            self.total_items_label.configure(text=f"Total Orders {date_label}: 0  |  Sales: ₱0.00")
            return

        total_sales = sum(order["total_amount"] for order in self.orders_sequence_data)
        self.total_items_label.configure(
            text=f"Total Orders {date_label}: {len(self.orders_sequence_data)}  |  Total Sales: ₱{total_sales:,.2f}"
        )

        self._render_orders_batch(0, token)

    def _render_orders_batch(self, start_idx: int, token: int) -> None:
        self._render_job = None
        if token != self._render_token or not self.winfo_exists():
            return

        c = self.controller.colors
        f = self.controller.fonts
        end_idx = min(start_idx + self.RENDER_BATCH_SIZE, len(self.orders_sequence_data))

        for idx in range(start_idx, end_idx):
            order = self.orders_sequence_data[idx]
            status = order["status"]
            status_color = (
                c["text_green"] if status == "COMPLETED" else "#60A5FA" if status == "READY" else c["accent_gold"]
            )
            order_type = order.get("order_type", "DINE IN")
            order_code = order.get("order_code") or self._format_order_code(
                order_type, order["sequence_number"]
            )
            order_type_label = self._format_order_type_label(order_type)
            time_str = order["order_date"].split(" ")[-1] if " " in order["order_date"] else order["order_date"]
            discount_note = (
                f"  (Discount: {order['discount_applied']})" if order["discount_applied"] != "None" else ""
            )
            amount_tendered = float(order.get("amount_tendered", order["total_amount"]))
            change_amount = float(order.get("change_amount", 0.0))

            card = ctk.CTkFrame(
                self.data_frame,
                fg_color=c["bg_input"],
                corner_radius=10,
                border_width=1,
                border_color=c["border"],
            )
            card.grid(row=idx, column=0, sticky="ew", pady=6, padx=8)
            card.grid_columnconfigure(0, weight=1)
            card.grid_columnconfigure(1, weight=0)

            ctk.CTkLabel(
                card,
                text=f"{order_code} ({order_type_label})   •   {time_str}   •   [{status}]",
                font=f["subheader"],
                text_color=status_color,
            ).grid(row=0, column=0, sticky="w", padx=(14, 8), pady=(10, 4))

            ctk.CTkLabel(
                card,
                text=f"Total: ₱{order['total_amount']:.2f}{discount_note}",
                font=f["subheader"],
                text_color=c["accent_gold"] if discount_note else c["text_main"],
            ).grid(row=0, column=1, sticky="e", padx=(8, 14), pady=(10, 4))

            ctk.CTkFrame(card, height=1, fg_color=c["border"]).grid(
                row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=3
            )

            items = order.get("items", [])
            if items:
                left_lines = "\n".join(
                    f"•  {item['quantity']}x {item['name']}  ({item['category']})" for item in items
                )
                right_lines = "\n".join(f"₱{item['line_total']:.2f}" for item in items)

                ctk.CTkLabel(
                    card,
                    text=left_lines,
                    font=f["body"],
                    text_color=c["text_main"],
                    justify="left",
                    anchor="w",
                ).grid(row=2, column=0, sticky="nw", padx=(18, 8), pady=(4, 6))

                ctk.CTkLabel(
                    card,
                    text=right_lines,
                    font=f["body"],
                    text_color=c["text_muted"],
                    justify="right",
                    anchor="e",
                ).grid(row=2, column=1, sticky="ne", padx=(8, 18), pady=(4, 6))

            ctk.CTkLabel(
                card,
                text=f"Paid: ₱{amount_tendered:.2f}   •   Change: ₱{change_amount:.2f}",
                font=f["small"],
                text_color=c["text_green"],
                anchor="e",
            ).grid(row=3, column=0, columnspan=2, sticky="e", padx=18, pady=(0, 10))

        if end_idx < len(self.orders_sequence_data):
            self._render_job = self.after(
                self.RENDER_DELAY_MS, lambda: self._render_orders_batch(end_idx, token)
            )

    def export_csv(self):
        selected_date = self._get_selected_date()
        date_stamp = selected_date.replace("-", "")

        orders_data = self.controller.db.get_daily_orders_sequence(selected_date)
        tally_data = self.controller.db.get_daily_item_tally(selected_date)

        if not orders_data and not tally_data:
            messagebox.showwarning(
                "No Data", f"There are no sales records to export for {selected_date}."
            )
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"daily_sales_report_{date_stamp}.csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not filepath:
            return

        cashier_name = getattr(self.controller, "current_user", None) or "Cashier"

        total_orders = len(orders_data)
        dine_in_orders = 0
        take_out_orders = 0
        total_gross_sales = 0.0
        total_discounts = 0.0
        total_net_sales = 0.0

        with open(filepath, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)

            # Section 1: Order Log
            writer.writerow([
                "Order ID",
                "Order Type",
                "Time",
                "Cashier",
                "Subtotal",
                "Discount",
                "Final Total",
                "Items Ordered",
                "Status",
            ])

            for order in orders_data:
                raw_type = order.get("order_type", "DINE IN")
                order_code = order.get("order_code") or self._format_order_code(
                    raw_type, order["sequence_number"]
                )
                order_type_label = self._format_order_type_label(raw_type)

                if order_type_label == "Take Out":
                    take_out_orders += 1
                else:
                    dine_in_orders += 1

                raw_dt = order.get("order_date", "")
                try:
                    dt_obj = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M:%S")
                    time_str = dt_obj.strftime("%I:%M:%S %p").lstrip("0")
                except ValueError:
                    time_str = raw_dt.split(" ")[-1] if " " in raw_dt else raw_dt

                items = order.get("items", [])
                subtotal = round(sum(float(item["line_total"]) for item in items), 2)
                final_total = round(float(order["total_amount"]), 2)
                discount = round(max(0.0, subtotal - final_total), 2)

                items_ordered_str = ", ".join(
                    f"{item['quantity']}x {item['name']}" for item in items
                )

                total_gross_sales += subtotal
                total_discounts += discount
                total_net_sales += final_total

                writer.writerow([
                    order_code,
                    order_type_label,
                    time_str,
                    cashier_name,
                    f"{subtotal:.2f}",
                    f"{discount:.2f}",
                    f"{final_total:.2f}",
                    items_ordered_str,
                    order["status"],
                ])

            # Section 2: Daily Summary
            writer.writerow([])
            writer.writerow(["DAILY SUMMARY"])
            writer.writerow(["Total Orders:", total_orders])
            writer.writerow(["Dine In Orders:", dine_in_orders])
            writer.writerow(["Take Out Orders:", take_out_orders])
            writer.writerow(["Total Gross Sales:", f"{total_gross_sales:.2f}"])
            writer.writerow(["Total Discounts:", f"{total_discounts:.2f}"])
            writer.writerow(["Total Net Sales:", f"{total_net_sales:.2f}"])

            # Section 3: Itemized Tally
            writer.writerow([])
            writer.writerow(["ITEMIZED TALLY"])
            writer.writerow(["Item Name", "Quantity Sold", "Total Earned"])
            for item_name, qty_sold, item_earned in tally_data:
                writer.writerow([item_name, qty_sold, f"{item_earned:.2f}"])

        messagebox.showinfo("Export Successful", f"Daily sales report saved to {filepath}")

    def upload_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            self.controller.db.import_inventory_from_csv(filepath)
            self._inventory_dirty = True
            messagebox.showinfo("Success", "Inventory successfully updated from CSV.")

    def open_add_item_dialog(self):
        def _mark_inventory_dirty():
            self._inventory_dirty = True

        AddItemDialog(self, self.controller, on_saved=_mark_inventory_dirty)

    def open_delete_item_dialog(self):
        def _mark_inventory_dirty():
            self._inventory_dirty = True

        DeleteItemDialog(self, self.controller, on_deleted=_mark_inventory_dirty)

    def apply_theme(self):
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        self.header.apply_theme()
        self.switch_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.date_label.configure(text_color=c["text_main"])
        self.prev_date_btn.configure(
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_color=c["border"],
            text_color=c["text_main"],
        )
        self.next_date_btn.configure(
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_color=c["border"],
            text_color=c["text_main"],
        )
        self.date_menu.configure(
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
        )
        self._update_delete_date_button_state()
        self.bottom_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.total_items_label.configure(text_color=c["text_green"])
        self.inventory_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.refresh_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.export_btn.configure(fg_color=c["accent_green"], hover_color=c["green_hover"])
        self.import_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.delete_item_btn.configure(
            fg_color=c.get("danger", "#DC2626"),
            hover_color=c.get("danger_hover", "#B91C1C"),
        )
        self.add_item_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.view_mode_selector.configure(
            fg_color=c["bg_input"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["bg_input"],
            unselected_hover_color=c["border"],
        )
        self.data_frame.configure(
            fg_color=c["bg_card"],
            border_color=c["border"],
            label_fg_color=c["border"],
            label_text_color=c["accent_gold"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )

        if self.winfo_viewable():
            self._theme_dirty = False
            self.load_daily_data(keep_selected_date=True)
        else:
            self._cancel_pending_render()
            self._theme_dirty = True