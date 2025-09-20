import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import sqlite3
import hashlib
import json
import os
import re
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bakery.db')
        self.create_tables()
        self.insert_sample_data()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Cakes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                flavor TEXT NOT NULL,
                size TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                image_path TEXT,
                description TEXT,
                category TEXT DEFAULT 'regular'
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                customer_name TEXT NOT NULL,
                cake_id INTEGER,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                status TEXT NOT NULL,
                order_date TEXT NOT NULL,
                delivery_date TEXT,
                special_instructions TEXT,
                delivery_type TEXT DEFAULT 'pickup',
                address TEXT,
                phone TEXT,
                email TEXT,
                FOREIGN KEY (customer_id) REFERENCES users (id),
                FOREIGN KEY (cake_id) REFERENCES cakes (id)
            )
        ''')
        
        # Order status history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                status TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        # Inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                min_stock_level REAL NOT NULL,
                last_updated TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
    
    def insert_sample_data(self):
        cursor = self.conn.cursor()
        
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Insert sample users
            users = [
                ('admin', self.hash_password('admin'), 'admin', 'Admin User', 'admin@bakery.com', '123-456-7890'),
                ('staff1', self.hash_password('staff1'), 'staff', 'John Baker', 'john@bakery.com', '123-456-7891'),
                ('staff2', self.hash_password('staff2'), 'staff', 'Sarah Chef', 'sarah@bakery.com', '123-456-7892'),
                ('customer1', self.hash_password('customer1'), 'customer', 'Alice Johnson', 'alice@example.com', '123-456-7893'),
                ('customer2', self.hash_password('customer2'), 'customer', 'Bob Smith', 'bob@example.com', '123-456-7894')
            ]
            
            cursor.executemany(
                "INSERT INTO users (username, password, role, name, email, phone) VALUES (?, ?, ?, ?, ?, ?)",
                users
            )
            
            # Insert sample cakes
            cakes = [
                ('Chocolate Birthday Cake', 'chocolate', 'medium', 35.00, 5, 'chocolate_cake.jpg', 'Delicious chocolate cake with buttercream frosting', 'birthday'),
                ('Vanilla Wedding Cake', 'vanilla', 'large', 120.00, 2, 'vanilla_cake.jpg', 'Elegant vanilla wedding cake with fondant', 'wedding'),
                ('Strawberry Anniversary Cake', 'strawberry', 'medium', 65.00, 3, 'strawberry_cake.jpg', 'Fresh strawberry cake with cream filling', 'anniversary'),
                ('Red Velvet Celebration', 'red-velvet', 'large', 85.00, 4, 'red_velvet_cake.jpg', 'Classic red velvet cake with cream cheese frosting', 'celebration'),
                ('Carrot Cake', 'carrot', 'small', 25.00, 8, 'carrot_cake.jpg', 'Moist carrot cake with walnuts and cream cheese frosting', 'regular'),
                ('Lemon Drizzle Cake', 'lemon', 'small', 20.00, 10, 'lemon_cake.jpg', 'Tangy lemon cake with lemon glaze', 'regular')
            ]
            
            cursor.executemany(
                "INSERT INTO cakes (name, flavor, size, price, stock, image_path, description, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                cakes
            )
            
            # Insert sample inventory
            inventory = [
                ('Flour', 'baking', 100.0, 'lbs', 20.0, datetime.datetime.now().isoformat()),
                ('Sugar', 'baking', 50.0, 'lbs', 10.0, datetime.datetime.now().isoformat()),
                ('Butter', 'dairy', 30.0, 'lbs', 5.0, datetime.datetime.now().isoformat()),
                ('Eggs', 'dairy', 200.0, 'pieces', 50.0, datetime.datetime.now().isoformat()),
                ('Chocolate', 'baking', 15.0, 'lbs', 8.0, datetime.datetime.now().isoformat()),
                ('Vanilla Extract', 'flavoring', 5.0, 'liters', 1.0, datetime.datetime.now().isoformat())
            ]
            
            cursor.executemany(
                "INSERT INTO inventory (item_name, category, quantity, unit, min_stock_level, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
                inventory
            )
            
            self.conn.commit()
    
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_user(self, username: str, password: str, role: str) -> Optional[tuple]:
        cursor = self.conn.cursor()
        hashed_password = self.hash_password(password)
        cursor.execute(
            "SELECT id, name, email FROM users WHERE username = ? AND password = ? AND role = ? AND status = 'active'",
            (username, hashed_password, role)
        )
        return cursor.fetchone()
    
    def get_cakes(self, category: Optional[str] = None, search_term: Optional[str] = None) -> List[tuple]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM cakes WHERE stock > 0"
        params = []
        
        if category and category != "all":
            query += " AND category = ?"
            params.append(category)
        
        if search_term:
            query += " AND (name LIKE ? OR flavor LIKE ? OR description LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def get_cake_by_id(self, cake_id: int) -> Optional[tuple]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cakes WHERE id = ?", (cake_id,))
        return cursor.fetchone()
    
    def update_cake_stock(self, cake_id: int, quantity: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE cakes SET stock = stock - ? WHERE id = ?", (quantity, cake_id))
        self.conn.commit()
    
    def create_order(self, customer_id: Optional[int], customer_name: str, cake_id: int, 
                    quantity: int, total_price: float, status: str, special_instructions: str,
                    delivery_type: str, delivery_date: str, address: str, phone: str, email: str) -> int:
        cursor = self.conn.cursor()
        order_date = datetime.datetime.now().isoformat()
        
        cursor.execute(
            """INSERT INTO orders 
            (customer_id, customer_name, cake_id, quantity, total_price, status, order_date, 
            special_instructions, delivery_type, delivery_date, address, phone, email) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (customer_id, customer_name, cake_id, quantity, total_price, status, order_date,
             special_instructions, delivery_type, delivery_date, address, phone, email)
        )
        
        order_id = cursor.lastrowid
        
        # Add initial status to history
        cursor.execute(
            "INSERT INTO order_status_history (order_id, status, changed_at) VALUES (?, ?, ?)",
            (order_id, status, order_date)
        )
        
        self.conn.commit()
        return order_id
    
    def get_orders(self, user_id: Optional[int] = None, user_role: Optional[str] = None, 
                  status: Optional[str] = None) -> List[tuple]:
        cursor = self.conn.cursor()
        
        if user_role == "customer" and user_id:
            query = "SELECT * FROM orders WHERE customer_id = ?"
            params = [user_id]
        else:
            query = "SELECT * FROM orders"
            params = []
        
        if status and status != "all":
            query += " AND status = ?" if "WHERE" in query else " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY order_date DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def update_order_status(self, order_id: int, new_status: str, notes: Optional[str] = None) -> None:
        cursor = self.conn.cursor()
        changed_at = datetime.datetime.now().isoformat()
        
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        
        cursor.execute(
            "INSERT INTO order_status_history (order_id, status, changed_at, notes) VALUES (?, ?, ?, ?)",
            (order_id, new_status, changed_at, notes)
        )
        
        self.conn.commit()
    
    def get_inventory(self) -> List[tuple]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM inventory ORDER BY category, item_name")
        return cursor.fetchall()
    
    def update_inventory(self, item_id: int, quantity: float) -> None:
        cursor = self.conn.cursor()
        last_updated = datetime.datetime.now().isoformat()
        cursor.execute(
            "UPDATE inventory SET quantity = ?, last_updated = ? WHERE id = ?",
            (quantity, last_updated, item_id)
        )
        self.conn.commit()
    
    def add_inventory_item(self, item_name: str, category: str, quantity: float, 
                          unit: str, min_stock_level: float) -> None:
        cursor = self.conn.cursor()
        last_updated = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO inventory (item_name, category, quantity, unit, min_stock_level, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
            (item_name, category, quantity, unit, min_stock_level, last_updated)
        )
        self.conn.commit()
    
    def get_low_stock_items(self) -> List[tuple]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM inventory WHERE quantity <= min_stock_level")
        return cursor.fetchall()
    
    def add_cake(self, name: str, flavor: str, size: str, price: float, stock: int, 
                description: str, category: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO cakes (name, flavor, size, price, stock, description, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, flavor, size, price, stock, description, category)
        )
        self.conn.commit()
    
    def delete_cake(self, cake_id: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM cakes WHERE id = ?", (cake_id,))
        self.conn.commit()
    
    def add_user(self, username: str, password: str, role: str, name: str, email: str, phone: str = "") -> None:
        cursor = self.conn.cursor()
        hashed_password = self.hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password, role, name, email, phone) VALUES (?, ?, ?, ?, ?, ?)",
            (username, hashed_password, role, name, email, phone)
        )
        self.conn.commit()
    
    def get_users_by_role(self, role: str) -> List[tuple]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = ? ORDER BY name", (role,))
        return cursor.fetchall()

class SweetDreamsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sweet Dreams Cake Ordering System")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f8ff")
        
        # Initialize database
        self.db = Database()
        
        # Current user state
        self.current_user = None
        self.current_user_id = None
        self.current_role = None
        self.current_user_name = None
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure custom styles
        self.style.configure('Title.TLabel', font=('Arial', 24, 'bold'), foreground='#ff69b4')
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'), foreground='#333333')
        self.style.configure('Info.TLabel', font=('Arial', 10), foreground='#666666')
        self.style.configure('Success.TButton', background='#4CAF50')
        self.style.configure('Warning.TButton', background='#ff9800')
        self.style.configure('Danger.TButton', background='#f44336')
        
        # Create main container
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self.create_header()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Create login tab
        self.login_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.login_frame, text="Login")
        
        # Create role-specific tabs (initially hidden)
        self.admin_frame = ttk.Frame(self.notebook)
        self.staff_frame = ttk.Frame(self.notebook)
        self.customer_frame = ttk.Frame(self.notebook)
        
        # Create login interface
        self.create_login_interface()
        
        # Show login tab by default
        self.notebook.select(self.login_frame)
    
    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(header_frame, text="🎂 Sweet Dreams Bakery", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # User info frame (initially hidden)
        self.user_info_frame = ttk.Frame(header_frame)
        self.user_info_frame.pack(side=tk.RIGHT)
        
        self.user_label = ttk.Label(self.user_info_frame, text="", style='Info.TLabel')
        self.user_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.logout_btn = ttk.Button(self.user_info_frame, text="Logout", command=self.logout)
        self.logout_btn.pack(side=tk.LEFT)
        
        # Hide user info initially
        self.user_info_frame.pack_forget()
    
    def create_login_interface(self):
        # Center the login form
        login_container = ttk.Frame(self.login_frame)
        login_container.pack(expand=True, fill=tk.BOTH)
        
        login_form = ttk.Frame(login_container)
        login_form.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        ttk.Label(login_form, text="System Login", style='Header.TLabel').pack(pady=(0, 30))
        
        # Username
        ttk.Label(login_form, text="Username:", font=('Arial', 12)).pack(anchor=tk.W)
        self.username_entry = ttk.Entry(login_form, font=('Arial', 12), width=25)
        self.username_entry.pack(pady=(5, 15))
        
        # Password
        ttk.Label(login_form, text="Password:", font=('Arial', 12)).pack(anchor=tk.W)
        self.password_entry = ttk.Entry(login_form, font=('Arial', 12), width=25, show="*")
        self.password_entry.pack(pady=(5, 15))
        
        # User Type
        ttk.Label(login_form, text="User Type:", font=('Arial', 12)).pack(anchor=tk.W)
        self.user_type_var = tk.StringVar(value="admin")
        user_type_combo = ttk.Combobox(login_form, textvariable=self.user_type_var,
                                      values=["admin", "staff", "customer"], 
                                      state="readonly", font=('Arial', 12), width=23)
        user_type_combo.pack(pady=(5, 20))
        
        # Login Button
        login_btn = ttk.Button(login_form, text="Login", command=self.login, style='Success.TButton')
        login_btn.pack(pady=(0, 20))
        
        # Register link
        register_frame = ttk.Frame(login_form)
        register_frame.pack()
        
        ttk.Label(register_frame, text="Don't have an account?", font=('Arial', 10)).pack(side=tk.LEFT)
        register_btn = ttk.Button(register_frame, text="Register here", command=self.show_register_modal)
        register_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Demo credentials
        demo_frame = ttk.LabelFrame(login_form, text="Demo Credentials", padding="10")
        demo_frame.pack(pady=(20, 0), fill=tk.X)
        
        demo_text = "Admin: admin / admin\nStaff: staff1 / staff1\nCustomer: customer1 / customer1"
        ttk.Label(demo_frame, text=demo_text, font=('Arial', 9), foreground='#666').pack()
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda event: self.login())
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user_type = self.user_type_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return
        
        user_data = self.db.validate_user(username, password, user_type)
        
        if user_data:
            self.current_user = username
            self.current_user_id = user_data[0]
            self.current_user_name = user_data[1]
            self.current_role = user_type
            
            # Show user info
            self.user_label.config(text=f"Welcome, {self.current_user_name} ({user_type})")
            self.user_info_frame.pack(side=tk.RIGHT)
            
            # Clear login form
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            
            # Create and show appropriate dashboard
            self.create_dashboard()
        else:
            messagebox.showerror("Error", "Invalid credentials. Please try again.")
    
    def logout(self):
        # Clear user state
        self.current_user = None
        self.current_user_id = None
        self.current_user_name = None
        self.current_role = None
        
        # Hide user info
        self.user_info_frame.pack_forget()
        
        # Remove role-specific tabs
        for tab_id in self.notebook.tabs():
            if tab_id != str(self.login_frame):
                self.notebook.forget(tab_id)
        
        # Show login tab
        self.notebook.select(self.login_frame)
    
    def create_dashboard(self):
        # Remove existing role-specific tabs
        for tab_id in self.notebook.tabs():
            if tab_id != str(self.login_frame):
                self.notebook.forget(tab_id)
        
        if self.current_role == "admin":
            self.create_admin_dashboard()
            self.notebook.add(self.admin_frame, text="Admin Dashboard")
            self.notebook.select(self.admin_frame)
        elif self.current_role == "staff":
            self.create_staff_dashboard()
            self.notebook.add(self.staff_frame, text="Staff Dashboard")
            self.notebook.select(self.staff_frame)
        elif self.current_role == "customer":
            self.create_customer_dashboard()
            self.notebook.add(self.customer_frame, text="Customer Portal")
            self.notebook.select(self.customer_frame)
    
    def create_admin_dashboard(self):
        # Clear existing widgets
        for widget in self.admin_frame.winfo_children():
            widget.destroy()
        
        # Create scrollable frame
        canvas = tk.Canvas(self.admin_frame, bg="#f0f8ff")
        scrollbar = ttk.Scrollbar(self.admin_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Dashboard content
        ttk.Label(scrollable_frame, text="Admin Dashboard", style='Header.TLabel').pack(pady=(0, 20))
        
        # Quick Stats
        stats_frame = ttk.LabelFrame(scrollable_frame, text="📊 Quick Stats", padding="15")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.update_admin_stats(stats_frame)
        
        # Create notebook for admin sections
        admin_notebook = ttk.Notebook(scrollable_frame)
        admin_notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Cake Management Tab
        cake_frame = ttk.Frame(admin_notebook)
        admin_notebook.add(cake_frame, text="🍰 Cakes")
        self.create_cake_management(cake_frame)
        
        # Order Management Tab
        order_frame = ttk.Frame(admin_notebook)
        admin_notebook.add(order_frame, text="📋 Orders")
        self.create_order_management(order_frame)
        
        # Staff Management Tab
        staff_frame = ttk.Frame(admin_notebook)
        admin_notebook.add(staff_frame, text="👥 Staff")
        self.create_staff_management(staff_frame)
        
        # Inventory Tab
        inventory_frame = ttk.Frame(admin_notebook)
        admin_notebook.add(inventory_frame, text="📦 Inventory")
        self.create_inventory_management(inventory_frame)
        
        # Reports Tab
        reports_frame = ttk.Frame(admin_notebook)
        admin_notebook.add(reports_frame, text="📈 Reports")
        self.create_reports_section(reports_frame)
    
    def create_staff_dashboard(self):
        # Clear existing widgets
        for widget in self.staff_frame.winfo_children():
            widget.destroy()
        
        # Create scrollable frame
        canvas = tk.Canvas(self.staff_frame, bg="#f0f8ff")
        scrollbar = ttk.Scrollbar(self.staff_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Dashboard content
        ttk.Label(scrollable_frame, text="Staff Dashboard", style='Header.TLabel').pack(pady=(0, 20))
        
        # Incoming Orders
        incoming_frame = ttk.LabelFrame(scrollable_frame, text="📥 Incoming Orders", padding="15")
        incoming_frame.pack(fill=tk.X, padx=20, pady=10)
        self.create_incoming_orders(incoming_frame)
        
        # Order Management
        mgmt_frame = ttk.LabelFrame(scrollable_frame, text="🔄 Order Management", padding="15")
        mgmt_frame.pack(fill=tk.X, padx=20, pady=10)
        self.create_staff_order_management(mgmt_frame)
        
        # Walk-in Orders
        walkin_frame = ttk.LabelFrame(scrollable_frame, text="📝 Walk-in Orders", padding="15")
        walkin_frame.pack(fill=tk.X, padx=20, pady=10)
        
        walkin_btn = ttk.Button(walkin_frame, text="Record Walk-in Order", 
                               command=self.show_walkin_order_modal, style='Success.TButton')
        walkin_btn.pack()
        
        # Inventory Status
        inv_frame = ttk.LabelFrame(scrollable_frame, text="📦 Inventory Status", padding="15")
        inv_frame.pack(fill=tk.X, padx=20, pady=10)
        self.create_staff_inventory_view(inv_frame)
    
    def create_customer_dashboard(self):
        # Clear existing widgets
        for widget in self.customer_frame.winfo_children():
            widget.destroy()
        
        # Create scrollable frame
        canvas = tk.Canvas(self.customer_frame, bg="#f0f8ff")
        scrollbar = ttk.Scrollbar(self.customer_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Dashboard content
        ttk.Label(scrollable_frame, text="Customer Portal", style='Header.TLabel').pack(pady=(0, 20))
        
        # Welcome message
        welcome_text = f"Welcome, {self.current_user_name}! Browse our delicious cakes and place your order."
        ttk.Label(scrollable_frame, text=welcome_text, font=('Arial', 12)).pack(pady=(0, 20))
        
        # Available Cakes
        cakes_frame = ttk.LabelFrame(scrollable_frame, text="🍰 Available Cakes", padding="15")
        cakes_frame.pack(fill=tk.X, padx=20, pady=10)
        self.create_customer_cake_view(cakes_frame)
        
        # My Orders
        orders_frame = ttk.LabelFrame(scrollable_frame, text="🛒 My Orders", padding="15")
        orders_frame.pack(fill=tk.X, padx=20, pady=10)
        self.create_customer_orders_view(orders_frame)
    
    def update_admin_stats(self, parent):
        # Clear existing stats
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get today's orders
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        all_orders = self.db.get_orders()
        today_orders = [order for order in all_orders if order[7].startswith(today)]
        
        today_revenue = sum(order[5] for order in today_orders)
        total_cakes = len(self.db.get_cakes())
        low_stock = len(self.db.get_low_stock_items())
        
        stats_text = f"""Today's Orders: {len(today_orders)}
Today's Revenue: ${today_revenue:.2f}
Available Cakes: {total_cakes}
Low Stock Items: {low_stock}"""
        
        ttk.Label(parent, text=stats_text, font=('Arial', 11)).pack(anchor=tk.W)
    
    def create_cake_management(self, parent):
        # Search and filter frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.cake_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.cake_search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(5, 20))
        search_entry.bind('<KeyRelease>', self.refresh_cake_list)
        
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT)
        self.cake_category_var = tk.StringVar(value="all")
        category_combo = ttk.Combobox(search_frame, textvariable=self.cake_category_var,
                                     values=["all", "birthday", "wedding", "anniversary", "celebration", "regular"],
                                     state="readonly", width=15)
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind('<<ComboboxSelected>>', self.refresh_cake_list)
        
        # Add cake button
        add_btn = ttk.Button(search_frame, text="Add New Cake", command=self.show_add_cake_modal, 
                            style='Success.TButton')
        add_btn.pack(side=tk.RIGHT)
        
        # Cake list frame
        self.cake_list_frame = ttk.Frame(parent)
        self.cake_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.refresh_cake_list()
    
    def refresh_cake_list(self, event=None):
        # Clear existing cake widgets
        for widget in self.cake_list_frame.winfo_children():
            widget.destroy()
        
        # Get filtered cakes
        category = self.cake_category_var.get() if self.cake_category_var.get() != "all" else None
        search_term = self.cake_search_var.get() if self.cake_search_var.get() else None
        cakes = self.db.get_cakes(category, search_term)
        
        if not cakes:
            ttk.Label(self.cake_list_frame, text="No cakes found matching your criteria.", 
                     font=('Arial', 12)).pack(pady=20)
            return
        
        # Create cake cards
        row, col = 0, 0
        for cake in cakes:
            cake_card = ttk.LabelFrame(self.cake_list_frame, text=cake[1], padding="10")
            cake_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Cake emoji
            emoji = self.get_cake_emoji(cake[2])
            ttk.Label(cake_card, text=emoji, font=('Arial', 24)).pack()
            
            # Cake info
            info_text = f"Flavor: {cake[2]}\nSize: {cake[3]}\nStock: {cake[5]}\nPrice: ${cake[4]:.2f}"
            ttk.Label(cake_card, text=info_text, font=('Arial', 10)).pack(pady=5)
            
            # Description
            ttk.Label(cake_card, text=cake[7], font=('Arial', 9), foreground='#666', 
                     wraplength=200).pack(pady=5)
            
            # Buttons
            btn_frame = ttk.Frame(cake_card)
            btn_frame.pack(pady=5)
            
            edit_btn = ttk.Button(btn_frame, text="Edit", style='Warning.TButton')
            edit_btn.pack(side=tk.LEFT, padx=2)
            
            delete_btn = ttk.Button(btn_frame, text="Delete", 
                                   command=lambda c=cake: self.delete_cake(c), 
                                   style='Danger.TButton')
            delete_btn.pack(side=tk.LEFT, padx=2)
            
            # Update grid position
            col += 1
            if col > 2:  # 3 columns
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            self.cake_list_frame.columnconfigure(i, weight=1)
    
    def create_order_management(self, parent):
        # Filter frame
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Filter by status:").pack(side=tk.LEFT)
        self.order_status_var = tk.StringVar(value="all")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.order_status_var,
                                   values=["all", "pending", "preparing", "ready", "completed", "cancelled"],
                                   state="readonly", width=15)
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind('<<ComboboxSelected>>', self.refresh_order_list)
        
        # Order list
        self.order_tree_frame = ttk.Frame(parent)
        self.order_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview
        columns = ("ID", "Customer", "Cake", "Qty", "Status", "Total", "Date")
        self.order_tree = ttk.Treeview(self.order_tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=100)
        
        # Scrollbar
        order_scrollbar = ttk.Scrollbar(self.order_tree_frame, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=order_scrollbar.set)
        
        self.order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        order_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click
        self.order_tree.bind("<Double-1>", self.show_order_details)
        
        self.refresh_order_list()
    
    def refresh_order_list(self, event=None):
        # Clear existing items
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # Get filtered orders
        status = self.order_status_var.get() if self.order_status_var.get() != "all" else None
        orders = self.db.get_orders(status=status)
        
        # Add orders to tree
        for order in orders:
            cake = self.db.get_cake_by_id(order[3])
            cake_name = cake[1] if cake else "Unknown"
            
            self.order_tree.insert("", "end", values=(
                f"#{order[0]}",
                order[2],
                cake_name,
                order[4],
                order[6].capitalize(),
                f"${order[5]:.2f}",
                order[7].split('T')[0]
            ))
    
    def create_staff_management(self, parent):
        # Add staff button
        add_staff_btn = ttk.Button(parent, text="Add Staff Member", 
                                  command=self.show_add_staff_modal, style='Success.TButton')
        add_staff_btn.pack(pady=10)
        
        # Staff list
        staff_members = self.db.get_users_by_role('staff')
        
        if not staff_members:
            ttk.Label(parent, text="No staff members found.", font=('Arial', 12)).pack(pady=20)
            return
        
        for staff in staff_members:
            staff_frame = ttk.LabelFrame(parent, text=staff[4], padding="10")  # name
            staff_frame.pack(fill=tk.X, padx=10, pady=5)
            
            info_text = f"Username: {staff[1]}\nEmail: {staff[5]}\nPhone: {staff[6] or 'N/A'}\nStatus: {staff[7]}"
            ttk.Label(staff_frame, text=info_text, font=('Arial', 10)).pack(anchor=tk.W)
    
    def create_inventory_management(self, parent):
        # Add inventory button
        add_inv_btn = ttk.Button(parent, text="Add Inventory Item", 
                                command=self.show_add_inventory_modal, style='Success.TButton')
        add_inv_btn.pack(pady=10)
        
        # Inventory list
        inventory = self.db.get_inventory()
        low_stock = self.db.get_low_stock_items()
        
        # Create notebook for inventory sections
        inv_notebook = ttk.Notebook(parent)
        inv_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # All inventory tab
        all_inv_frame = ttk.Frame(inv_notebook)
        inv_notebook.add(all_inv_frame, text="All Items")
        
        for item in inventory:
            item_frame = ttk.Frame(all_inv_frame)
            item_frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(item_frame, text=f"{item[1]} ({item[2]})", font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
            ttk.Label(item_frame, text=f"{item[3]} {item[4]}", font=('Arial', 10)).pack(side=tk.RIGHT)
            
            if item[3] <= item[5]:  # Low stock
                ttk.Label(item_frame, text="⚠️ LOW STOCK", foreground='red', font=('Arial', 9)).pack(side=tk.RIGHT, padx=10)
        
        # Low stock tab
        if low_stock:
            low_stock_frame = ttk.Frame(inv_notebook)
            inv_notebook.add(low_stock_frame, text=f"Low Stock ({len(low_stock)})")
            
            for item in low_stock:
                item_frame = ttk.Frame(low_stock_frame)
                item_frame.pack(fill=tk.X, padx=5, pady=2)
                
                ttk.Label(item_frame, text=f"{item[1]} ({item[2]})", 
                         font=('Arial', 11, 'bold'), foreground='red').pack(side=tk.LEFT)
                ttk.Label(item_frame, text=f"{item[3]} {item[4]} (Min: {item[5]})", 
                         font=('Arial', 10), foreground='red').pack(side=tk.RIGHT)
    
    def create_reports_section(self, parent):
        # Date range frame
        date_frame = ttk.Frame(parent)
        date_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(date_frame, text="Report Period:").pack(side=tk.LEFT)
        
        report_btn_frame = ttk.Frame(parent)
        report_btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(report_btn_frame, text="Daily Report", 
                  command=lambda: self.generate_report("daily")).pack(side=tk.LEFT, padx=5)
        ttk.Button(report_btn_frame, text="Weekly Report", 
                  command=lambda: self.generate_report("weekly")).pack(side=tk.LEFT, padx=5)
        ttk.Button(report_btn_frame, text="Monthly Report", 
                  command=lambda: self.generate_report("monthly")).pack(side=tk.LEFT, padx=5)
        
        # Report display
        self.report_text = tk.Text(parent, height=20, width=80)
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        report_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=report_scroll.set)
    
    def create_incoming_orders(self, parent):
        # Get pending orders
        orders = self.db.get_orders(status="pending")
        
        if not orders:
            ttk.Label(parent, text="No pending orders at the moment.", font=('Arial', 12)).pack(pady=10)
            return
        
        for order in orders:
            order_frame = ttk.LabelFrame(parent, text=f"Order #{order[0]}", padding="10")
            order_frame.pack(fill=tk.X, pady=5)
            
            cake = self.db.get_cake_by_id(order[3])
            cake_name = cake[1] if cake else "Unknown"
            
            info_text = f"Customer: {order[2]}\nCake: {cake_name}\nQuantity: {order[4]}\nTotal: ${order[5]:.2f}"
            ttk.Label(order_frame, text=info_text, font=('Arial', 10)).pack(anchor=tk.W)
            
            btn_frame = ttk.Frame(order_frame)
            btn_frame.pack(fill=tk.X, pady=5)
            
            ttk.Button(btn_frame, text="Accept", 
                      command=lambda o=order: self.accept_order(o), 
                      style='Success.TButton').pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_frame, text="Decline", 
                      command=lambda o=order: self.decline_order(o), 
                      style='Danger.TButton').pack(side=tk.LEFT, padx=2)
    
    def create_staff_order_management(self, parent):
        # Get active orders
        orders = self.db.get_orders()
        active_orders = [order for order in orders if order[6] not in ["completed", "cancelled"]]
        
        if not active_orders:
            ttk.Label(parent, text="No active orders at the moment.", font=('Arial', 12)).pack(pady=10)
            return
        
        for order in active_orders:
            order_frame = ttk.LabelFrame(parent, text=f"Order #{order[0]} - {order[2]}", padding="10")
            order_frame.pack(fill=tk.X, pady=5)
            
            cake = self.db.get_cake_by_id(order[3])
            cake_name = cake[1] if cake else "Unknown"
            
            info_text = f"Cake: {cake_name}\nQuantity: {order[4]}\nCurrent Status: {order[6].capitalize()}"
            ttk.Label(order_frame, text=info_text, font=('Arial', 10)).pack(anchor=tk.W)
            
            status_frame = ttk.Frame(order_frame)
            status_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(status_frame, text="Update Status:").pack(side=tk.LEFT)
            
            status_var = tk.StringVar(value=order[6])
            status_combo = ttk.Combobox(status_frame, textvariable=status_var,
                                       values=["pending", "preparing", "ready", "completed", "cancelled"],
                                       state="readonly", width=15)
            status_combo.pack(side=tk.LEFT, padx=5)
            status_combo.bind('<<ComboboxSelected>>', 
                             lambda e, o=order, sv=status_var: self.update_order_status_staff(o, sv.get()))
    
    def create_staff_inventory_view(self, parent):
        inventory = self.db.get_inventory()
        low_stock = self.db.get_low_stock_items()
        
        # Show first 5 items
        ttk.Label(parent, text="Current Inventory (Sample):", font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        for item in inventory[:5]:
            ttk.Label(parent, text=f"• {item[1]}: {item[3]} {item[4]}", 
                     font=('Arial', 10)).pack(anchor=tk.W)
        
        if low_stock:
            ttk.Label(parent, text=f"\n⚠️ Low Stock Alert: {len(low_stock)} items need restocking", 
                     font=('Arial', 11, 'bold'), foreground='red').pack(anchor=tk.W, pady=(10, 0))
    
    def create_customer_cake_view(self, parent):
        # Search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.customer_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.customer_search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(5, 20))
        search_entry.bind('<KeyRelease>', self.refresh_customer_cakes)
        
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT)
        self.customer_category_var = tk.StringVar(value="all")
        category_combo = ttk.Combobox(search_frame, textvariable=self.customer_category_var,
                                     values=["all", "birthday", "wedding", "anniversary", "celebration", "regular"],
                                     state="readonly", width=15)
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind('<<ComboboxSelected>>', self.refresh_customer_cakes)
        
        # Cake display frame
        self.customer_cake_frame = ttk.Frame(parent)
        self.customer_cake_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.refresh_customer_cakes()
    
    def refresh_customer_cakes(self, event=None):
        # Clear existing widgets
        for widget in self.customer_cake_frame.winfo_children():
            widget.destroy()
        
        # Get filtered cakes
        category = self.customer_category_var.get() if self.customer_category_var.get() != "all" else None
        search_term = self.customer_search_var.get() if self.customer_search_var.get() else None
        cakes = self.db.get_cakes(category, search_term)
        
        if not cakes:
            ttk.Label(self.customer_cake_frame, text="No cakes found matching your criteria.", 
                     font=('Arial', 12)).pack(pady=20)
            return
        
        # Create cake cards
        row, col = 0, 0
        for cake in cakes:
            cake_card = ttk.LabelFrame(self.customer_cake_frame, text=cake[1], padding="10")
            cake_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Cake emoji
            emoji = self.get_cake_emoji(cake[2])
            ttk.Label(cake_card, text=emoji, font=('Arial', 24)).pack()
            
            # Cake info
            info_text = f"{cake[2]} flavor, {cake[3]} size\nAvailable: {cake[5]} pieces"
            ttk.Label(cake_card, text=info_text, font=('Arial', 10)).pack(pady=5)
            
            # Price
            ttk.Label(cake_card, text=f"${cake[4]:.2f}", font=('Arial', 14, 'bold'), 
                     foreground='#ff69b4').pack(pady=5)
            
            # Order button
            order_btn = ttk.Button(cake_card, text="Order Now", 
                                  command=lambda c=cake: self.show_order_modal(c), 
                                  style='Success.TButton')
            order_btn.pack(pady=5)
            
            # Update grid position
            col += 1
            if col > 2:  # 3 columns
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            self.customer_cake_frame.columnconfigure(i, weight=1)
    
    def create_customer_orders_view(self, parent):
        # Get customer orders
        orders = self.db.get_orders(user_id=self.current_user_id, user_role="customer")
        
        if not orders:
            ttk.Label(parent, text="No orders yet. Browse our cakes and place your first order!", 
                     font=('Arial', 12)).pack(pady=20)
            return
        
        # Create notebook for current and history
        orders_notebook = ttk.Notebook(parent)
        orders_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Current orders
        current_frame = ttk.Frame(orders_notebook)
        orders_notebook.add(current_frame, text="Current Orders")
        
        active_orders = [order for order in orders if order[6] not in ["completed", "cancelled"]]
        
        if active_orders:
            for order in active_orders:
                self.create_order_card(current_frame, order)
        else:
            ttk.Label(current_frame, text="No current orders.", font=('Arial', 12)).pack(pady=20)
        
        # Order history
        history_frame = ttk.Frame(orders_notebook)
        orders_notebook.add(history_frame, text="Order History")
        
        for order in orders:
            self.create_order_card(history_frame, order)
    
    def create_order_card(self, parent, order):
        order_frame = ttk.LabelFrame(parent, text=f"Order #{order[0]}", padding="10")
        order_frame.pack(fill=tk.X, pady=5)
        
        cake = self.db.get_cake_by_id(order[3])
        cake_name = cake[1] if cake else "Unknown"
        
        info_text = f"Cake: {cake_name}\nQuantity: {order[4]}\nTotal: ${order[5]:.2f}\nStatus: {order[6].capitalize()}\nDate: {order[7].split('T')[0]}"
        ttk.Label(order_frame, text=info_text, font=('Arial', 10)).pack(anchor=tk.W)
        
        if order[6] == "pending":
            cancel_btn = ttk.Button(order_frame, text="Cancel Order", 
                                   command=lambda o=order: self.cancel_customer_order(o), 
                                   style='Danger.TButton')
            cancel_btn.pack(anchor=tk.E, pady=5)
    
    # Modal dialogs and helper methods
    def show_register_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Customer Registration")
        modal.geometry("400x500")
        modal.configure(bg="#f0f8ff")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(modal, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Customer Registration", style='Header.TLabel').pack(pady=(0, 20))
        
        # Form fields
        fields = [
            ("Full Name:", "name"),
            ("Username:", "username"),
            ("Password:", "password"),
            ("Confirm Password:", "confirm_password"),
            ("Email:", "email"),
            ("Phone:", "phone")
        ]
        
        entries = {}
        for label, field in fields:
            ttk.Label(main_frame, text=label, font=('Arial', 12)).pack(anchor=tk.W, pady=(10, 5))
            entry = ttk.Entry(main_frame, font=('Arial', 12), width=30)
            if field == "password" or field == "confirm_password":
                entry.config(show="*")
            entry.pack(fill=tk.X, pady=(0, 5))
            entries[field] = entry
        
        def register():
            # Get form data
            data = {field: entry.get() for field, entry in entries.items()}
            
            # Validate
            if not all([data['name'], data['username'], data['password'], data['email']]):
                messagebox.showerror("Error", "Please fill in all required fields.")
                return
            
            if data['password'] != data['confirm_password']:
                messagebox.showerror("Error", "Passwords do not match.")
                return
            
            if not self.validate_email(data['email']):
                messagebox.showerror("Error", "Please enter a valid email address.")
                return
            
            try:
                self.db.add_user(data['username'], data['password'], 'customer', 
                               data['name'], data['email'], data['phone'])
                modal.destroy()
                messagebox.showinfo("Success", "Registration successful! You can now login.")
            except Exception as e:
                messagebox.showerror("Error", f"Registration failed: {str(e)}")
        
        ttk.Button(main_frame, text="Register", command=register, 
                  style='Success.TButton').pack(pady=(20, 0))
    
    def show_add_cake_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Add New Cake")
        modal.geometry("500x600")
        modal.configure(bg="#f0f8ff")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(modal, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Add New Cake", style='Header.TLabel').pack(pady=(0, 20))
        
        # Form fields
        entries = {}
        
        # Cake Name
        ttk.Label(main_frame, text="Cake Name:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['name'] = ttk.Entry(main_frame, font=('Arial', 12), width=40)
        entries['name'].pack(fill=tk.X, pady=(0, 10))
        
        # Flavor
        ttk.Label(main_frame, text="Flavor:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['flavor'] = ttk.Combobox(main_frame, values=["chocolate", "vanilla", "strawberry", "red-velvet", "carrot", "lemon"],
                                        state="readonly", font=('Arial', 12), width=38)
        entries['flavor'].set("chocolate")
        entries['flavor'].pack(fill=tk.X, pady=(0, 10))
        
        # Size
        ttk.Label(main_frame, text="Size:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['size'] = ttk.Combobox(main_frame, values=["small", "medium", "large", "extra-large"],
                                      state="readonly", font=('Arial', 12), width=38)
        entries['size'].set("medium")
        entries['size'].pack(fill=tk.X, pady=(0, 10))
        
        # Category
        ttk.Label(main_frame, text="Category:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['category'] = ttk.Combobox(main_frame, values=["birthday", "wedding", "anniversary", "celebration", "regular"],
                                          state="readonly", font=('Arial', 12), width=38)
        entries['category'].set("regular")
        entries['category'].pack(fill=tk.X, pady=(0, 10))
        
        # Price
        ttk.Label(main_frame, text="Price:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['price'] = ttk.Entry(main_frame, font=('Arial', 12), width=40)
        entries['price'].pack(fill=tk.X, pady=(0, 10))
        
        # Stock
        ttk.Label(main_frame, text="Stock Quantity:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['stock'] = ttk.Entry(main_frame, font=('Arial', 12), width=40)
        entries['stock'].pack(fill=tk.X, pady=(0, 10))
        
        # Description
        ttk.Label(main_frame, text="Description:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['description'] = tk.Text(main_frame, font=('Arial', 12), height=4, width=40)
        entries['description'].pack(fill=tk.X, pady=(0, 10))
        
        def add_cake():
            try:
                name = entries['name'].get()
                flavor = entries['flavor'].get()
                size = entries['size'].get()
                category = entries['category'].get()
                price = float(entries['price'].get())
                stock = int(entries['stock'].get())
                description = entries['description'].get("1.0", tk.END).strip()
                
                if not name or price <= 0 or stock < 0:
                    raise ValueError("Invalid input")
                
                self.db.add_cake(name, flavor, size, price, stock, description, category)
                modal.destroy()
                self.refresh_cake_list()
                messagebox.showinfo("Success", "Cake added successfully!")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid values for all fields.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add cake: {str(e)}")
        
        ttk.Button(main_frame, text="Add Cake", command=add_cake, 
                  style='Success.TButton').pack(pady=(10, 0))
    
    def show_add_staff_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Add Staff Member")
        modal.geometry("400x450")
        modal.configure(bg="#f0f8ff")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(modal, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Add Staff Member", style='Header.TLabel').pack(pady=(0, 20))
        
        # Form fields
        fields = [
            ("Full Name:", "name"),
            ("Username:", "username"),
            ("Password:", "password"),
            ("Email:", "email"),
            ("Phone:", "phone")
        ]
        
        entries = {}
        for label, field in fields:
            ttk.Label(main_frame, text=label, font=('Arial', 12)).pack(anchor=tk.W, pady=(10, 5))
            entry = ttk.Entry(main_frame, font=('Arial', 12), width=30)
            if field == "password":
                entry.config(show="*")
            entry.pack(fill=tk.X, pady=(0, 5))
            entries[field] = entry
        
        def add_staff():
            data = {field: entry.get() for field, entry in entries.items()}
            
            if not all([data['name'], data['username'], data['password'], data['email']]):
                messagebox.showerror("Error", "Please fill in all required fields.")
                return
            
            if not self.validate_email(data['email']):
                messagebox.showerror("Error", "Please enter a valid email address.")
                return
            
            try:
                self.db.add_user(data['username'], data['password'], 'staff', 
                               data['name'], data['email'], data['phone'])
                modal.destroy()
                messagebox.showinfo("Success", "Staff member added successfully!")
                # Refresh staff list if needed
                if self.current_role == "admin":
                    self.create_admin_dashboard()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add staff: {str(e)}")
        
        ttk.Button(main_frame, text="Add Staff", command=add_staff, 
                  style='Success.TButton').pack(pady=(20, 0))
    
    def show_add_inventory_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Add Inventory Item")
        modal.geometry("400x400")
        modal.configure(bg="#f0f8ff")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(modal, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Add Inventory Item", style='Header.TLabel').pack(pady=(0, 20))
        
        entries = {}
        
        # Item Name
        ttk.Label(main_frame, text="Item Name:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['name'] = ttk.Entry(main_frame, font=('Arial', 12), width=30)
        entries['name'].pack(fill=tk.X, pady=(0, 10))
        
        # Category
        ttk.Label(main_frame, text="Category:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['category'] = ttk.Combobox(main_frame, values=["baking", "dairy", "flavoring", "decorations", "packaging"],
                                          state="readonly", font=('Arial', 12), width=28)
        entries['category'].set("baking")
        entries['category'].pack(fill=tk.X, pady=(0, 10))
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['quantity'] = ttk.Entry(main_frame, font=('Arial', 12), width=30)
        entries['quantity'].pack(fill=tk.X, pady=(0, 10))
        
        # Unit
        ttk.Label(main_frame, text="Unit:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['unit'] = ttk.Combobox(main_frame, values=["lbs", "kg", "pieces", "liters", "packets"],
                                      state="readonly", font=('Arial', 12), width=28)
        entries['unit'].set("lbs")
        entries['unit'].pack(fill=tk.X, pady=(0, 10))
        
        # Min Stock Level
        ttk.Label(main_frame, text="Minimum Stock Level:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['min_stock'] = ttk.Entry(main_frame, font=('Arial', 12), width=30)
        entries['min_stock'].pack(fill=tk.X, pady=(0, 10))
        
        def add_item():
            try:
                name = entries['name'].get()
                category = entries['category'].get()
                quantity = float(entries['quantity'].get())
                unit = entries['unit'].get()
                min_stock = float(entries['min_stock'].get())
                
                if not name or quantity < 0 or min_stock < 0:
                    raise ValueError("Invalid input")
                
                self.db.add_inventory_item(name, category, quantity, unit, min_stock)
                modal.destroy()
                messagebox.showinfo("Success", "Inventory item added successfully!")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid values for all fields.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add inventory item: {str(e)}")
        
        ttk.Button(main_frame, text="Add Item", command=add_item, 
                  style='Success.TButton').pack(pady=(10, 0))
    
    def show_walkin_order_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Record Walk-in Order")
        modal.geometry("500x600")
        modal.configure(bg="#f0f8ff")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(modal, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Record Walk-in Order", style='Header.TLabel').pack(pady=(0, 20))
        
        entries = {}
        
        # Customer Name
        ttk.Label(main_frame, text="Customer Name:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['name'] = ttk.Entry(main_frame, font=('Arial', 12), width=40)
        entries['name'].pack(fill=tk.X, pady=(0, 10))
        
        # Phone
        ttk.Label(main_frame, text="Phone:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['phone'] = ttk.Entry(main_frame, font=('Arial', 12), width=40)
        entries['phone'].pack(fill=tk.X, pady=(0, 10))
        
        # Email (optional)
        ttk.Label(main_frame, text="Email (optional):", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['email'] = ttk.Entry(main_frame, font=('Arial', 12), width=40)
        entries['email'].pack(fill=tk.X, pady=(0, 10))
        
        # Cake selection
        ttk.Label(main_frame, text="Select Cake:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        cakes = self.db.get_cakes()
        cake_options = [f"{cake[1]} - ${cake[4]:.2f}" for cake in cakes]
        entries['cake'] = ttk.Combobox(main_frame, values=cake_options, state="readonly", 
                                      font=('Arial', 12), width=38)
        if cake_options:
            entries['cake'].set(cake_options[0])
        entries['cake'].pack(fill=tk.X, pady=(0, 10))
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['quantity'] = ttk.Combobox(main_frame, values=["1", "2", "3", "4", "5"], 
                                          state="readonly", font=('Arial', 12), width=38)
        entries['quantity'].set("1")
        entries['quantity'].pack(fill=tk.X, pady=(0, 10))
        
        # Special Instructions
        ttk.Label(main_frame, text="Special Instructions:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['instructions'] = tk.Text(main_frame, font=('Arial', 12), height=3, width=40)
        entries['instructions'].pack(fill=tk.X, pady=(0, 10))
        
        # Service Type
        ttk.Label(main_frame, text="Service Type:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['service'] = ttk.Combobox(main_frame, values=["pickup", "delivery"], 
                                         state="readonly", font=('Arial', 12), width=38)
        entries['service'].set("pickup")
        entries['service'].pack(fill=tk.X, pady=(0, 10))
        
        # Address (for delivery)
        address_frame = ttk.Frame(main_frame)
        ttk.Label(address_frame, text="Delivery Address:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['address'] = tk.Text(address_frame, font=('Arial', 12), height=2, width=40)
        entries['address'].pack(fill=tk.X, pady=(0, 10))
        
        def toggle_address(*args):
            if entries['service'].get() == "delivery":
                address_frame.pack(fill=tk.X, pady=(0, 10))
            else:
                address_frame.pack_forget()
        
        entries['service'].bind('<<ComboboxSelected>>', toggle_address)
        
        def record_order():
            try:
                name = entries['name'].get()
                phone = entries['phone'].get()
                email = entries['email'].get()
                cake_selection = entries['cake'].get()
                quantity = int(entries['quantity'].get())
                instructions = entries['instructions'].get("1.0", tk.END).strip()
                service = entries['service'].get()
                address = entries['address'].get("1.0", tk.END).strip()
                
                if not name or not phone or not cake_selection:
                    messagebox.showerror("Error", "Please fill in all required fields.")
                    return
                
                if service == "delivery" and not address:
                    messagebox.showerror("Error", "Please provide a delivery address.")
                    return
                
                # Extract cake ID
                cake_name = cake_selection.split(" - $")[0]
                cake = None
                for c in cakes:
                    if c[1] == cake_name:
                        cake = c
                        break
                
                if not cake:
                    messagebox.showerror("Error", "Selected cake not found.")
                    return
                
                total_price = cake[4] * quantity
                if service == "delivery":
                    total_price += 5  # Delivery fee
                
                order_id = self.db.create_order(
                    customer_id=None,
                    customer_name=name,
                    cake_id=cake[0],
                    quantity=quantity,
                    total_price=total_price,
                    status="pending",
                    special_instructions=instructions,
                    delivery_type=service,
                    delivery_date=datetime.datetime.now().isoformat(),
                    address=address,
                    phone=phone,
                    email=email
                )
                
                self.db.update_cake_stock(cake[0], quantity)
                
                modal.destroy()
                messagebox.showinfo("Success", f"Walk-in order recorded successfully!\nOrder #{order_id}\nTotal: ${total_price:.2f}")
                
                # Refresh staff dashboard
                if self.current_role == "staff":
                    self.create_staff_dashboard()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid quantity.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to record order: {str(e)}")
        
        ttk.Button(main_frame, text="Record Order", command=record_order, 
                  style='Success.TButton').pack(pady=(10, 0))
    
    def show_order_modal(self, cake):
        modal = tk.Toplevel(self.root)
        modal.title(f"Order {cake[1]}")
        modal.geometry("500x700")
        modal.configure(bg="#f0f8ff")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(modal, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"Order: {cake[1]}", style='Header.TLabel').pack(pady=(0, 20))
        
        entries = {}
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['quantity'] = ttk.Combobox(main_frame, values=["1", "2", "3"], 
                                          state="readonly", font=('Arial', 12), width=38)
        entries['quantity'].set("1")
        entries['quantity'].pack(fill=tk.X, pady=(0, 10))
        
        # Special Message
        ttk.Label(main_frame, text="Special Message:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['message'] = ttk.Entry(main_frame, font=('Arial', 12), width=40)
        entries['message'].pack(fill=tk.X, pady=(0, 10))
        
        # Design Request
        ttk.Label(main_frame, text="Design Request:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['design'] = tk.Text(main_frame, font=('Arial', 12), height=4, width=40)
        entries['design'].pack(fill=tk.X, pady=(0, 10))
        
        # Delivery Date
        ttk.Label(main_frame, text="Pickup/Delivery Date:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        entries['date'] = ttk.Entry(date_frame, font=('Arial', 12), width=15)
        entries['date'].pack(side=tk.LEFT)
        entries['date'].insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        entries['time'] = ttk.Entry(date_frame, font=('Arial', 12), width=10)
        entries['time'].pack(side=tk.LEFT, padx=(10, 0))
        entries['time'].insert(0, "12:00")
        
        # Service Type
        ttk.Label(main_frame, text="Service Type:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['service'] = ttk.Combobox(main_frame, values=["pickup", "delivery"], 
                                         state="readonly", font=('Arial', 12), width=38)
        entries['service'].set("pickup")
        entries['service'].pack(fill=tk.X, pady=(0, 10))
        
        # Address (for delivery)
        address_frame = ttk.Frame(main_frame)
        ttk.Label(address_frame, text="Delivery Address:", font=('Arial', 12)).pack(anchor=tk.W, pady=(5, 2))
        entries['address'] = tk.Text(address_frame, font=('Arial', 12), height=3, width=40)
        entries['address'].pack(fill=tk.X, pady=(0, 10))
        
        def toggle_address(*args):
            if entries['service'].get() == "delivery":
                address_frame.pack(fill=tk.X, pady=(0, 10))
            else:
                address_frame.pack_forget()
        
        entries['service'].bind('<<ComboboxSelected>>', toggle_address)
        
        # Price display
        price_frame = ttk.Frame(main_frame)
        price_frame.pack(fill=tk.X, pady=(10, 0))
        
        base_price_label = ttk.Label(price_frame, text=f"Base Price: ${cake[4]:.2f}", font=('Arial', 12))
        base_price_label.pack(side=tk.LEFT)
        
        delivery_label = ttk.Label(price_frame, text="", font=('Arial', 12), foreground='green')
        delivery_label.pack(side=tk.LEFT, padx=(10, 0))
        
        total_label = ttk.Label(price_frame, text=f"Total: ${cake[4]:.2f}", 
                               font=('Arial', 12, 'bold'), foreground='#ff69b4')
        total_label.pack(side=tk.RIGHT)
        
        def update_prices(*args):
            try:
                qty = int(entries['quantity'].get())
                base_price = cake[4] * qty
                delivery_fee = 5 if entries['service'].get() == "delivery" else 0
                total = base_price + delivery_fee
                
                base_price_label.config(text=f"Base Price: ${base_price:.2f}")
                
                if delivery_fee > 0:
                    delivery_label.config(text=f"+ ${delivery_fee:.2f} delivery")
                else:
                    delivery_label.config(text="")
                
                total_label.config(text=f"Total: ${total:.2f}")
            except:
                pass
        
        entries['quantity'].bind('<<ComboboxSelected>>', update_prices)
        entries['service'].bind('<<ComboboxSelected>>', update_prices)
        
        def confirm_order():
            try:
                quantity = int(entries['quantity'].get())
                message = entries['message'].get()
                design = entries['design'].get("1.0", tk.END).strip()
                date = entries['date'].get()
                time = entries['time'].get()
                service = entries['service'].get()
                address = entries['address'].get("1.0", tk.END).strip()
                
                if not date:
                    messagebox.showerror("Error", "Please enter a delivery date.")
                    return
                
                if service == "delivery" and not address:
                    messagebox.showerror("Error", "Please provide a delivery address.")
                    return
                
                base_price = cake[4] * quantity
                delivery_fee = 5 if service == "delivery" else 0
                total = base_price + delivery_fee
                
                # Get user info
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT email, phone FROM users WHERE id = ?", (self.current_user_id,))
                user_info = cursor.fetchone()
                email = user_info[0] if user_info else None
                phone = user_info[1] if user_info else None
                
                order_id = self.db.create_order(
                    customer_id=self.current_user_id,
                    customer_name=self.current_user_name,
                    cake_id=cake[0],
                    quantity=quantity,
                    total_price=total,
                    status="pending",
                    special_instructions=f"{message}\n\nDesign: {design}",
                    delivery_type=service,
                    delivery_date=f"{date} {time}",
                    address=address,
                    phone=phone,
                    email=email
                )
                
                self.db.update_cake_stock(cake[0], quantity)
                
                modal.destroy()
                messagebox.showinfo("Success", f"Order placed successfully!\nOrder #{order_id}\nTotal: ${total:.2f}")
                
                # Refresh customer dashboard
                self.create_customer_dashboard()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid values.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to place order: {str(e)}")
        
        ttk.Button(main_frame, text="Confirm Order", command=confirm_order, 
                  style='Success.TButton').pack(pady=(20, 0))
    
    def show_order_details(self, event):
        selection = self.order_tree.selection()
        if not selection:
            return
        
        item = self.order_tree.item(selection[0])
        order_id = item['values'][0].replace("#", "")
        
        # Get order details
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return
        
        # Create details modal
        modal = tk.Toplevel(self.root)
        modal.title(f"Order Details #{order_id}")
        modal.geometry("500x600")
        modal.configure(bg="#f0f8ff")
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(modal, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"Order Details #{order_id}", style='Header.TLabel').pack(pady=(0, 20))
        
        # Order details
        cake = self.db.get_cake_by_id(order[3])
        cake_name = cake[1] if cake else "Unknown Cake"
        
        details_text = f"""Customer: {order[2]}
Cake: {cake_name}
Quantity: {order[4]}
Total: ${order[5]:.2f}
Status: {order[6].capitalize()}
Order Date: {order[7].split('T')[0]}
Delivery Date: {order[9] if order[9] else 'N/A'}
Delivery Type: {order[10].capitalize()}"""
        
        if order[11]:  # special instructions
            details_text += f"\n\nSpecial Instructions:\n{order[11]}"
        
        if order[12]:  # address
            details_text += f"\n\nAddress:\n{order[12]}"
        
        details_label = ttk.Label(main_frame, text=details_text, font=('Arial', 11), justify=tk.LEFT)
        details_label.pack(anchor=tk.W, pady=(0, 20))
        
        ttk.Button(main_frame, text="Close", command=modal.destroy).pack()
    
    # Helper methods
    def get_cake_emoji(self, flavor):
        emoji_map = {
            "chocolate": "🍫",
            "vanilla": "🍰",
            "strawberry": "🍓",
            "red-velvet": "❤️",
            "carrot": "🥕",
            "lemon": "🍋",
            "cheesecake": "🧀"
        }
        return emoji_map.get(flavor, "🎂")
    
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def delete_cake(self, cake):
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete '{cake[1]}'?"):
            try:
                self.db.delete_cake(cake[0])
                self.refresh_cake_list()
                messagebox.showinfo("Success", "Cake deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete cake: {str(e)}")
    
    def accept_order(self, order):
        self.db.update_order_status(order[0], "preparing", "Order accepted by staff")
        messagebox.showinfo("Success", f"Order #{order[0]} has been accepted and moved to preparation.")
        self.create_staff_dashboard()
    
    def decline_order(self, order):
        if messagebox.askyesno("Confirm", "Are you sure you want to decline this order?"):
            self.db.update_order_status(order[0], "cancelled", "Order declined by staff")
            messagebox.showinfo("Success", f"Order #{order[0]} has been declined and cancelled.")
            self.create_staff_dashboard()
    
    def update_order_status_staff(self, order, new_status):
        self.db.update_order_status(order[0], new_status, f"Status changed by {self.current_role}")
        messagebox.showinfo("Success", f"Order #{order[0]} status updated to: {new_status}")
        self.create_staff_dashboard()
    
    def cancel_customer_order(self, order):
        if messagebox.askyesno("Confirm", "Are you sure you want to cancel this order?"):
            self.db.update_order_status(order[0], "cancelled", "Cancelled by customer")
            messagebox.showinfo("Success", f"Order #{order[0]} has been cancelled.")
            self.create_customer_dashboard()
    
    def generate_report(self, period):
        end_date = datetime.datetime.now()
        
        if period == "daily":
            start_date = end_date
            period_text = "Daily"
        elif period == "weekly":
            start_date = end_date - datetime.timedelta(days=7)
            period_text = "Weekly"
        elif period == "monthly":
            start_date = end_date - datetime.timedelta(days=30)
            period_text = "Monthly"
        else:
            return
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Get orders in date range
        all_orders = self.db.get_orders()
        period_orders = [order for order in all_orders 
                        if start_date_str <= order[7].split('T')[0] <= end_date_str]
        
        total_orders = len(period_orders)
        total_revenue = sum(order[5] for order in period_orders)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Status breakdown
        status_counts = {}
        for order in period_orders:
            status = order[6]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Generate report text
        report_text = f"{period_text} Report ({start_date_str} to {end_date_str})\n"
        report_text += "=" * 50 + "\n\n"
        report_text += f"Total Orders: {total_orders}\n"
        report_text += f"Total Revenue: ${total_revenue:.2f}\n"
        report_text += f"Average Order Value: ${avg_order_value:.2f}\n\n"
        
        report_text += "Order Status Breakdown:\n"
        for status, count in status_counts.items():
            report_text += f"  {status.capitalize()}: {count}\n"
        
        # Popular items
        cake_counts = {}
        for order in period_orders:
            cake_id = order[3]
            cake = self.db.get_cake_by_id(cake_id)
            if cake:
                cake_name = cake[1]
                cake_counts[cake_name] = cake_counts.get(cake_name, 0) + order[4]
        
        if cake_counts:
            report_text += f"\nMost Popular Items:\n"
            sorted_cakes = sorted(cake_counts.items(), key=lambda x: x[1], reverse=True)
            for cake_name, count in sorted_cakes[:5]:
                report_text += f"  {cake_name}: {count} orders\n"
        
        # Display report
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report_text)

def main():
    root = tk.Tk()
    app = SweetDreamsApp(root)
    
    # Bind mouse wheel scrolling
    def _on_mousewheel(event):
        try:
            # Find the canvas widget
            widget = event.widget
            while widget and not isinstance(widget, tk.Canvas):
                widget = widget.master
            if widget:
                widget.yview_scroll(int(-1*(event.delta/120)), "units")
        except:
            pass
    
    root.bind_all("<MouseWheel>", _on_mousewheel)
    
    root.mainloop()

if __name__ == "__main__":
    main()