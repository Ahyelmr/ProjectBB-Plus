import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import os
from utils import get_resource_path

class CashierFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.cart = {}
        
        # 3-Column Layout: Menu (weight 2) | Cart & Checkout (weight 1) | Kitchen Queue (weight 2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=2)
        
        # --- Column 0: Menu Items ---
        self.menu_frame = ctk.CTkScrollableFrame(self, label_text="Menu Items")
        self.menu_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # --- Column 1: Cart & Cashier Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self)
        self.sidebar_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        self.sidebar_frame.grid_rowconfigure(1, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.sidebar_frame, text="Current Order", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=10)
        self.cart_display = ctk.CTkScrollableFrame(self.sidebar_frame, width=220)
        self.cart_display.grid(row=1, column=0, sticky="nsew", padx=10)
        
        self.total_label = ctk.CTkLabel(self.sidebar_frame, text="Total: ₱0.00", font=("Arial", 16, "bold"))
        self.total_label.grid(row=2, column=0, pady=10)
        
        self.checkout_btn = ctk.CTkButton(self.sidebar_frame, text="Checkout", fg_color="green", hover_color="darkgreen", command=self.process_checkout)
        self.checkout_btn.grid(row=3, column=0, pady=5, padx=15, sticky="ew")
        
        self.progress_btn = ctk.CTkButton(self.sidebar_frame, text="Daily Progress & Export", fg_color="#b8860b", hover_color="#8b6508", command=lambda: [self.controller.frames["ProgressFrame"].load_daily_data(), controller.show_frame("ProgressFrame")])
        self.logout_btn = ctk.CTkButton(self.sidebar_frame, text="Logout", fg_color="red", hover_color="darkred", command=lambda: controller.show_frame("LoginFrame"))
        
        # --- Column 2: Kitchen Live Queue ---
        self.kitchen_panel = ctk.CTkFrame(self)
        self.kitchen_panel.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
        self.kitchen_panel.grid_rowconfigure(1, weight=1)
        self.kitchen_panel.grid_columnconfigure(0, weight=1)
        self.kitchen_panel.grid_columnconfigure(1, weight=1)
        
        # Header bar for Kitchen Queue
        self.k_header = ctk.CTkFrame(self.kitchen_panel, fg_color="transparent")
        self.k_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(self.k_header, text="Kitchen Live Queue", font=("Arial", 18, "bold")).pack(side="left")
        ctk.CTkButton(self.k_header, text="Refresh", width=70, command=self.load_kitchen_orders).pack(side="right")
        
        # Sub-columns for Preparing and Ready orders
        self.prep_column = ctk.CTkScrollableFrame(self.kitchen_panel, label_text="Preparing", label_font=("Arial", 14, "bold"))
        self.prep_column.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.ready_column = ctk.CTkScrollableFrame(self.kitchen_panel, label_text="Ready for Pickup", label_font=("Arial", 14, "bold"))
        self.ready_column.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Load initial operational data
        self.load_menu()
        self.load_kitchen_orders()

    def update_admin_features(self):
        """Toggles Admin dashboard access controls dynamically upon login."""
        if self.controller.current_user_role == "Admin":
            self.progress_btn.grid(row=4, column=0, pady=5, padx=15, sticky="ew")
            self.logout_btn.grid(row=5, column=0, pady=(0, 15), padx=15, sticky="ew")
        else:
            self.progress_btn.grid_forget()
            self.logout_btn.grid(row=4, column=0, pady=(0, 15), padx=15, sticky="ew")

    def load_menu(self):
        """Loads inventory items with 3-tier image fallback strategy."""
        for widget in self.menu_frame.winfo_children():
            widget.destroy()

        with self.controller.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sku, name, price, stock_qty, image_path FROM inventory WHERE stock_qty > 0")
            items = cursor.fetchall()
            
        default_img_path = get_resource_path("assets/default.png")
            
        row_idx, col_idx = 0, 0
        for item in items:
            btn_text = f"{item['name']}\n₱{item['price']:.2f}\nStock: {item['stock_qty']}"
            btn_image = None
            
            # Step 1: Item image from DB path
            img_path = get_resource_path(item['image_path']) if item['image_path'] else ""
            if img_path and os.path.exists(img_path):
                try:
                    pil_img = Image.open(img_path)
                    btn_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))
                except Exception as e:
                    print(f"Failed to load image for {item['name']}: {e}")

            # Step 2: File fallback to assets/default.png
            if btn_image is None and os.path.exists(default_img_path):
                try:
                    pil_img = Image.open(default_img_path)
                    btn_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))
                except Exception as e:
                    print(f"Failed to load default asset image: {e}")

            # Step 3: Dynamic in-memory gray placeholder
            if btn_image is None:
                try:
                    placeholder_pil = Image.new('RGB', (60, 60), color=(50, 54, 62))
                    btn_image = ctk.CTkImage(light_image=placeholder_pil, dark_image=placeholder_pil, size=(60, 60))
                except Exception as e:
                    print(f"Failed to create dynamic placeholder image: {e}")

            btn = ctk.CTkButton(
                self.menu_frame, 
                text=btn_text, 
                image=btn_image, 
                compound="top", 
                width=110, 
                height=100, 
                command=lambda i=item: self.add_to_cart(i)
            )
            btn.grid(row=row_idx, column=col_idx, padx=5, pady=5)
            
            col_idx += 1
            if col_idx > 2:
                col_idx = 0
                row_idx += 1

    def add_to_cart(self, item):
        sku = item['sku']
        if sku in self.cart:
            if self.cart[sku]['qty'] < item['stock_qty']:
                self.cart[sku]['qty'] += 1
            else:
                messagebox.showwarning("Stock Limit", "Cannot add more of this item.")
        else:
            self.cart[sku] = {'name': item['name'], 'price': item['price'], 'qty': 1}
        self.update_cart_display()

    def update_cart_display(self):
        for widget in self.cart_display.winfo_children():
            widget.destroy()
        total = 0
        for r_idx, (sku, data) in enumerate(self.cart.items()):
            item_total = data['price'] * data['qty']
            total += item_total
            ctk.CTkLabel(self.cart_display, text=f"{data['qty']}x {data['name']} - ₱{item_total:.2f}", font=("Arial", 12)).grid(row=r_idx, column=0, sticky="w", pady=2)
        self.total_label.configure(text=f"Total: ₱{total:.2f}")

    def process_checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Cannot checkout an empty order.")
            return
            
        cart_list = [{"sku": k, "quantity": v["qty"], "price": v["price"], "name": v["name"]} for k, v in self.cart.items()]
        total_amount = sum(v["price"] * v["qty"] for v in self.cart.values())
        
        try:
            order_id, seq_num = self.controller.queue.process_new_transaction(cart_list, total_amount)
            messagebox.showinfo("Success", f"Order #{seq_num} completed successfully!")
            self.cart.clear()
            self.update_cart_display()
            self.load_menu()
            # Instantly reflect newly checked-out transaction in the live kitchen panel
            self.load_kitchen_orders()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to process order: {str(e)}")

    # --- Live Kitchen Queue Management ---
    def load_kitchen_orders(self):
        """Fetches active orders and populates the kitchen queue columns."""
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
        card = ctk.CTkFrame(self.prep_column, border_width=1, corner_radius=8)
        card.pack(fill="x", padx=3, pady=4)
        
        ctk.CTkLabel(card, text=f"Order #{seq_num}", font=("Arial", 14, "bold")).pack(pady=(4, 0))
        ctk.CTkLabel(card, text=item_text, justify="left", font=("Arial", 11)).pack(pady=3)
        
        action_btn = ctk.CTkButton(
            card, 
            text="Move to Ready", 
            fg_color="orange", 
            hover_color="darkorange", 
            height=24, 
            font=("Arial", 11),
            command=lambda: [self.controller.queue.mark_order_ready(order_id, seq_num), self.load_kitchen_orders()]
        )
        action_btn.pack(pady=6)

    def create_ready_card(self, order_id, seq_num, item_text):
        card = ctk.CTkFrame(self.ready_column, border_width=1, corner_radius=8, fg_color="#2b2b2b")
        card.pack(fill="x", padx=3, pady=4)
        
        ctk.CTkLabel(card, text=f"Order #{seq_num}", font=("Arial", 14, "bold"), text_color="cyan").pack(pady=(4, 0))
        ctk.CTkLabel(card, text=item_text, justify="left", font=("Arial", 11)).pack(pady=3)
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=6)
        
        announce_btn = ctk.CTkButton(
            btn_frame, 
            text="Call", 
            fg_color="blue", 
            width=50, 
            height=24, 
            font=("Arial", 11),
            command=lambda: self.controller.queue._play_announcement(seq_num)
        )
        announce_btn.pack(side="left", padx=2)
        
        complete_btn = ctk.CTkButton(
            btn_frame, 
            text="Done", 
            fg_color="green", 
            hover_color="darkgreen", 
            width=50, 
            height=24, 
            font=("Arial", 11),
            command=lambda: [self.controller.queue.complete_order(order_id), self.load_kitchen_orders()]
        )
        complete_btn.pack(side="right", padx=2)