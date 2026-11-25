import customtkinter as ctk
from tkinter import messagebox


class DeleteItemDialog(ctk.CTkToplevel):
    """Scrollable modal dialog to search and delete active menu/inventory items."""

    def __init__(self, parent, controller, on_deleted=None):
        super().__init__(parent)
        self.withdraw()

        self.controller = controller
        self.on_deleted = on_deleted

        c = controller.colors
        f = controller.fonts
        self.title("Delete Menu / Inventory Item")
        self.configure(fg_color=c["bg_main"])
        self.transient(parent.winfo_toplevel())

        root = parent.winfo_toplevel()
        if root.winfo_width() <= 1 or root.winfo_height() <= 1:
            root.update_idletasks()
        win_w = 560
        win_h = min(600, max(440, root.winfo_height() - 60))
        x = root.winfo_x() + (root.winfo_width() - win_w) // 2
        y = root.winfo_y() + (root.winfo_height() - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{max(0, x)}+{max(0, y)}")
        self.minsize(480, 400)
        self.resizable(True, True)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._build_filters(c, f)
        self._build_list_area(c, f)
        self._build_footer(c, f)

        self._load_items()

        self.deiconify()
        self.lift()
        self.grab_set()
        self.search_entry.focus_set()

    def _build_filters(self, c: dict, f: dict) -> None:
        header_card = ctk.CTkFrame(
            self, fg_color=c["bg_card"], corner_radius=12, border_width=1, border_color=c["border"]
        )
        header_card.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        header_card.grid_columnconfigure(0, weight=1)
        header_card.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            header_card,
            text="Delete Menu / Inventory Item",
            font=f["header"],
            text_color=c["accent_gold"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            header_card,
            text="Deleted items are removed from the Cashier menu while keeping historical sales intact.",
            font=f["small"],
            text_color=c["text_muted"],
            wraplength=500,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            header_card,
            textvariable=self.search_var,
            placeholder_text="Search by item name or SKU...",
            height=36,
            font=f["body"],
            fg_color=c["bg_input"],
            border_color=c["border"],
            text_color=c["text_main"],
        )
        self.search_entry.grid(row=2, column=0, sticky="ew", padx=(14, 8), pady=(0, 12))
        self.search_entry.bind("<KeyRelease>", lambda _e: self._load_items())

        self.category_var = ctk.StringVar(value="All Categories")
        self.category_menu = ctk.CTkOptionMenu(
            header_card,
            variable=self.category_var,
            values=["All Categories"],
            width=165,
            height=36,
            font=f["small"],
            fg_color=c["primary"],
            button_color=c["primary_hover"],
            button_hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=lambda _: self._load_items(),
        )
        self.category_menu.grid(row=2, column=1, sticky="e", padx=(0, 14), pady=(0, 12))

    def _build_list_area(self, c: dict, f: dict) -> None:
        self.list_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.list_scroll.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 8))
        self.list_scroll.grid_columnconfigure(0, weight=1)

        self.bind("<MouseWheel>", self._on_mousewheel)

    def _build_footer(self, c: dict, f: dict) -> None:
        footer = ctk.CTkFrame(
            self, fg_color=c["bg_card"], corner_radius=12, border_width=1, border_color=c["border"]
        )
        footer.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            footer,
            text="",
            font=f["small"],
            text_color=c["text_muted"],
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=14, pady=10)

        ctk.CTkButton(
            footer,
            text="Close",
            width=110,
            height=36,
            font=f["button"],
            fg_color=c["border"],
            hover_color=c["text_muted"],
            text_color=c["text_main"],
            command=self.destroy,
        ).grid(row=0, column=1, sticky="e", padx=14, pady=10)

    def _on_mousewheel(self, event):
        if not self.list_scroll.winfo_exists() or event.delta == 0:
            return None
        canvas = self.list_scroll._parent_canvas
        if canvas.yview() == (0.0, 1.0):
            return "break"
        step = int(-1 * (event.delta / 120))
        if step == 0:
            step = -1 if event.delta > 0 else 1
        canvas.yview_scroll(step, "units")
        return "break"

    def _refresh_categories(self) -> None:
        categories = ["All Categories"] + self.controller.db.get_inventory_categories()
        self.category_menu.configure(values=categories)
        if self.category_var.get() not in categories:
            self.category_var.set("All Categories")

    def _load_items(self) -> None:
        self._refresh_categories()

        for widget in self.list_scroll.winfo_children():
            widget.destroy()

        c = self.controller.colors
        f = self.controller.fonts
        danger_bg = c.get("danger", "#DC2626")
        danger_hover = c.get("danger_hover", "#B91C1C")

        items = self.controller.db.get_menu_items(
            category=self.category_var.get(),
            sort_by="Name (Asc)",
            search_query=self.search_var.get().strip(),
        )

        self.status_label.configure(text=f"Showing {len(items)} active menu item(s)")

        if not items:
            ctk.CTkLabel(
                self.list_scroll,
                text="No matching menu items found.",
                font=f["body"],
                text_color=c["text_muted"],
            ).grid(row=0, column=0, pady=24, padx=10)
            return

        for idx, item in enumerate(items):
            sku = item["sku"]
            name = item["name"]
            price = float(item["price"])
            category = item["category"]

            row_card = ctk.CTkFrame(
                self.list_scroll,
                fg_color=c["bg_input"],
                corner_radius=8,
                border_width=1,
                border_color=c["border"],
            )
            row_card.grid(row=idx, column=0, sticky="ew", padx=6, pady=4)
            row_card.grid_columnconfigure(0, weight=1)

            info_frame = ctk.CTkFrame(row_card, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="w", padx=12, pady=8)

            ctk.CTkLabel(
                info_frame,
                text=name,
                font=f["subheader"],
                text_color=c["text_main"],
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_frame,
                text=f"SKU: {sku}   •   {category}   •   ₱{price:,.2f}",
                font=f["small"],
                text_color=c["text_muted"],
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkButton(
                row_card,
                text="Delete",
                width=84,
                height=32,
                font=f["small"],
                fg_color=danger_bg,
                hover_color=danger_hover,
                text_color="#FFFFFF",
                command=lambda s=sku, n=name: self._confirm_delete(s, n),
            ).grid(row=0, column=1, sticky="e", padx=12, pady=8)

    def _confirm_delete(self, sku: str, name: str) -> None:
        confirmed = messagebox.askyesno(
            "Confirm Delete Menu Item",
            f"Are you sure you want to delete '{name}' ({sku}) from the menu?\n\n"
            "Past sales reports will remain intact.",
            parent=self,
        )
        if not confirmed:
            return

        success, msg = self.controller.db.delete_inventory_item(sku)
        if success:
            if callable(self.on_deleted):
                self.on_deleted()
            self._load_items()
            messagebox.showinfo("Item Deleted", msg, parent=self)
        else:
            messagebox.showerror("Delete Failed", msg, parent=self)