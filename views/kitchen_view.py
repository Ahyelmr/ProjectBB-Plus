import customtkinter as ctk

class KitchenFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        # Inherit the main background color from the centralized theme
        super().__init__(parent, fg_color=controller.colors["bg_main"])
        self.controller = controller
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Top Navigation & Controls
        self.top_bar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        self.back_btn = ctk.CTkButton(
            self.top_bar, 
            text="Back to Cashier", 
            width=140, 
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=lambda: controller.show_frame("CashierFrame")
        )
        self.back_btn.pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            self.top_bar, 
            text="Kitchen Display System (KDS)", 
            font=self.controller.fonts["title"],
            text_color=self.controller.colors["text_main"]
        ).pack(side="left", expand=True)
        
        self.refresh_btn = ctk.CTkButton(
            self.top_bar, 
            text="Refresh Queue", 
            width=120, 
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"],
            hover_color=self.controller.colors["primary_hover"],
            command=self.load_orders
        )
        self.refresh_btn.pack(side="right", padx=10, pady=10)
        
        # Order Queue Columns
        self.prep_column = ctk.CTkScrollableFrame(
            self, 
            label_text="Preparing", 
            label_font=self.controller.fonts["header"],
            label_text_color=self.controller.colors["text_main"],
            fg_color=self.controller.colors["bg_card"]
        )
        self.prep_column.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.ready_column = ctk.CTkScrollableFrame(
            self, 
            label_text="Ready to Claim", 
            label_font=self.controller.fonts["header"],
            label_text_color=self.controller.colors["text_main"],
            fg_color=self.controller.colors["bg_card"]
        )
        self.ready_column.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.load_orders()

    def load_orders(self):
        """Clears and reloads active kitchen tickets from the database."""
        for widget in self.prep_column.winfo_children():
            widget.destroy()
        for widget in self.ready_column.winfo_children():
            widget.destroy()
            
        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT order_id, sequence_number, status FROM orders WHERE status IN ('PENDING', 'READY')")
            orders = cursor.fetchall()
            
            for order in orders:
                order_id = order['order_id']
                seq_num = order['sequence_number']
                status = order['status']
                
                cursor.execute("""
                    SELECT inventory.name, order_items.quantity 
                    FROM order_items 
                    JOIN inventory ON order_items.sku = inventory.sku 
                    WHERE order_items.order_id = ?
                """, (order_id,))
                items = cursor.fetchall()
                
                item_text = "\n".join([f"{item['quantity']}x {item['name']}" for item in items])
                
                if status == 'PENDING':
                    self.create_prep_card(order_id, seq_num, item_text)
                elif status == 'READY':
                    self.create_ready_card(order_id, seq_num, item_text)

    def create_prep_card(self, order_id, seq_num, item_text):
        card = ctk.CTkFrame(
            self.prep_column, 
            border_width=2, 
            border_color=self.controller.colors["border"],
            corner_radius=10,
            fg_color=self.controller.colors["bg_main"]
        )
        card.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            card, 
            text=f"Order #{seq_num}", 
            font=self.controller.fonts["subheader"],
            text_color=self.controller.colors["text_main"]
        ).pack(pady=(5, 0))
        
        ctk.CTkLabel(
            card, 
            text=item_text, 
            justify="left", 
            font=self.controller.fonts["body"],
            text_color=self.controller.colors["text_muted"]
        ).pack(pady=5)
        
        action_btn = ctk.CTkButton(
            card, 
            text="Move to Ready", 
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["accent_gold"], 
            hover_color=self.controller.colors["gold_hover"],
            command=lambda: [
                self.controller.queue.mark_order_ready(order_id, seq_num), 
                self.load_orders(),
                self.controller.frames["CashierFrame"].load_kitchen_orders()
            ]
        )
        action_btn.pack(pady=10)

    def create_ready_card(self, order_id, seq_num, item_text):
        card = ctk.CTkFrame(
            self.ready_column, 
            border_width=2, 
            border_color=self.controller.colors["border"],
            corner_radius=10, 
            fg_color=self.controller.colors["bg_main"]
        )
        card.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            card, 
            text=f"Order #{seq_num}", 
            font=self.controller.fonts["subheader"], 
            text_color=self.controller.colors["accent_green"]
        ).pack(pady=(5, 0))
        
        ctk.CTkLabel(
            card, 
            text=item_text, 
            justify="left", 
            font=self.controller.fonts["body"],
            text_color=self.controller.colors["text_muted"]
        ).pack(pady=5)
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        announce_btn = ctk.CTkButton(
            btn_frame, 
            text="Call (TTS)", 
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["primary"], 
            hover_color=self.controller.colors["primary_hover"],
            width=100,
            command=lambda: self.controller.queue._play_announcement(seq_num)
        )
        announce_btn.pack(side="left", padx=5)
        
        complete_btn = ctk.CTkButton(
            btn_frame, 
            text="Done", 
            font=self.controller.fonts["button"],
            fg_color=self.controller.colors["accent_green"], 
            hover_color=self.controller.colors["green_hover"], 
            width=100,
            command=lambda: [
                self.controller.queue.complete_order(order_id), 
                self.load_orders(),
                self.controller.frames["CashierFrame"].load_kitchen_orders()
            ]
        )
        complete_btn.pack(side="right", padx=5)