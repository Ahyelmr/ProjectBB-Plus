import os
import shutil
import customtkinter as ctk
from tkinter import messagebox, filedialog
from core.paths import get_assets_dir


class AddItemDialog(ctk.CTkToplevel):
    """Scrollable modal dialog to add or overwrite a menu/inventory item."""

    def __init__(self, parent, controller, on_saved=None):
        super().__init__(parent)
        self.controller = controller
        self.on_saved = on_saved
        self._selected_source_path = ""

        c = controller.colors
        f = controller.fonts
        self.title("Add Menu / Inventory Item")
        self.configure(fg_color=c["bg_main"])
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        root = parent.winfo_toplevel()
        root.update_idletasks()
        win_w = 500
        win_h = min(560, max(420, root.winfo_height() - 60))
        x = root.winfo_x() + (root.winfo_width() - win_w) // 2
        y = root.winfo_y() + (root.winfo_height() - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{max(0, x)}+{max(0, y)}")
        self.minsize(440, 380)
        self.resizable(True, True)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._build_form(c, f)
        self._build_footer(c, f)
        self.sku_entry.focus_set()

    def _build_form(self, c: dict, f: dict) -> None:
        self.form_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.form_scroll.grid(row=0, column=0, sticky="nsew", padx=14, pady=(14, 8))
        self.form_scroll.grid_columnconfigure(0, weight=1)

        self.bind("<MouseWheel>", self._on_mousewheel)

        ctk.CTkLabel(
            self.form_scroll, text="Add New Menu Item", font=f["header"], text_color=c["accent_gold"]
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            self.form_scroll,
            text="Fill in the product details below. Existing SKUs can be updated.",
            font=f["body"],
            text_color=c["text_muted"],
            wraplength=410,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))

        self.sku_entry = self._add_entry(2, "SKU Code *", "e.g., SKU01 or DRK-01", c, f)
        self.name_entry = self._add_entry(4, "Item Name *", "e.g., Classic Cheeseburger", c, f)
        self.price_entry = self._add_entry(6, "Price (₱) *", "e.g., 85.00", c, f)

        ctk.CTkLabel(
            self.form_scroll, text="Category *", font=f["body"], text_color=c["text_main"]
        ).grid(row=8, column=0, sticky="w", padx=14, pady=(4, 2))

        existing_cats = self.controller.db.get_inventory_categories()
        cat_options = existing_cats if existing_cats else ["Meals", "Drinks", "Snacks", "Desserts"]

        self.category_combo = ctk.CTkComboBox(
            self.form_scroll,
            values=cat_options,
            height=36,
            font=f["body"],
            fg_color=c["bg_input"],
            border_color=c["border"],
            button_color=c["primary"],
            button_hover_color=c["primary_hover"],
            text_color=c["text_main"],
        )
        self.category_combo.set(cat_options[0])
        self.category_combo.grid(row=9, column=0, sticky="ew", padx=14, pady=(0, 10))

        ctk.CTkLabel(
            self.form_scroll, text="Product Image (Optional)", font=f["body"], text_color=c["text_main"]
        ).grid(row=10, column=0, sticky="w", padx=14, pady=(4, 2))

        img_row = ctk.CTkFrame(self.form_scroll, fg_color="transparent")
        img_row.grid(row=11, column=0, sticky="ew", padx=14, pady=(0, 12))
        img_row.grid_columnconfigure(0, weight=1)

        self.image_entry = ctk.CTkEntry(
            img_row,
            placeholder_text="No image selected",
            height=36,
            font=f["body"],
            fg_color=c["bg_input"],
            border_color=c["border"],
            text_color=c["text_muted"],
        )
        self.image_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            img_row,
            text="Browse...",
            width=95,
            height=36,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=self._browse_image,
        ).grid(row=0, column=1)

    def _add_entry(self, start_row: int, label: str, placeholder: str, c: dict, f: dict):
        ctk.CTkLabel(
            self.form_scroll, text=label, font=f["body"], text_color=c["text_main"]
        ).grid(row=start_row, column=0, sticky="w", padx=14, pady=(4, 2))

        entry = ctk.CTkEntry(
            self.form_scroll,
            placeholder_text=placeholder,
            height=36,
            font=f["body"],
            fg_color=c["bg_input"],
            border_color=c["border"],
            text_color=c["text_main"],
        )
        entry.grid(row=start_row + 1, column=0, sticky="ew", padx=14, pady=(0, 10))
        return entry

    def _build_footer(self, c: dict, f: dict) -> None:
        footer = ctk.CTkFrame(
            self, fg_color=c["bg_card"], corner_radius=12, border_width=1, border_color=c["border"]
        )
        footer.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            footer,
            text="Cancel",
            height=38,
            font=f["button"],
            fg_color=c["border"],
            hover_color=c["text_muted"],
            text_color=c["text_main"],
            command=self.destroy,
        ).grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=10)

        ctk.CTkButton(
            footer,
            text="Save Menu Item",
            height=38,
            font=f["button"],
            fg_color=c["accent_gold"],
            hover_color=c["gold_hover"],
            text_color=c["text_on_gold"],
            command=self._save_item,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 12), pady=10)

    def _on_mousewheel(self, event) -> None:
        if self.form_scroll.winfo_exists():
            self.form_scroll._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _browse_image(self) -> None:
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select Menu Item Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp")],
        )
        if file_path:
            self._selected_source_path = file_path
            self.image_entry.delete(0, "end")
            self.image_entry.insert(0, os.path.basename(file_path))

    def _save_item(self) -> None:
        sku_val = self.sku_entry.get().strip().upper()
        name_val = self.name_entry.get().strip()
        price_val = self.price_entry.get().strip()
        category_val = self.category_combo.get().strip()

        if not sku_val or not name_val or not price_val or not category_val:
            messagebox.showwarning(
                "Missing Fields", "Please fill in SKU, Item Name, Price, and Category.", parent=self
            )
            return

        try:
            numeric_price = float(price_val)
            if numeric_price < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Price", "Please enter a valid non-negative number for the price.", parent=self
            )
            return

        if self.controller.db.sku_exists(sku_val):
            confirm = messagebox.askyesno(
                "SKU Already Exists",
                f"SKU '{sku_val}' already exists in the menu.\nDo you want to overwrite it with these new details?",
                parent=self,
            )
            if not confirm:
                return

        relative_image_path = ""
        if self._selected_source_path:
            try:
                assets_dir = get_assets_dir()
                os.makedirs(assets_dir, exist_ok=True)
                filename = os.path.basename(self._selected_source_path)
                dest_path = os.path.join(assets_dir, filename)
                if os.path.abspath(self._selected_source_path) != os.path.abspath(dest_path):
                    shutil.copy2(self._selected_source_path, dest_path)
                relative_image_path = f"assets/{filename}"
            except Exception as e:
                messagebox.showerror("Image Error", f"Could not copy image to assets folder:\n{e}", parent=self)
                return

        success, msg = self.controller.db.add_inventory_item(
            sku=sku_val,
            name=name_val,
            price=numeric_price,
            category=category_val,
            image_path=relative_image_path,
        )
        if success:
            if callable(self.on_saved):
                self.on_saved()
            messagebox.showinfo("Item Saved", msg, parent=self)
            self.destroy()
        else:
            messagebox.showerror("Save Failed", msg, parent=self)