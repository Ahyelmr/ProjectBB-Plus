import csv
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog
from components.page_header import PageHeader
from database.inventory_repo import SORT_CLAUSES
from views.progress.add_item_dialog import AddItemDialog


class InventoryFrame(ctk.CTkFrame):
    """Full-screen database viewer and manager for menu & inventory items."""

    RENDER_BATCH_SIZE = 20
    RENDER_DELAY_MS = 10

    def __init__(self, parent, controller):
        c = controller.colors
        f = controller.fonts
        super().__init__(parent, fg_color=c["bg_main"])
        self.controller = controller
        self.inventory_items = []

        self._render_job = None
        self._render_token = 0
        self._inventory_dirty = False

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Row 0: Header
        self.header = PageHeader(
            self,
            controller=controller,
            title="Menu & Inventory List",
            back_command=self._go_back,
            logo_size=44,
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        self.refresh_btn = ctk.CTkButton(
            self.header.right_slot,
            text="Refresh List",
            width=130,
            height=36,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=self.load_inventory,
        )
        self.refresh_btn.pack()

        # Row 1: Filter & Search Toolbar
        self.filter_bar = ctk.CTkFrame(
            self, fg_color=c["bg_card"], corner_radius=12, border_width=1, border_color=c["border"]
        )
        self.filter_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 6))
        self.filter_bar.grid_columnconfigure(1, weight=1)

        self.search_label = ctk.CTkLabel(
            self.filter_bar, text="Search:", font=f["body"], text_color=c["text_main"]
        )
        self.search_label.grid(row=0, column=0, padx=(14, 6), pady=10)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.filter_bar,
            textvariable=self.search_var,
            placeholder_text="Filter by SKU or item name...",
            height=34,
            font=f["body"],
            fg_color=c["bg_input"],
            border_color=c["border"],
            text_color=c["text_main"],
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=10)
        self.search_entry.bind("<KeyRelease>", lambda _: self.load_inventory())

        self.clear_search_btn = ctk.CTkButton(
            self.filter_bar,
            text="Clear",
            width=70,
            height=34,
            font=f["small"],
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_width=1,
            border_color=c["border"],
            text_color=c["text_main"],
            command=self._clear_search,
        )
        self.clear_search_btn.grid(row=0, column=2, padx=(0, 14), pady=10)

        self.category_var = ctk.StringVar(value="All Categories")
        self.category_menu = ctk.CTkOptionMenu(
            self.filter_bar,
            variable=self.category_var,
            values=["All Categories"],
            width=185,
            height=34,
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda _: self.load_inventory(),
        )
        self.category_menu.grid(row=0, column=3, padx=(0, 10), pady=10)

        self.sort_var = ctk.StringVar(value="Name (Asc)")
        self.sort_menu = ctk.CTkOptionMenu(
            self.filter_bar,
            variable=self.sort_var,
            values=list(SORT_CLAUSES.keys()),
            width=155,
            height=34,
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda _: self.load_inventory(),
        )
        self.sort_menu.grid(row=0, column=4, padx=(0, 14), pady=10)

        # Row 2: Inventory Items List
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Registered Menu Items (Database)",
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
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=6)
        self.list_frame.grid_columnconfigure(0, weight=1)

        # Row 3: Bottom Bar
        self.bottom_bar = ctk.CTkFrame(
            self, fg_color=c["bg_card"], corner_radius=12, border_width=1, border_color=c["border"]
        )
        self.bottom_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(6, 10))

        self.summary_label = ctk.CTkLabel(
            self.bottom_bar,
            text="Total Menu Items: 0",
            font=f["header"],
            text_color=c["text_green"],
        )
        self.summary_label.pack(side="left", padx=16, pady=10)

        self.export_btn = ctk.CTkButton(
            self.bottom_bar,
            text="Export Menu CSV",
            height=36,
            font=f["button"],
            fg_color=c["accent_green"],
            hover_color=c["green_hover"],
            text_color="#FFFFFF",
            command=self.export_inventory_csv,
        )
        self.export_btn.pack(side="right", padx=(6, 12), pady=10)

        self.import_btn = ctk.CTkButton(
            self.bottom_bar,
            text="Import CSV",
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

        self.bind("<Configure>", self._on_configure)

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

    def _clear_list_frame(self) -> None:
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        try:
            self.list_frame._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _go_back(self) -> None:
        self._cancel_pending_render()
        if self._inventory_dirty and "CashierFrame" in self.controller.frames:
            self.controller.frames["CashierFrame"].load_menu()
            self._inventory_dirty = False
        self.controller.show_frame("ProgressFrame")

    def _clear_search(self) -> None:
        if self.search_var.get():
            self.search_var.set("")
            self.load_inventory()

    def _refresh_categories(self) -> None:
        categories = ["All Categories"] + self.controller.db.get_inventory_categories()
        self.category_menu.configure(values=categories)
        if self.category_var.get() not in categories:
            self.category_var.set("All Categories")

    def on_show(self) -> None:
        self._refresh_categories()
        self.load_inventory()

    def load_inventory(self) -> None:
        self._cancel_pending_render()
        self._clear_list_frame()

        token = self._render_token
        c = self.controller.colors
        f = self.controller.fonts

        selected_cat = self.category_var.get()
        selected_sort = self.sort_var.get()
        search_text = self.search_var.get()

        self.inventory_items = self.controller.db.get_menu_items(
            category=selected_cat,
            sort_by=selected_sort,
            search_query=search_text,
        )

        if not self.inventory_items:
            ctk.CTkLabel(
                self.list_frame,
                text="No menu or inventory items match your current filter.",
                font=f["body"],
                text_color=c["text_muted"],
            ).grid(row=0, column=0, pady=24, padx=10)
            self.summary_label.configure(text="Showing 0 Menu Items")
            return

        distinct_cats = {row["category"] for row in self.inventory_items}
        self.summary_label.configure(
            text=f"Showing {len(self.inventory_items)} Menu Item(s) across {len(distinct_cats)} Categor{'y' if len(distinct_cats) == 1 else 'ies'}"
        )
        self._render_batch(0, token)

    def _render_batch(self, start_idx: int, token: int) -> None:
        self._render_job = None
        if token != self._render_token or not self.winfo_exists():
            return

        c = self.controller.colors
        f = self.controller.fonts
        end_idx = min(start_idx + self.RENDER_BATCH_SIZE, len(self.inventory_items))

        for idx in range(start_idx, end_idx):
            item = self.inventory_items[idx]
            sku = item["sku"]
            name = item["name"]
            price = float(item["price"])
            category = item["category"]
            has_image = bool((item["image_path"] or "").strip())

            row_card = ctk.CTkFrame(
                self.list_frame,
                fg_color=c["bg_input"],
                corner_radius=8,
                border_width=1,
                border_color=c["border"],
            )
            row_card.grid(row=idx, column=0, sticky="ew", pady=4, padx=8)
            row_card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row_card,
                text=sku,
                font=f["subheader"],
                text_color=c["accent_gold"],
                width=110,
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=(14, 10), pady=10)

            ctk.CTkLabel(
                row_card,
                text=name,
                font=f["body"],
                text_color=c["text_main"],
                anchor="w",
            ).grid(row=0, column=1, sticky="w", padx=6, pady=10)

            ctk.CTkLabel(
                row_card,
                text=category,
                font=f["small"],
                text_color=c["text_muted"],
            ).grid(row=0, column=2, sticky="e", padx=12, pady=10)

            ctk.CTkLabel(
                row_card,
                text="Image: Set" if has_image else "No Image",
                font=f["small"],
                text_color=c["text_green"] if has_image else c["text_muted"],
            ).grid(row=0, column=3, sticky="e", padx=12, pady=10)

            ctk.CTkLabel(
                row_card,
                text=f"₱{price:,.2f}",
                font=f["subheader"],
                text_color=c["text_green"],
            ).grid(row=0, column=4, sticky="e", padx=(8, 16), pady=10)

        if end_idx < len(self.inventory_items):
            self._render_job = self.after(
                self.RENDER_DELAY_MS, lambda: self._render_batch(end_idx, token)
            )

    def open_add_item_dialog(self) -> None:
        def _on_saved():
            self._inventory_dirty = True
            self._refresh_categories()
            self.load_inventory()

        AddItemDialog(self, self.controller, on_saved=_on_saved)

    def upload_csv(self) -> None:
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            self.controller.db.import_inventory_from_csv(filepath)
            self._inventory_dirty = True
            self._refresh_categories()
            self.load_inventory()
            messagebox.showinfo("Success", "Inventory successfully updated from CSV.")

    def export_inventory_csv(self) -> None:
        if not self.inventory_items:
            messagebox.showwarning("No Data", "There are no menu items to export.")
            return

        date_stamp = datetime.now().strftime("%Y%m%d")
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile=f"menu_inventory_{date_stamp}.csv"
        )
        if filepath:
            with open(filepath, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["SKU", "Name", "Price", "Category", "Image Path"])
                for item in self.inventory_items:
                    writer.writerow([
                        item["sku"],
                        item["name"],
                        f"{float(item['price']):.2f}",
                        item["category"],
                        item["image_path"] or "",
                    ])
            messagebox.showinfo("Export Successful", f"Menu inventory saved to {filepath}")

    def apply_theme(self) -> None:
        c = self.controller.colors
        self.configure(fg_color=c["bg_main"])
        self.header.apply_theme()
        self.filter_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.search_label.configure(text_color=c["text_main"])
        self.search_entry.configure(
            fg_color=c["bg_input"], border_color=c["border"], text_color=c["text_main"]
        )
        self.clear_search_btn.configure(
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_color=c["border"],
            text_color=c["text_main"],
        )
        self.category_menu.configure(
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
        )
        self.sort_menu.configure(
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
        )
        self.list_frame.configure(
            fg_color=c["bg_card"],
            border_color=c["border"],
            label_fg_color=c["border"],
            label_text_color=c["accent_gold"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.bottom_bar.configure(fg_color=c["bg_card"], border_color=c["border"])
        self.summary_label.configure(text_color=c["text_green"])
        self.refresh_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )
        self.export_btn.configure(fg_color=c["accent_green"], hover_color=c["green_hover"])
        self.import_btn.configure(fg_color=c["primary"], hover_color=c["primary_hover"])
        self.add_item_btn.configure(
            fg_color=c["accent_gold"], hover_color=c["gold_hover"], text_color=c["text_on_gold"]
        )

        if self.winfo_viewable():
            self.load_inventory()