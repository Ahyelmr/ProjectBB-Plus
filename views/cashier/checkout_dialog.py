import customtkinter as ctk


class CheckoutDialog(ctk.CTkToplevel):
    """Two-stage checkout modal: (1) Calculate Change -> (2) Confirm & Send to Kitchen."""

    _IGNORED_KEY_SYMS = {
        "Return",
        "KP_Enter",
        "Tab",
        "Escape",
        "Shift_L",
        "Shift_R",
        "Control_L",
        "Control_R",
        "Alt_L",
        "Alt_R",
    }

    def __init__(
        self,
        parent,
        controller,
        cart_items: dict,
        subtotal: float,
        discount_name: str,
        discount_amount: float,
        total_amount: float,
        on_confirm,
    ):
        super().__init__(parent)
        self.withdraw()

        self.controller = controller
        self.cart_items = {sku: dict(data) for sku, data in cart_items.items()}
        self.subtotal = round(float(subtotal), 2)
        self.discount_name = discount_name or "None"
        self.discount_amount = round(float(discount_amount), 2)
        self.total_amount = round(float(total_amount), 2)
        self.on_confirm = on_confirm

        self._stage = "CALCULATE"  # "CALCULATE" -> "CONFIRM"
        self._tendered_amount: float | None = None
        self._change_amount: float = 0.0
        self._submitting = False

        c = controller.colors
        f = controller.fonts

        self.title("Order Checkout & Payment")
        self.configure(fg_color=c["bg_main"])
        self.transient(parent.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        root = parent.winfo_toplevel()
        if root.winfo_width() <= 1 or root.winfo_height() <= 1:
            root.update_idletasks()
        win_w = 480
        win_h = min(620, max(480, root.winfo_height() - 50))
        x = root.winfo_x() + (root.winfo_width() - win_w) // 2
        y = root.winfo_y() + (root.winfo_height() - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{max(0, x)}+{max(0, y)}")
        self.minsize(430, 460)
        self.resizable(True, True)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._build_summary_section(c, f)
        self._build_payment_section(c, f)
        self._build_footer(c, f)

        self.bind("<Escape>", lambda _e: self._cancel())

        if self.total_amount == 0.0:
            self.amount_entry.insert(0, "0.00")

        self.deiconify()
        self.lift()
        self.grab_set()
        self.amount_entry.focus_set()
        self.amount_entry.select_range(0, "end")

    # =========================================================================
    # UI CONSTRUCTION
    # =========================================================================
    def _build_summary_section(self, c: dict, f: dict) -> None:
        summary_card = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        summary_card.grid(row=0, column=0, sticky="nsew", padx=14, pady=(14, 8))
        summary_card.grid_rowconfigure(1, weight=1)
        summary_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            summary_card,
            text="Order Summary",
            font=f["header"],
            text_color=c["accent_gold"],
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))

        self.items_scroll = ctk.CTkScrollableFrame(
            summary_card,
            fg_color=c["bg_input"],
            corner_radius=8,
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text_muted"],
        )
        self.items_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.items_scroll.grid_columnconfigure(0, weight=1)
        self.bind("<MouseWheel>", self._on_mousewheel)

        for idx, data in enumerate(self.cart_items.values()):
            line_total = data["price"] * data["qty"]
            row_frame = ctk.CTkFrame(self.items_scroll, fg_color="transparent")
            row_frame.grid(row=idx, column=0, sticky="ew", padx=6, pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row_frame,
                text=f"{data['qty']}x {data['name']}",
                font=f["body"],
                text_color=c["text_main"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(
                row_frame,
                text=f"₱{line_total:.2f}",
                font=f["body"],
                text_color=c["text_muted"],
                anchor="e",
            ).grid(row=0, column=1, sticky="e", padx=(8, 0))

        totals_frame = ctk.CTkFrame(summary_card, fg_color="transparent")
        totals_frame.grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 12))
        totals_frame.grid_columnconfigure(1, weight=1)

        # Subtotal row
        ctk.CTkLabel(
            totals_frame, text="Subtotal:", font=f["body"], text_color=c["text_muted"]
        ).grid(row=0, column=0, sticky="w", pady=1)
        ctk.CTkLabel(
            totals_frame, text=f"₱{self.subtotal:.2f}", font=f["body"], text_color=c["text_main"]
        ).grid(row=0, column=1, sticky="e", pady=1)

        # Discount row
        disc_label_text = (
            f"Discount ({self.discount_name}):"
            if self.discount_name != "None" and self.discount_amount > 0
            else "Discount:"
        )
        ctk.CTkLabel(
            totals_frame, text=disc_label_text, font=f["body"], text_color=c["text_red"]
        ).grid(row=1, column=0, sticky="w", pady=1)
        ctk.CTkLabel(
            totals_frame,
            text=f"-₱{self.discount_amount:.2f}",
            font=f["body"],
            text_color=c["text_red"],
        ).grid(row=1, column=1, sticky="e", pady=1)

        # Divider
        ctk.CTkFrame(totals_frame, height=1, fg_color=c["border"]).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=6
        )

        # Grand Total row
        ctk.CTkLabel(
            totals_frame, text="Total Due:", font=f["header"], text_color=c["text_main"]
        ).grid(row=3, column=0, sticky="w")
        ctk.CTkLabel(
            totals_frame,
            text=f"₱{self.total_amount:.2f}",
            font=f["header"],
            text_color=c["text_green"],
        ).grid(row=3, column=1, sticky="e")

    def _build_payment_section(self, c: dict, f: dict) -> None:
        payment_card = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        payment_card.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        payment_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            payment_card,
            text="Amount Paid (₱)",
            font=f["subheader"],
            text_color=c["text_main"],
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 4))

        input_row = ctk.CTkFrame(payment_card, fg_color="transparent")
        input_row.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        input_row.grid_columnconfigure(0, weight=1)

        self.amount_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Enter cash received...",
            height=40,
            font=f["header"],
            fg_color=c["bg_input"],
            border_color=c["border"],
            text_color=c["text_main"],
            justify="right",
        )
        self.amount_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.amount_entry.bind("<Return>", lambda _e: self._on_action_click())
        self.amount_entry.bind("<KP_Enter>", lambda _e: self._on_action_click())
        self.amount_entry.bind("<KeyRelease>", self._on_amount_edited)

        self.exact_btn = ctk.CTkButton(
            input_row,
            text="Exact",
            width=72,
            height=40,
            font=f["button"],
            fg_color=c["bg_input"],
            hover_color=c["border"],
            border_width=1,
            border_color=c["border"],
            text_color=c["text_main"],
            command=self._fill_exact_amount,
        )
        self.exact_btn.grid(row=0, column=1)

        # Highlighted Change display box
        change_box = ctk.CTkFrame(
            payment_card,
            fg_color=c["bg_input"],
            corner_radius=8,
            border_width=1,
            border_color=c["border"],
        )
        change_box.grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 6))
        change_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            change_box,
            text="Change:",
            font=f["header"],
            text_color=c["text_main"],
        ).grid(row=0, column=0, sticky="w", padx=12, pady=8)

        self.change_value_label = ctk.CTkLabel(
            change_box,
            text="₱0.00",
            font=f["header"],
            text_color=c["text_muted"],
        )
        self.change_value_label.grid(row=0, column=1, sticky="e", padx=12, pady=8)

        self.status_label = ctk.CTkLabel(
            payment_card,
            text="Enter amount paid and click 'Calculate Change'.",
            font=f["small"],
            text_color=c["text_muted"],
            anchor="w",
        )
        self.status_label.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))

    def _build_footer(self, c: dict, f: dict) -> None:
        footer = ctk.CTkFrame(
            self,
            fg_color=c["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=c["border"],
        )
        footer.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=2)

        self.cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            height=42,
            font=f["button"],
            fg_color=c["border"],
            hover_color=c["text_muted"],
            text_color=c["text_main"],
            command=self._cancel,
        )
        self.cancel_btn.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=10)

        self.action_btn = ctk.CTkButton(
            footer,
            text="Calculate Change",
            height=42,
            font=f["button"],
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            text_color="#FFFFFF",
            command=self._on_action_click,
        )
        self.action_btn.grid(row=0, column=1, sticky="ew", padx=(6, 12), pady=10)

    # =========================================================================
    # INTERACTION & TWO-STAGE STATE MACHINE
    # =========================================================================
    def _on_mousewheel(self, event):
        if not self.items_scroll.winfo_exists() or event.delta == 0:
            return None
        canvas = self.items_scroll._parent_canvas
        if canvas.yview() == (0.0, 1.0):
            return "break"
        step = int(-1 * (event.delta / 120))
        if step == 0:
            step = -1 if event.delta > 0 else 1
        canvas.yview_scroll(step, "units")
        return "break"

    def _fill_exact_amount(self) -> None:
        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, f"{self.total_amount:.2f}")
        self._reset_to_calculate_stage("Exact amount entered. Click 'Calculate Change'.")
        self.amount_entry.focus_set()

    def _on_amount_edited(self, event) -> None:
        if getattr(event, "keysym", "") in self._IGNORED_KEY_SYMS:
            return
        if self._stage == "CONFIRM":
            self._reset_to_calculate_stage("Amount edited. Click 'Calculate Change' to recalculate.")

    def _reset_to_calculate_stage(self, message: str) -> None:
        c = self.controller.colors
        self._stage = "CALCULATE"
        self._tendered_amount = None
        self._change_amount = 0.0
        self.change_value_label.configure(text="₱0.00", text_color=c["text_muted"])
        self.status_label.configure(text=message, text_color=c["accent_gold"])
        self.action_btn.configure(
            text="Calculate Change",
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
        )

    def _on_action_click(self) -> None:
        if self._submitting:
            return

        c = self.controller.colors

        # STAGE 1: Validate payment and display change
        if self._stage == "CALCULATE":
            raw = self.amount_entry.get().strip().replace("₱", "").replace(",", "")
            if not raw:
                self.status_label.configure(
                    text="Please enter the amount paid first.", text_color=c["text_red"]
                )
                self.amount_entry.focus_set()
                return

            try:
                tendered = round(float(raw), 2)
                if tendered < 0:
                    raise ValueError
            except ValueError:
                self.status_label.configure(
                    text="Invalid amount. Enter a valid number (e.g., 200 or 150.50).",
                    text_color=c["text_red"],
                )
                self.amount_entry.focus_set()
                self.amount_entry.select_range(0, "end")
                return

            if tendered + 1e-9 < self.total_amount:
                shortage = round(self.total_amount - tendered, 2)
                self.change_value_label.configure(text="₱0.00", text_color=c["text_red"])
                self.status_label.configure(
                    text=f"Insufficient payment — short by ₱{shortage:.2f}.",
                    text_color=c["text_red"],
                )
                self.amount_entry.focus_set()
                self.amount_entry.select_range(0, "end")
                return

            self._tendered_amount = tendered
            self._change_amount = round(max(0.0, tendered - self.total_amount), 2)
            self._stage = "CONFIRM"

            self.change_value_label.configure(
                text=f"₱{self._change_amount:.2f}", text_color=c["text_green"]
            )
            self.status_label.configure(
                text="Change calculated. Press 'Confirm & Send to Kitchen' to complete.",
                text_color=c["text_green"],
            )
            self.action_btn.configure(
                text="Confirm & Send to Kitchen",
                fg_color=c["accent_green"],
                hover_color=c["green_hover"],
            )
            return

        # STAGE 2: Commit transaction and send to Live Kitchen Queue
        if self._stage == "CONFIRM" and self._tendered_amount is not None:
            self._submitting = True
            self.action_btn.configure(state="disabled")
            self.cancel_btn.configure(state="disabled")
            try:
                if callable(self.on_confirm):
                    self.on_confirm(self._tendered_amount, self._change_amount)
                self.destroy()
            finally:
                self._submitting = False
                if self.winfo_exists():
                    if self.action_btn.winfo_exists():
                        self.action_btn.configure(state="normal")
                    if self.cancel_btn.winfo_exists():
                        self.cancel_btn.configure(state="normal")

    def _cancel(self) -> None:
        if not self._submitting:
            self.destroy()