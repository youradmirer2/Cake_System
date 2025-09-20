import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
from PIL import Image, ImageTk
import random
import sqlite3
import hashlib
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re

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
        
        # Staff table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                position TEXT NOT NULL,
                hire_date TEXT NOT NULL,
                salary REAL,
                FOREIGN KEY (user_id) REFERENCES users (id)
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
                ('Chocolate', 'baking', 40.0, 'lbs', 8.0, datetime.datetime.now().isoformat()),
                ('Vanilla Extract', 'flavoring', 5.0, 'liters', 1.0, datetime.datetime.now().isoformat())
            ]
            
            cursor.executemany(
                "INSERT INTO inventory (item_name, category, quantity, unit, min_stock_level, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
                inventory
            )
            
            self.conn.commit()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_user(self, username, password, role):
        cursor = self.conn.cursor()
        hashed_password = self.hash_password(password)
        cursor.execute(
            "SELECT id, name, email FROM users WHERE username = ? AND password = ? AND role = ? AND status = 'active'",
            (username, hashed_password, role)
        )
        return cursor.fetchone()
    
    def get_cakes(self, category=None, search_term=None):
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
    
    def get_cake_by_id(self, cake_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cakes WHERE id = ?", (cake_id,))
        return cursor.fetchone()
    
    def update_cake_stock(self, cake_id, quantity):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE cakes SET stock = stock - ? WHERE id = ?", (quantity, cake_id))
        self.conn.commit()
    
    def create_order(self, customer_id, customer_name, cake_id, quantity, total_price, status, 
                    special_instructions, delivery_type, delivery_date, address, phone, email):
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
    
    def get_orders(self, user_id=None, user_role=None, status=None):
        cursor = self.conn.cursor()
        
        if user_role == "customer":
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
    
    def update_order_status(self, order_id, new_status, notes=None):
        cursor = self.conn.cursor()
        changed_at = datetime.datetime.now().isoformat()
        
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        
        cursor.execute(
            "INSERT INTO order_status_history (order_id, status, changed_at, notes) VALUES (?, ?, ?, ?)",
            (order_id, new_status, changed_at, notes)
        )
        
        self.conn.commit()
    
    def get_order_history(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY changed_at DESC",
            (order_id,)
        )
        return cursor.fetchall()
    
    def get_inventory(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM inventory ORDER BY category, item_name")
        return cursor.fetchall()
    
    def update_inventory(self, item_id, quantity):
        cursor = self.conn.cursor()
        last_updated = datetime.datetime.now().isoformat()
        cursor.execute(
            "UPDATE inventory SET quantity = ?, last_updated = ? WHERE id = ?",
            (quantity, last_updated, item_id)
        )
        self.conn.commit()
    
    def add_inventory_item(self, item_name, category, quantity, unit, min_stock_level):
        cursor = self.conn.cursor()
        last_updated = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO inventory (item_name, category, quantity, unit, min_stock_level, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
            (item_name, category, quantity, unit, min_stock_level, last_updated)
        )
        self.conn.commit()
    
    def get_low_stock_items(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM inventory WHERE quantity <= min_stock_level")
        return cursor.fetchall()
    
    def get_sales_report(self, start_date, end_date):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT 
                COUNT(*) as total_orders,
                SUM(total_price) as total_revenue,
                AVG(total_price) as avg_order_value,
                status,
                COUNT(CASE WHEN delivery_type = 'delivery' THEN 1 END) as delivery_orders,
                COUNT(CASE WHEN delivery_type = 'pickup' THEN 1 END) as pickup_orders
            FROM orders 
            WHERE order_date BETWEEN ? AND ?
            GROUP BY status""",
            (start_date, end_date)
        )
        return cursor.fetchall()
    
    def get_popular_items(self, start_date, end_date):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT 
                c.name, 
                c.flavor, 
                c.category,
                COUNT(o.id) as order_count,
                SUM(o.quantity) as total_quantity,
                SUM(o.total_price) as total_revenue
            FROM orders o
            JOIN cakes c ON o.cake_id = c.id
            WHERE o.order_date BETWEEN ? AND ?
            GROUP BY o.cake_id
            ORDER BY total_revenue DESC
            LIMIT 10""",
            (start_date, end_date)
        )
        return cursor.fetchall()

class EmailService:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_email(self, to_email, subject, body):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.username, to_email, text)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

class SweetDreamsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sweet Dreams Cake Ordering System")
        self.root.geometry("1200x800")
        self.root.configure(bg="#764ba2")
        
        # Initialize database
        self.db = Database()
        
        # Email service (configure with your SMTP settings)
        self.email_service = EmailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="your_email@gmail.com",
            password="your_app_password"
        )
        
        # Current user state
        self.current_user = None
        self.current_user_id = None
        self.current_role = None
        self.current_user_name = None
        
        # Image cache
        self.image_cache = {}
        
        # Create the main container
        self.main_container = tk.Frame(root, bg="white", relief=tk.RAISED, bd=2)
        self.main_container.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Create header
        self.create_header()
        
        # Create tabs container
        self.tab_control = ttk.Notebook(self.main_container)
        
        # Create tabs
        self.login_tab = ttk.Frame(self.tab_control)
        self.admin_tab = ttk.Frame(self.tab_control)
        self.staff_tab = ttk.Frame(self.tab_control)
        self.customer_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.login_tab, text="Login")
        self.tab_control.add(self.admin_tab, text="Admin Dashboard", state="hidden")
        self.tab_control.add(self.staff_tab, text="Staff Dashboard", state="hidden")
        self.tab_control.add(self.customer_tab, text="Customer Portal", state="hidden")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Create login form
        self.create_login_form()
        
        # Create admin dashboard
        self.create_admin_dashboard()
        
        # Create staff dashboard
        self.create_staff_dashboard()
        
        # Create customer dashboard
        self.create_customer_dashboard()
        
        # Show login tab by default
        self.tab_control.select(self.login_tab)
    
    def create_header(self):
        header_frame = tk.Frame(self.main_container, bg="white")
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            header_frame, 
            text="🎂 Sweet Cake", 
            font=("Arial", 24, "bold"),
            fg="#ff6b6b",
            bg="white"
        )
        title_label.pack(pady=(10, 0))
        
        # User info (initially hidden)
        self.user_info_frame = tk.Frame(header_frame, bg="white")
        self.user_info_frame.pack(side=tk.RIGHT, padx=10)
        
        self.user_label = tk.Label(
            self.user_info_frame, 
            text="", 
            font=("Arial", 10),
            bg="white"
        )
        self.user_label.pack(side=tk.LEFT)
        
        self.logout_btn = tk.Button(
            self.user_info_frame,
            text="Logout",
            command=self.logout,
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        self.logout_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        self.user_info_frame.pack_forget()  # Hide initially
    
    def create_login_form(self):
        login_frame = tk.Frame(self.login_tab, bg="white")
        login_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        title_label = tk.Label(
            login_frame,
            text="System Login",
            font=("Arial", 18, "bold"),
            fg="#333",
            bg="white"
        )
        title_label.pack(pady=(0, 30))
        
        # Username
        username_frame = tk.Frame(login_frame, bg="white")
        username_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            username_frame,
            text="Username:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W)
        
        self.username_entry = tk.Entry(
            username_frame,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        self.username_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Password
        password_frame = tk.Frame(login_frame, bg="white")
        password_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            password_frame,
            text="Password:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W)
        
        self.password_entry = tk.Entry(
            password_frame,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1,
            show="*"
        )
        self.password_entry.pack(fill=tk.X, pady=(5, 0))
        
        # User Type
        user_type_frame = tk.Frame(login_frame, bg="white")
        user_type_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            user_type_frame,
            text="User Type:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W)
        
        self.user_type_var = tk.StringVar(value="admin")
        user_type_combo = ttk.Combobox(
            user_type_frame,
            textvariable=self.user_type_var,
            values=["admin", "staff", "customer"],
            state="readonly",
            font=("Arial", 12)
        )
        user_type_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Login Button
        login_btn = tk.Button(
            login_frame,
            text="Login",
            command=self.login,
            bg="#667eea",
            fg="white",
            font=("Arial", 14, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        login_btn.pack(pady=20)
        
        # Register link for customers
        register_frame = tk.Frame(login_frame, bg="white")
        register_frame.pack(pady=10)
        
        tk.Label(
            register_frame,
            text="Don't have an account?",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT)
        
        register_btn = tk.Button(
            register_frame,
            text="Register here",
            command=self.show_register_modal,
            font=("Arial", 10, "underline"),
            fg="#667eea",
            bg="white",
            relief=tk.FLAT,
            cursor="hand2"
        )
        register_btn.pack(side=tk.LEFT, padx=(5, 0))
    
    def create_admin_dashboard(self):
        # Create a canvas and scrollbar for the admin dashboard
        canvas = tk.Canvas(self.admin_tab, bg="white")
        scrollbar = ttk.Scrollbar(self.admin_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = tk.Label(
            scrollable_frame,
            text="Admin Dashboard",
            font=("Arial", 18, "bold"),
            fg="#333",
            bg="white"
        )
        title_label.pack(pady=(20, 10))
        
        # Quick Stats
        stats_frame = tk.LabelFrame(
            scrollable_frame,
            text="📊 Quick Stats",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_display = tk.Label(
            stats_frame,
            text="Loading stats...",
            font=("Arial", 11),
            bg="white",
            justify=tk.LEFT
        )
        self.stats_display.pack(anchor=tk.W)
        
        # Cake Management
        cake_frame = tk.LabelFrame(
            scrollable_frame,
            text="🍰 Cake Management",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        cake_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Search and filter frame
        search_frame = tk.Frame(cake_frame, bg="white")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            search_frame,
            text="Search:",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT)
        
        self.cake_search_entry = tk.Entry(
            search_frame,
            font=("Arial", 10),
            width=20
        )
        self.cake_search_entry.pack(side=tk.LEFT, padx=5)
        self.cake_search_entry.bind("<KeyRelease>", self.filter_cakes)
        
        tk.Label(
            search_frame,
            text="Category:",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT, padx=(20, 5))
        
        self.category_var = tk.StringVar(value="all")
        category_combo = ttk.Combobox(
            search_frame,
            textvariable=self.category_var,
            values=["all", "birthday", "wedding", "anniversary", "celebration", "regular"],
            state="readonly",
            width=15,
            font=("Arial", 10)
        )
        category_combo.pack(side=tk.LEFT)
        category_combo.bind("<<ComboboxSelected>>", self.filter_cakes)
        
        add_cake_btn = tk.Button(
            cake_frame,
            text="Add New Cake",
            command=self.show_add_cake_modal,
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        add_cake_btn.pack(pady=(0, 10))
        
        # Cake list
        self.admin_cake_frame = tk.Frame(cake_frame, bg="white")
        self.admin_cake_frame.pack(fill=tk.X)
        
        # Staff Management
        staff_frame = tk.LabelFrame(
            scrollable_frame,
            text="👥 Staff Management",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        staff_frame.pack(fill=tk.X, padx=20, pady=10)
        
        add_staff_btn = tk.Button(
            staff_frame,
            text="Add Staff Member",
            command=self.show_add_staff_modal,
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        add_staff_btn.pack(pady=(0, 10))
        
        # Staff list
        self.staff_list_frame = tk.Frame(staff_frame, bg="white")
        self.staff_list_frame.pack(fill=tk.X)
        
        # Inventory Management
        inventory_frame = tk.LabelFrame(
            scrollable_frame,
            text="📦 Inventory Management",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        inventory_frame.pack(fill=tk.X, padx=20, pady=10)
        
        inventory_btn_frame = tk.Frame(inventory_frame, bg="white")
        inventory_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        view_inv_btn = tk.Button(
            inventory_btn_frame,
            text="View Inventory",
            command=self.show_inventory_modal,
            bg="#667eea",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        view_inv_btn.pack(side=tk.LEFT, padx=5)
        
        add_inv_btn = tk.Button(
            inventory_btn_frame,
            text="Add Inventory Item",
            command=self.show_add_inventory_modal,
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        add_inv_btn.pack(side=tk.LEFT, padx=5)
        
        low_stock_btn = tk.Button(
            inventory_btn_frame,
            text="Check Low Stock",
            command=self.show_low_stock_modal,
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        low_stock_btn.pack(side=tk.LEFT, padx=5)
        
        # Sales Reports
        report_frame = tk.LabelFrame(
            scrollable_frame,
            text="📈 Sales Reports",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        report_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Date range for reports
        date_frame = tk.Frame(report_frame, bg="white")
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            date_frame,
            text="From:",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT)
        
        self.start_date_entry = tk.Entry(
            date_frame,
            font=("Arial", 10),
            width=12
        )
        self.start_date_entry.pack(side=tk.LEFT, padx=5)
        self.start_date_entry.insert(0, (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
        
        tk.Label(
            date_frame,
            text="To:",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        self.end_date_entry = tk.Entry(
            date_frame,
            font=("Arial", 10),
            width=12
        )
        self.end_date_entry.pack(side=tk.LEFT, padx=5)
        self.end_date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        report_btn_frame = tk.Frame(report_frame, bg="white")
        report_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        daily_btn = tk.Button(
            report_btn_frame,
            text="Daily Report",
            command=lambda: self.generate_report("daily"),
            bg="#667eea",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        daily_btn.pack(side=tk.LEFT, padx=5)
        
        weekly_btn = tk.Button(
            report_btn_frame,
            text="Weekly Report",
            command=lambda: self.generate_report("weekly"),
            bg="#667eea",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        weekly_btn.pack(side=tk.LEFT, padx=5)
        
        monthly_btn = tk.Button(
            report_btn_frame,
            text="Monthly Report",
            command=lambda: self.generate_report("monthly"),
            bg="#667eea",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        monthly_btn.pack(side=tk.LEFT, padx=5)
        
        custom_btn = tk.Button(
            report_btn_frame,
            text="Custom Report",
            command=self.generate_custom_report,
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        custom_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(
            report_btn_frame,
            text="Export PDF",
            command=self.export_report_pdf,
            bg="#feca57",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        self.report_display = tk.Label(
            report_frame,
            text="Select a report to generate...",
            font=("Arial", 11),
            bg="white",
            justify=tk.LEFT
        )
        self.report_display.pack(anchor=tk.W)
        
        # All Orders
        orders_frame = tk.LabelFrame(
            scrollable_frame,
            text="📋 All Orders",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        orders_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Order filter
        order_filter_frame = tk.Frame(orders_frame, bg="white")
        order_filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            order_filter_frame,
            text="Filter by status:",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT)
        
        self.order_status_var = tk.StringVar(value="all")
        status_combo = ttk.Combobox(
            order_filter_frame,
            textvariable=self.order_status_var,
            values=["all", "pending", "preparing", "ready", "completed", "cancelled"],
            state="readonly",
            width=15,
            font=("Arial", 10)
        )
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", self.filter_orders)
        
        # Create a treeview for orders
        columns = ("order_id", "customer", "cake", "quantity", "status", "total", "order_date")
        self.orders_tree = ttk.Treeview(
            orders_frame, 
            columns=columns, 
            show="headings",
            height=8
        )
        
        self.orders_tree.heading("order_id", text="Order ID")
        self.orders_tree.heading("customer", text="Customer")
        self.orders_tree.heading("cake", text="Cake")
        self.orders_tree.heading("quantity", text="Qty")
        self.orders_tree.heading("status", text="Status")
        self.orders_tree.heading("total", text="Total")
        self.orders_tree.heading("order_date", text="Order Date")
        
        self.orders_tree.column("order_id", width=80)
        self.orders_tree.column("customer", width=120)
        self.orders_tree.column("cake", width=150)
        self.orders_tree.column("quantity", width=50)
        self.orders_tree.column("status", width=100)
        self.orders_tree.column("total", width=80)
        self.orders_tree.column("order_date", width=100)
        
        # Add scrollbar to treeview
        tree_scroll = ttk.Scrollbar(orders_frame, orient="vertical", command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event
        self.orders_tree.bind("<Double-1>", self.show_order_details)
    
    def create_staff_dashboard(self):
        # Create a canvas and scrollbar for the staff dashboard
        canvas = tk.Canvas(self.staff_tab, bg="white")
        scrollbar = ttk.Scrollbar(self.staff_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = tk.Label(
            scrollable_frame,
            text="Staff Dashboard",
            font=("Arial", 18, "bold"),
            fg="#333",
            bg="white"
        )
        title_label.pack(pady=(20, 10))
        
        # Incoming Orders
        incoming_frame = tk.LabelFrame(
            scrollable_frame,
            text="📥 Incoming Orders",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        incoming_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.incoming_orders_frame = tk.Frame(incoming_frame, bg="white")
        self.incoming_orders_frame.pack(fill=tk.X)
        
        # Order Management
        order_mgmt_frame = tk.LabelFrame(
            scrollable_frame,
            text="🔄 Order Management",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        order_mgmt_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.order_mgmt_frame = tk.Frame(order_mgmt_frame, bg="white")
        self.order_mgmt_frame.pack(fill=tk.X)
        
        # Walk-in Order
        walkin_frame = tk.LabelFrame(
            scrollable_frame,
            text="📝 Record Walk-in Order",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        walkin_frame.pack(fill=tk.X, padx=20, pady=10)
        
        walkin_btn = tk.Button(
            walkin_frame,
            text="New Walk-in Order",
            command=self.show_walkin_order_modal,
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        walkin_btn.pack()
        
        # Inventory Status
        inventory_frame = tk.LabelFrame(
            scrollable_frame,
            text="📦 Inventory Status",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        inventory_frame.pack(fill=tk.X, padx=20, pady=10)
        
        inventory_btn_frame = tk.Frame(inventory_frame, bg="white")
        inventory_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        view_inv_btn = tk.Button(
            inventory_btn_frame,
            text="View Inventory",
            command=self.show_inventory_modal,
            bg="#667eea",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        view_inv_btn.pack(side=tk.LEFT, padx=5)
        
        low_stock_btn = tk.Button(
            inventory_btn_frame,
            text="Check Low Stock",
            command=self.show_low_stock_modal,
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        low_stock_btn.pack(side=tk.LEFT, padx=5)
        
        self.inventory_display = tk.Label(
            inventory_frame,
            text="Loading inventory...",
            font=("Arial", 11),
            bg="white",
            justify=tk.LEFT
        )
        self.inventory_display.pack(anchor=tk.W)
    
    def create_customer_dashboard(self):
        # Create a canvas and scrollbar for the customer dashboard
        canvas = tk.Canvas(self.customer_tab, bg="white")
        scrollbar = ttk.Scrollbar(self.customer_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = tk.Label(
            scrollable_frame,
            text="Customer Portal",
            font=("Arial", 18, "bold"),
            fg="#333",
            bg="white"
        )
        title_label.pack(pady=(20, 10))
        
        # Welcome message
        welcome_frame = tk.Frame(scrollable_frame, bg="white")
        welcome_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.welcome_label = tk.Label(
            welcome_frame,
            text="",
            font=("Arial", 12),
            bg="white",
            justify=tk.LEFT
        )
        self.welcome_label.pack(anchor=tk.W)
        
        # Available Cakes
        cakes_frame = tk.LabelFrame(
            scrollable_frame,
            text="🍰 Available Cakes",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        cakes_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Search and filter frame
        search_frame = tk.Frame(cakes_frame, bg="white")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            search_frame,
            text="Search:",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT)
        
        self.customer_search_entry = tk.Entry(
            search_frame,
            font=("Arial", 10),
            width=20
        )
        self.customer_search_entry.pack(side=tk.LEFT, padx=5)
        self.customer_search_entry.bind("<KeyRelease>", self.filter_customer_cakes)
        
        tk.Label(
            search_frame,
            text="Category:",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT, padx=(20, 5))
        
        self.customer_category_var = tk.StringVar(value="all")
        category_combo = ttk.Combobox(
            search_frame,
            textvariable=self.customer_category_var,
            values=["all", "birthday", "wedding", "anniversary", "celebration", "regular"],
            state="readonly",
            width=15,
            font=("Arial", 10)
        )
        category_combo.pack(side=tk.LEFT)
        category_combo.bind("<<ComboboxSelected>>", self.filter_customer_cakes)
        
        self.customer_cakes_frame = tk.Frame(cakes_frame, bg="white")
        self.customer_cakes_frame.pack(fill=tk.X)
        
        # My Orders
        orders_frame = tk.LabelFrame(
            scrollable_frame,
            text="🛒 My Orders",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        orders_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.customer_orders_frame = tk.Frame(orders_frame, bg="white")
        self.customer_orders_frame.pack(fill=tk.X)
        
        # Order History
        history_frame = tk.LabelFrame(
            scrollable_frame,
            text="📋 Order History",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        history_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Create a treeview for order history
        columns = ("date", "cake", "quantity", "status", "total")
        self.history_tree = ttk.Treeview(
            history_frame, 
            columns=columns, 
            show="headings",
            height=5
        )
        
        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("cake", text="Cake")
        self.history_tree.heading("quantity", text="Qty")
        self.history_tree.heading("status", text="Status")
        self.history_tree.heading("total", text="Total")
        
        self.history_tree.column("date", width=100)
        self.history_tree.column("cake", width=150)
        self.history_tree.column("quantity", width=50)
        self.history_tree.column("status", width=100)
        self.history_tree.column("total", width=80)
        
        # Add scrollbar to treeview
        tree_scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event
        self.history_tree.bind("<Double-1>", self.show_customer_order_details)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user_type = self.user_type_var.get()
        
        # Validate inputs
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return
        
        # Authenticate user
        user_data = self.db.validate_user(username, password, user_type)
        
        if user_data:
            self.current_user = username
            self.current_user_id = user_data[0]
            self.current_user_name = user_data[1]
            self.current_role = user_type
            
            # Show user info
            self.user_label.config(text=f"{username} ({user_type})")
            self.user_info_frame.pack(side=tk.RIGHT, padx=10)
            
            # Show appropriate tabs
            self.tab_control.tab(1, state="normal" if user_type == "admin" else "hidden")
            self.tab_control.tab(2, state="normal" if user_type == "staff" else "hidden")
            self.tab_control.tab(3, state="normal" if user_type == "customer" else "hidden")
            
            # Navigate to appropriate dashboard
            if user_type == "admin":
                self.tab_control.select(self.admin_tab)
                self.initialize_admin_dashboard()
            elif user_type == "staff":
                self.tab_control.select(self.staff_tab)
                self.initialize_staff_dashboard()
            elif user_type == "customer":
                self.tab_control.select(self.customer_tab)
                self.initialize_customer_dashboard()
            
            # Clear login form
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Invalid credentials. Please try again.")
    
    def logout(self):
        self.current_user = None
        self.current_user_id = None
        self.current_user_name = None
        self.current_role = None
        self.user_info_frame.pack_forget()
        
        # Hide all tabs except login
        self.tab_control.tab(1, state="hidden")
        self.tab_control.tab(2, state="hidden")
        self.tab_control.tab(3, state="hidden")
        
        # Show login tab
        self.tab_control.select(self.login_tab)
    
    def initialize_admin_dashboard(self):
        self.render_admin_cakes()
        self.render_all_orders()
        self.render_staff_list()
        self.update_stats_display()
    
    def initialize_staff_dashboard(self):
        self.render_incoming_orders()
        self.render_order_management()
        self.update_inventory_display()
    
    def initialize_customer_dashboard(self):
        self.welcome_label.config(text=f"Welcome, {self.current_user_name}! Browse our delicious cakes and place your order.")
        self.render_customer_cakes()
        self.render_customer_orders()
        self.render_order_history()
    
    def render_admin_cakes(self):
        # Clear existing widgets
        for widget in self.admin_cake_frame.winfo_children():
            widget.destroy()
        
        # Get cakes from database
        category = self.category_var.get() if self.category_var.get() != "all" else None
        search_term = self.cake_search_entry.get() if self.cake_search_entry.get() else None
        cakes = self.db.get_cakes(category, search_term)
        
        if not cakes:
            no_cakes_label = tk.Label(
                self.admin_cake_frame,
                text="No cakes found matching your criteria.",
                font=("Arial", 11),
                bg="white"
            )
            no_cakes_label.pack(pady=10)
            return
        
        # Create a grid of cakes
        row, col = 0, 0
        for cake in cakes:
            cake_card = tk.Frame(
                self.admin_cake_frame,
                bg="white",
                relief=tk.RAISED,
                bd=1,
                padx=10,
                pady=10
            )
            cake_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Cake image/emoji
            emoji_label = tk.Label(
                cake_card,
                text=self.get_cake_emoji(cake[2]),  # flavor
                font=("Arial", 24),
                bg="white"
            )
            emoji_label.pack(pady=(0, 10))
            
            # Cake info
            tk.Label(
                cake_card,
                text=cake[1],  # name
                font=("Arial", 12, "bold"),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                cake_card,
                text=f"Flavor: {cake[2]}",  # flavor
                font=("Arial", 10),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                cake_card,
                text=f"Size: {cake[3]}",  # size
                font=("Arial", 10),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                cake_card,
                text=f"Stock: {cake[5]}",  # stock
                font=("Arial", 10),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                cake_card,
                text=f"${cake[4]:.2f}",  # price
                font=("Arial", 12, "bold"),
                fg="#ff6b6b",
                bg="white"
            ).pack(anchor=tk.W, pady=(5, 10))
            
            # Buttons
            btn_frame = tk.Frame(cake_card, bg="white")
            btn_frame.pack(fill=tk.X)
            
            edit_btn = tk.Button(
                btn_frame,
                text="Edit",
                command=lambda c=cake: self.edit_cake(c),
                bg="#feca57",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=10
            )
            edit_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            delete_btn = tk.Button(
                btn_frame,
                text="Delete",
                command=lambda c=cake: self.delete_cake(c),
                bg="#ff6b6b",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=10
            )
            delete_btn.pack(side=tk.LEFT)
            
            # Update column and row for grid
            col += 1
            if col > 2:  # 3 columns per row
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            self.admin_cake_frame.columnconfigure(i, weight=1)
    
    def render_all_orders(self):
        # Clear existing items
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        
        # Get orders from database
        status = self.order_status_var.get() if self.order_status_var.get() != "all" else None
        orders = self.db.get_orders(status=status)
        
        # Add orders to treeview
        for order in orders:
            status_text = order[5].capitalize()  # status
            self.orders_tree.insert("", "end", values=(
                f"#{order[0]}",  # id
                order[2],  # customer_name
                self.get_cake_name(order[3]),  # cake_id -> name
                order[4],  # quantity
                status_text,
                f"${order[5]:.2f}",  # total_price
                order[7].split('T')[0] if order[7] else ""  # order_date (just date part)
            ))
    
    def render_staff_list(self):
        # Clear existing widgets
        for widget in self.staff_list_frame.winfo_children():
            widget.destroy()
        
        # Get staff from database
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT u.name, u.email, u.status FROM users u WHERE u.role = 'staff' ORDER BY u.name"
        )
        staff_members = cursor.fetchall()
        
        # Add staff members
        for staff in staff_members:
            staff_text = f"• {staff[0]} ({staff[1]}) - {staff[2]}"
            tk.Label(
                self.staff_list_frame,
                text=staff_text,
                font=("Arial", 11),
                bg="white",
                justify=tk.LEFT
            ).pack(anchor=tk.W, pady=5)
    
    def render_incoming_orders(self):
        # Clear existing widgets
        for widget in self.incoming_orders_frame.winfo_children():
            widget.destroy()
        
        # Get pending orders from database
        orders = self.db.get_orders(status="pending")
        
        if not orders:
            tk.Label(
                self.incoming_orders_frame,
                text="No pending orders at the moment.",
                font=("Arial", 11),
                bg="white"
            ).pack(pady=10)
            return
        
        # Display pending orders
        for order in orders:
            order_frame = tk.Frame(
                self.incoming_orders_frame,
                bg="#f8f9fa",
                relief=tk.RAISED,
                bd=1,
                padx=10,
                pady=10
            )
            order_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(
                order_frame,
                text=f"Order #{order[0]} - {order[2]}",  # id, customer_name
                font=("Arial", 11, "bold"),
                bg="#f8f9fa"
            ).pack(anchor=tk.W)
            
            tk.Label(
                order_frame,
                text=f"Cake: {self.get_cake_name(order[3])}",  # cake_id -> name
                font=("Arial", 10),
                bg="#f8f9fa"
            ).pack(anchor=tk.W)
            
            tk.Label(
                order_frame,
                text=f"Quantity: {order[4]}",  # quantity
                font=("Arial", 10),
                bg="#f8f9fa"
            ).pack(anchor=tk.W)
            
            tk.Label(
                order_frame,
                text=f"Total: ${order[5]:.2f}",  # total_price
                font=("Arial", 10),
                bg="#f8f9fa"
            ).pack(anchor=tk.W)
            
            tk.Label(
                order_frame,
                text=f"Date: {order[7].split('T')[0] if order[7] else ''}",  # order_date
                font=("Arial", 10),
                bg="#f8f9fa"
            ).pack(anchor=tk.W)
            
            btn_frame = tk.Frame(order_frame, bg="#f8f9fa")
            btn_frame.pack(fill=tk.X, pady=(10, 0))
            
            accept_btn = tk.Button(
                btn_frame,
                text="Accept",
                command=lambda o=order: self.accept_order(o),
                bg="#4ecdc4",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=10
            )
            accept_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            decline_btn = tk.Button(
                btn_frame,
                text="Decline",
                command=lambda o=order: self.decline_order(o),
                bg="#ff6b6b",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=10
            )
            decline_btn.pack(side=tk.LEFT)
    
    def render_order_management(self):
        # Clear existing widgets
        for widget in self.order_mgmt_frame.winfo_children():
            widget.destroy()
        
        # Get active orders (not completed or cancelled) from database
        orders = self.db.get_orders()
        active_orders = [order for order in orders if order[5] not in ["completed", "cancelled"]]
        
        if not active_orders:
            tk.Label(
                self.order_mgmt_frame,
                text="No active orders at the moment.",
                font=("Arial", 11),
                bg="white"
            ).pack(pady=10)
            return
        
        # Display order management options
        for order in active_orders:
            order_frame = tk.Frame(
                self.order_mgmt_frame,
                bg="white",
                relief=tk.RAISED,
                bd=1,
                padx=10,
                pady=10
            )
            order_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(
                order_frame,
                text=f"Order #{order[0]} - {order[2]}",  # id, customer_name
                font=("Arial", 11, "bold"),
                bg="white"
            ).pack(anchor=tk.W)
            
            status_frame = tk.Frame(order_frame, bg="white")
            status_frame.pack(fill=tk.X, pady=(5, 0))
            
            tk.Label(
                status_frame,
                text="Current Status:",
                font=("Arial", 10),
                bg="white"
            ).pack(side=tk.LEFT)
            
            status_text = order[5].capitalize()  # status
            status_color = self.get_status_color(order[5])
            
            status_label = tk.Label(
                status_frame,
                text=status_text,
                font=("Arial", 10, "bold"),
                bg=status_color,
                fg="white",
                padx=5,
                pady=2
            )
            status_label.pack(side=tk.LEFT, padx=(5, 0))
            
            # Status dropdown
            status_var = tk.StringVar(value=order[5])
            status_combo = ttk.Combobox(
                status_frame,
                textvariable=status_var,
                values=["pending", "preparing", "ready", "completed", "cancelled"],
                state="readonly",
                width=15,
                font=("Arial", 10)
            )
            status_combo.pack(side=tk.LEFT, padx=(10, 0))
            status_combo.bind("<<ComboboxSelected>>", 
                             lambda e, o=order, sv=status_var: self.update_order_status(o, sv.get()))
            
            # Notify button
            notify_btn = tk.Button(
                status_frame,
                text="Notify Customer",
                command=lambda o=order: self.notify_customer(o),
                bg="#667eea",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=10
            )
            notify_btn.pack(side=tk.LEFT, padx=(10, 0))
    
    def render_customer_cakes(self):
        # Clear existing widgets
        for widget in self.customer_cakes_frame.winfo_children():
            widget.destroy()
        
        # Get cakes from database
        category = self.customer_category_var.get() if self.customer_category_var.get() != "all" else None
        search_term = self.customer_search_entry.get() if self.customer_search_entry.get() else None
        cakes = self.db.get_cakes(category, search_term)
        
        if not cakes:
            no_cakes_label = tk.Label(
                self.customer_cakes_frame,
                text="No cakes found matching your criteria.",
                font=("Arial", 11),
                bg="white"
            )
            no_cakes_label.pack(pady=10)
            return
        
        # Create a grid of cakes
        row, col = 0, 0
        for cake in cakes:
            cake_card = tk.Frame(
                self.customer_cakes_frame,
                bg="white",
                relief=tk.RAISED,
                bd=1,
                padx=10,
                pady=10
            )
            cake_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Cake image/emoji
            emoji_label = tk.Label(
                cake_card,
                text=self.get_cake_emoji(cake[2]),  # flavor
                font=("Arial", 24),
                bg="white"
            )
            emoji_label.pack(pady=(0, 10))
            
            # Cake info
            tk.Label(
                cake_card,
                text=cake[1],  # name
                font=("Arial", 12, "bold"),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                cake_card,
                text=f"{cake[2]} flavor, {cake[3]} size",  # flavor, size
                font=("Arial", 10),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                cake_card,
                text=f"Available: {cake[5]} pieces",  # stock
                font=("Arial", 10),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                cake_card,
                text=f"${cake[4]:.2f}",  # price
                font=("Arial", 12, "bold"),
                fg="#ff6b6b",
                bg="white"
            ).pack(anchor=tk.W, pady=(5, 10))
            
            # Order button
            order_btn = tk.Button(
                cake_card,
                text="Order Now",
                command=lambda c=cake: self.order_cake(c),
                bg="#667eea",
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                padx=10
            )
            order_btn.pack()
            
            # Update column and row for grid
            col += 1
            if col > 2:  # 3 columns per row
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            self.customer_cakes_frame.columnconfigure(i, weight=1)
    
    def render_customer_orders(self):
        # Clear existing widgets
        for widget in self.customer_orders_frame.winfo_children():
            widget.destroy()
        
        # Get customer orders from database
        orders = self.db.get_orders(user_id=self.current_user_id, user_role=self.current_role)
        active_orders = [order for order in orders if order[5] not in ["completed", "cancelled"]]
        
        if not active_orders:
            tk.Label(
                self.customer_orders_frame,
                text="No current orders. Browse our cakes and place an order!",
                font=("Arial", 11),
                bg="white"
            ).pack(pady=10)
            return
        
        # Display customer orders
        for order in active_orders:
            order_frame = tk.Frame(
                self.customer_orders_frame,
                bg="white",
                relief=tk.RAISED,
                bd=1,
                padx=10,
                pady=10
            )
            order_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(
                order_frame,
                text=f"Order #{order[0]}",
                font=("Arial", 11, "bold"),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                order_frame,
                text=f"Cake: {self.get_cake_name(order[3])}",  # cake_id -> name
                font=("Arial", 10),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                order_frame,
                text=f"Quantity: {order[4]}",  # quantity
                font=("Arial", 10),
                bg="white"
            ).pack(anchor=tk.W)
            
            status_text = order[5].capitalize()  # status
            status_color = self.get_status_color(order[5])
            
            status_label = tk.Label(
                order_frame,
                text=f"Status: {status_text}",
                font=("Arial", 10, "bold"),
                bg=status_color,
                fg="white",
                padx=5,
                pady=2
            )
            status_label.pack(anchor=tk.W, pady=(5, 0))
            
            tk.Label(
                order_frame,
                text=f"Total: ${order[5]:.2f}",  # total_price
                font=("Arial", 10),
                bg="white"
            ).pack(anchor=tk.W)
            
            tk.Label(
                order_frame,
                text=f"Order Date: {order[7].split('T')[0] if order[7] else ''}",  # order_date
                font=("Arial", 10),
                bg="white"
            ).pack(anchor=tk.W)
            
            # Cancel button for pending orders
            if order[5] == "pending":
                cancel_btn = tk.Button(
                    order_frame,
                    text="Cancel Order",
                    command=lambda o=order: self.cancel_order(o),
                    bg="#ff6b6b",
                    fg="white",
                    font=("Arial", 10, "bold"),
                    relief=tk.FLAT,
                    padx=10
                )
                cancel_btn.pack(anchor=tk.E, pady=(5, 0))
    
    def render_order_history(self):
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Get customer orders from database
        orders = self.db.get_orders(user_id=self.current_user_id, user_role=self.current_role)
        
        # Add orders to treeview
        for order in orders:
            status_text = order[5].capitalize()  # status
            self.history_tree.insert("", "end", values=(
                order[7].split('T')[0] if order[7] else "",  # order_date
                self.get_cake_name(order[3]),  # cake_id -> name
                order[4],  # quantity
                status_text,
                f"${order[5]:.2f}"  # total_price
            ))
    
    def show_register_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Customer Registration")
        modal.geometry("400x500")
        modal.configure(bg="white")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text="Customer Registration",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        # Full Name
        tk.Label(
            modal,
            text="Full Name:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        name_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        name_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Username
        tk.Label(
            modal,
            text="Username:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        username_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        username_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Password
        tk.Label(
            modal,
            text="Password:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        password_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1,
            show="*"
        )
        password_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Confirm Password
        tk.Label(
            modal,
            text="Confirm Password:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        confirm_password_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1,
            show="*"
        )
        confirm_password_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Email
        tk.Label(
            modal,
            text="Email:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        email_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        email_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Phone
        tk.Label(
            modal,
            text="Phone:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        phone_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        phone_entry.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Register Button
        register_btn = tk.Button(
            modal,
            text="Register",
            command=lambda: self.register_customer(
                name_entry.get(),
                username_entry.get(),
                password_entry.get(),
                confirm_password_entry.get(),
                email_entry.get(),
                phone_entry.get(),
                modal
            ),
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        register_btn.pack(pady=(0, 20))
    
    def register_customer(self, name, username, password, confirm_password, email, phone, modal):
        # Validate inputs
        if not all([name, username, password, confirm_password, email, phone]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        
        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address.")
            return
        
        # Check if username already exists
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            messagebox.showerror("Error", "Username already exists. Please choose a different one.")
            return
        
        # Hash password
        hashed_password = self.db.hash_password(password)
        
        # Insert new customer
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role, name, email, phone) VALUES (?, ?, 'customer', ?, ?, ?)",
                (username, hashed_password, name, email, phone)
            )
            self.db.conn.commit()
            modal.destroy()
            messagebox.showinfo("Success", "Registration successful! You can now login.")
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")
    
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def show_add_cake_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Add New Cake")
        modal.geometry("400x600")
        modal.configure(bg="white")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text="Add New Cake",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        # Cake Name
        tk.Label(
            modal,
            text="Cake Name:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        cake_name_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        cake_name_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Flavor
        tk.Label(
            modal,
            text="Flavor:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        flavor_var = tk.StringVar(value="chocolate")
        flavor_combo = ttk.Combobox(
            modal,
            textvariable=flavor_var,
            values=["chocolate", "vanilla", "strawberry", "red-velvet", "carrot", "lemon", "cheesecake"],
            state="readonly",
            font=("Arial", 12)
        )
        flavor_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Size
        tk.Label(
            modal,
            text="Size:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        size_var = tk.StringVar(value="medium")
        size_combo = ttk.Combobox(
            modal,
            textvariable=size_var,
            values=["small", "medium", "large", "extra-large"],
            state="readonly",
            font=("Arial", 12)
        )
        size_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Category
        tk.Label(
            modal,
            text="Category:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        category_var = tk.StringVar(value="regular")
        category_combo = ttk.Combobox(
            modal,
            textvariable=category_var,
            values=["birthday", "wedding", "anniversary", "celebration", "regular"],
            state="readonly",
            font=("Arial", 12)
        )
        category_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Price
        tk.Label(
            modal,
            text="Price:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        price_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        price_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Stock Quantity
        tk.Label(
            modal,
            text="Stock Quantity:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        stock_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        stock_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Description
        tk.Label(
            modal,
            text="Description:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        description_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        description_entry.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Add Button
        add_btn = tk.Button(
            modal,
            text="Add Cake",
            command=lambda: self.add_cake(
                cake_name_entry.get(),
                flavor_var.get(),
                size_var.get(),
                category_var.get(),
                price_entry.get(),
                stock_entry.get(),
                description_entry.get(),
                modal
            ),
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        add_btn.pack(pady=(0, 20))
    
    def add_cake(self, name, flavor, size, category, price, stock, description, modal):
        if not name or not price or not stock:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return
        
        try:
            price_val = float(price)
            stock_val = int(stock)
            
            if price_val <= 0 or stock_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter valid price and stock values.")
            return
        
        # Insert into database
        cursor = self.db.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO cakes (name, flavor, size, price, stock, description, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, flavor, size, price_val, stock_val, description, category)
            )
            self.db.conn.commit()
            modal.destroy()
            self.render_admin_cakes()
            messagebox.showinfo("Success", "Cake added successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add cake: {str(e)}")
    
    def edit_cake(self, cake):
        # For simplicity, we'll remove the old cake and open the add modal with pre-filled values
        # In a real application, we would create an edit modal
        messagebox.showinfo("Info", "Edit functionality would be implemented here.")
    
    def delete_cake(self, cake):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this cake?"):
            cursor = self.db.conn.cursor()
            try:
                cursor.execute("DELETE FROM cakes WHERE id = ?", (cake[0],))
                self.db.conn.commit()
                self.render_admin_cakes()
                messagebox.showinfo("Success", "Cake deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete cake: {str(e)}")
    
    def update_stats_display(self):
        # Get today's date
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Get sales data
        sales_data = self.db.get_sales_report(today, today)
        
        # Calculate totals
        total_orders = 0
        total_revenue = 0
        for data in sales_data:
            total_orders += data[0]  # total_orders
            total_revenue += data[1] if data[1] else 0  # total_revenue
        
        # Get popular items
        popular_items = self.db.get_popular_items(today, today)
        
        # Format stats text
        stats_text = f"Today's Stats:\n\n"
        stats_text += f"Total Orders: {total_orders}\n"
        stats_text += f"Total Revenue: ${total_revenue:.2f}\n"
        
        if popular_items:
            stats_text += f"Most Popular: {popular_items[0][0]}\n"
        
        # Get low stock items
        low_stock = self.db.get_low_stock_items()
        if low_stock:
            stats_text += f"\nLow Stock Alert: {len(low_stock)} items need restocking"
        
        self.stats_display.config(text=stats_text)
    
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
        
        # Get sales data
        sales_data = self.db.get_sales_report(start_date_str, end_date_str)
        popular_items = self.db.get_popular_items(start_date_str, end_date_str)
        
        # Calculate totals
        total_orders = 0
        total_revenue = 0
        status_counts = {}
        
        for data in sales_data:
            total_orders += data[0]  # total_orders
            total_revenue += data[1] if data[1] else 0  # total_revenue
            status_counts[data[3]] = data[0]  # status count
        
        # Format report text
        report_text = f"{period_text} Report ({start_date_str} to {end_date_str})\n\n"
        report_text += f"Total Orders: {total_orders}\n"
        report_text += f"Total Revenue: ${total_revenue:.2f}\n"
        report_text += f"Average Order Value: ${total_revenue/total_orders:.2f}\n\n" if total_orders > 0 else "\n"
        
        report_text += "Order Status:\n"
        for status, count in status_counts.items():
            report_text += f"  {status.capitalize()}: {count}\n"
        
        if popular_items:
            report_text += f"\nMost Popular Item: {popular_items[0][0]}\n"
            report_text += f"Revenue from Top Item: ${popular_items[0][5]:.2f}\n"
        
        self.report_display.config(text=report_text)
    
    def generate_custom_report(self):
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        
        if not start_date or not end_date:
            messagebox.showerror("Error", "Please enter both start and end dates.")
            return
        
        # Validate dates
        try:
            datetime.datetime.strptime(start_date, "%Y-%m-%d")
            datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Please enter dates in YYYY-MM-DD format.")
            return
        
        # Get sales data
        sales_data = self.db.get_sales_report(start_date, end_date)
        popular_items = self.db.get_popular_items(start_date, end_date)
        
        # Calculate totals
        total_orders = 0
        total_revenue = 0
        status_counts = {}
        
        for data in sales_data:
            total_orders += data[0]  # total_orders
            total_revenue += data[1] if data[1] else 0  # total_revenue
            status_counts[data[3]] = data[0]  # status count
        
        # Format report text
        report_text = f"Custom Report ({start_date} to {end_date})\n\n"
        report_text += f"Total Orders: {total_orders}\n"
        report_text += f"Total Revenue: ${total_revenue:.2f}\n"
        
        if total_orders > 0:
            report_text += f"Average Order Value: ${total_revenue/total_orders:.2f}\n\n"
        else:
            report_text += "\n"
        
        report_text += "Order Status:\n"
        for status, count in status_counts.items():
            report_text += f"  {status.capitalize()}: {count}\n"
        
        if popular_items:
            report_text += f"\nMost Popular Item: {popular_items[0][0]}\n"
            report_text += f"Revenue from Top Item: ${popular_items[0][5]:.2f}\n"
        
        self.report_display.config(text=report_text)
    
    def export_report_pdf(self):
        # Get the current report text
        report_text = self.report_display.cget("text")
        
        if report_text == "Select a report to generate...":
            messagebox.showerror("Error", "Please generate a report first.")
            return
        
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Report As"
        )
        
        if not file_path:
            return
        
        # Create PDF
        try:
            c = canvas.Canvas(file_path, pagesize=letter)
            c.setFont("Helvetica", 12)
            
            # Split text into lines and add to PDF
            y = 750
            for line in report_text.split('\n'):
                c.drawString(50, y, line)
                y -= 15
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = 750
            
            c.save()
            messagebox.showinfo("Success", f"Report exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")
    
    def show_add_staff_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Add Staff Member")
        modal.geometry("400x500")
        modal.configure(bg="white")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text="Add Staff Member",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        # Full Name
        tk.Label(
            modal,
            text="Full Name:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        name_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        name_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Username
        tk.Label(
            modal,
            text="Username:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        username_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        username_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Password
        tk.Label(
            modal,
            text="Password:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        password_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1,
            show="*"
        )
        password_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Email
        tk.Label(
            modal,
            text="Email:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        email_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        email_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Position
        tk.Label(
            modal,
            text="Position:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        position_var = tk.StringVar(value="baker")
        position_combo = ttk.Combobox(
            modal,
            textvariable=position_var,
            values=["baker", "decorator", "cashier", "manager"],
            state="readonly",
            font=("Arial", 12)
        )
        position_combo.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Add Button
        add_btn = tk.Button(
            modal,
            text="Add Staff",
            command=lambda: self.add_staff(
                name_entry.get(),
                username_entry.get(),
                password_entry.get(),
                email_entry.get(),
                position_var.get(),
                modal
            ),
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        add_btn.pack(pady=(0, 20))
    
    def add_staff(self, name, username, password, email, position, modal):
        if not all([name, username, password, email, position]):
            messagebox.showerror("Error", "Please fill in all required fields.")
            return
        
        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address.")
            return
        
        # Check if username already exists
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            messagebox.showerror("Error", "Username already exists. Please choose a different one.")
            return
        
        # Hash password
        hashed_password = self.db.hash_password(password)
        
        # Insert new staff
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role, name, email) VALUES (?, ?, 'staff', ?, ?)",
                (username, hashed_password, name, email)
            )
            user_id = cursor.lastrowid
            
            # Add to staff table
            hire_date = datetime.datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO staff (user_id, position, hire_date) VALUES (?, ?, ?)",
                (user_id, position, hire_date)
            )
            
            self.db.conn.commit()
            modal.destroy()
            self.render_staff_list()
            messagebox.showinfo("Success", "Staff member added successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add staff: {str(e)}")
    
    def show_inventory_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Inventory Management")
        modal.geometry("600x500")
        modal.configure(bg="white")
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text="Inventory Management",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        # Create a treeview for inventory
        columns = ("id", "item", "category", "quantity", "unit", "min_stock")
        tree = ttk.Treeview(
            modal, 
            columns=columns, 
            show="headings",
            height=15
        )
        
        tree.heading("id", text="ID")
        tree.heading("item", text="Item")
        tree.heading("category", text="Category")
        tree.heading("quantity", text="Quantity")
        tree.heading("unit", text="Unit")
        tree.heading("min_stock", text="Min Stock")
        
        tree.column("id", width=50)
        tree.column("item", width=150)
        tree.column("category", width=100)
        tree.column("quantity", width=80)
        tree.column("unit", width=60)
        tree.column("min_stock", width=80)
        
        # Add scrollbar to treeview
        tree_scroll = ttk.Scrollbar(modal, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Load inventory data
        inventory = self.db.get_inventory()
        for item in inventory:
            tree.insert("", "end", values=(
                item[0],  # id
                item[1],  # item_name
                item[2],  # category
                f"{item[3]:.1f}",  # quantity
                item[4],  # unit
                f"{item[5]:.1f}"  # min_stock_level
            ))
        
        # Edit button
        btn_frame = tk.Frame(modal, bg="white")
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        edit_btn = tk.Button(
            btn_frame,
            text="Edit Selected",
            command=lambda: self.edit_inventory_item(tree),
            bg="#feca57",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(
            btn_frame,
            text="Close",
            command=modal.destroy,
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
    
    def edit_inventory_item(self, tree):
        selection = tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select an item to edit.")
            return
        
        item_id = tree.item(selection[0], "values")[0]
        current_qty = tree.item(selection[0], "values")[3]
        
        # Create edit modal
        edit_modal = tk.Toplevel(self.root)
        edit_modal.title("Edit Inventory Item")
        edit_modal.geometry("300x200")
        edit_modal.configure(bg="white")
        edit_modal.transient(self.root)
        edit_modal.grab_set()
        
        # Center the modal
        edit_modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - edit_modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - edit_modal.winfo_height()) // 2
        edit_modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            edit_modal,
            text="Edit Inventory Quantity",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        tk.Label(
            edit_modal,
            text=f"Current Quantity: {current_qty}",
            font=("Arial", 11),
            bg="white"
        ).pack(pady=(0, 10))
        
        tk.Label(
            edit_modal,
            text="New Quantity:",
            font=("Arial", 11),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        qty_entry = tk.Entry(
            edit_modal,
            font=("Arial", 11),
            relief=tk.SOLID,
            bd=1
        )
        qty_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        qty_entry.insert(0, current_qty)
        
        # Update button
        update_btn = tk.Button(
            edit_modal,
            text="Update",
            command=lambda: self.update_inventory_item(item_id, qty_entry.get(), edit_modal),
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=5
        )
        update_btn.pack(pady=(10, 20))
    
    def update_inventory_item(self, item_id, quantity, modal):
        try:
            qty_val = float(quantity)
            if qty_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return
        
        try:
            self.db.update_inventory(item_id, qty_val)
            modal.destroy()
            messagebox.showinfo("Success", "Inventory updated successfully!")
            if self.current_role == "staff":
                self.update_inventory_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update inventory: {str(e)}")
    
    def show_add_inventory_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Add Inventory Item")
        modal.geometry("400x400")
        modal.configure(bg="white")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text="Add Inventory Item",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        # Item Name
        tk.Label(
            modal,
            text="Item Name:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        name_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        name_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Category
        tk.Label(
            modal,
            text="Category:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        category_var = tk.StringVar(value="baking")
        category_combo = ttk.Combobox(
            modal,
            textvariable=category_var,
            values=["baking", "dairy", "flavoring", "decorations", "packaging"],
            state="readonly",
            font=("Arial", 12)
        )
        category_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Quantity
        tk.Label(
            modal,
            text="Quantity:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        qty_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        qty_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Unit
        tk.Label(
            modal,
            text="Unit:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        unit_var = tk.StringVar(value="lbs")
        unit_combo = ttk.Combobox(
            modal,
            textvariable=unit_var,
            values=["lbs", "kg", "pieces", "liters", "packets"],
            state="readonly",
            font=("Arial", 12)
        )
        unit_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Minimum Stock Level
        tk.Label(
            modal,
            text="Minimum Stock Level:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        min_stock_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        min_stock_entry.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Add Button
        add_btn = tk.Button(
            modal,
            text="Add Item",
            command=lambda: self.add_inventory_item(
                name_entry.get(),
                category_var.get(),
                qty_entry.get(),
                unit_var.get(),
                min_stock_entry.get(),
                modal
            ),
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        add_btn.pack(pady=(0, 20))
    
    def add_inventory_item(self, name, category, quantity, unit, min_stock, modal):
        if not all([name, category, quantity, unit, min_stock]):
            messagebox.showerror("Error", "Please fill in all required fields.")
            return
        
        try:
            qty_val = float(quantity)
            min_stock_val = float(min_stock)
            if qty_val < 0 or min_stock_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter valid quantity and minimum stock values.")
            return
        
        try:
            self.db.add_inventory_item(name, category, qty_val, unit, min_stock_val)
            modal.destroy()
            messagebox.showinfo("Success", "Inventory item added successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add inventory item: {str(e)}")
    
    def show_low_stock_modal(self):
        low_stock_items = self.db.get_low_stock_items()
        
        if not low_stock_items:
            messagebox.showinfo("Info", "No items are below minimum stock levels.")
            return
        
        modal = tk.Toplevel(self.root)
        modal.title("Low Stock Alert")
        modal.geometry("500x300")
        modal.configure(bg="white")
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text="Low Stock Alert",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#ff6b6b"
        ).pack(pady=(20, 10))
        
        # Create a treeview for low stock items
        columns = ("item", "category", "quantity", "unit", "min_stock")
        tree = ttk.Treeview(
            modal, 
            columns=columns, 
            show="headings",
            height=10
        )
        
        tree.heading("item", text="Item")
        tree.heading("category", text="Category")
        tree.heading("quantity", text="Quantity")
        tree.heading("unit", text="Unit")
        tree.heading("min_stock", text="Min Stock")
        
        tree.column("item", width=150)
        tree.column("category", width=100)
        tree.column("quantity", width=80)
        tree.column("unit", width=60)
        tree.column("min_stock", width=80)
        
        # Add scrollbar to treeview
        tree_scroll = ttk.Scrollbar(modal, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Load low stock data
        for item in low_stock_items:
            tree.insert("", "end", values=(
                item[1],  # item_name
                item[2],  # category
                f"{item[3]:.1f}",  # quantity
                item[4],  # unit
                f"{item[5]:.1f}"  # min_stock_level
            ))
        
        # Close button
        close_btn = tk.Button(
            modal,
            text="Close",
            command=modal.destroy,
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20
        )
        close_btn.pack(pady=(0, 20))
    
    def update_inventory_display(self):
        inventory = self.db.get_inventory()
        
        # Format inventory text
        inventory_text = "Current Inventory:\n\n"
        for item in inventory[:5]:  # Show first 5 items
            inventory_text += f"{item[1]}: {item[3]:.1f} {item[4]}\n"
        
        if len(inventory) > 5:
            inventory_text += f"\n... and {len(inventory) - 5} more items"
        
        # Check for low stock
        low_stock = self.db.get_low_stock_items()
        if low_stock:
            inventory_text += f"\n\n⚠️ Low Stock Alert: {len(low_stock)} items need restocking"
        
        self.inventory_display.config(text=inventory_text)
    
    def accept_order(self, order):
        self.db.update_order_status(order[0], "preparing", "Order accepted by staff")
        self.render_incoming_orders()
        self.render_order_management()
        
        # Send notification email
        if order[13]:  # email
            subject = f"Sweet Dreams Bakery - Order #{order[0]} Accepted"
            body = f"Dear {order[2]},\n\nYour order #{order[0]} has been accepted and is now being prepared.\n\nThank you for choosing Sweet Dreams Bakery!"
            self.email_service.send_email(order[13], subject, body)
        
        messagebox.showinfo("Success", f"Order #{order[0]} has been accepted and moved to preparation.")
    
    def decline_order(self, order):
        if messagebox.askyesno("Confirm", "Are you sure you want to decline this order?"):
            self.db.update_order_status(order[0], "cancelled", "Order declined by staff")
            self.render_incoming_orders()
            self.render_order_management()
            
            # Send notification email
            if order[13]:  # email
                subject = f"Sweet Dreams Bakery - Order #{order[0]} Cancelled"
                body = f"Dear {order[2]},\n\nWe regret to inform you that your order #{order[0]} has been cancelled.\n\nPlease contact us if you have any questions."
                self.email_service.send_email(order[13], subject, body)
            
            messagebox.showinfo("Success", f"Order #{order[0]} has been declined and cancelled.")
    
    def update_order_status(self, order, new_status):
        self.db.update_order_status(order[0], new_status, f"Status changed by {self.current_role}")
        self.render_order_management()
        if self.current_role == "admin":
            self.render_all_orders()
        
        # Send notification email for important status changes
        if new_status in ["ready", "completed"] and order[13]:  # email
            subject = f"Sweet Dreams Bakery - Order #{order[0]} Status Update"
            body = f"Dear {order[2]},\n\nYour order #{order[0]} status has been updated to: {new_status}\n\nThank you for choosing Sweet Dreams Bakery!"
            self.email_service.send_email(order[13], subject, body)
        
        messagebox.showinfo("Success", f"Order #{order[0]} status updated to: {new_status}")
    
    def notify_customer(self, order):
        if order[13]:  # email
            subject = f"Sweet Dreams Bakery - Order #{order[0]} Notification"
            body = f"Dear {order[2]},\n\nThis is a notification about your order #{order[0]}.\n\nCurrent status: {order[5]}\n\nThank you for choosing Sweet Dreams Bakery!"
            if self.email_service.send_email(order[13], subject, body):
                messagebox.showinfo("Notification", f"Customer {order[2]} has been notified via email.")
            else:
                messagebox.showerror("Error", "Failed to send email notification.")
        else:
            messagebox.showinfo("Notification", f"Customer {order[2]} would be notified about Order #{order[0]} status: {order[5]}")
    
    def cancel_order(self, order):
        if messagebox.askyesno("Confirm", "Are you sure you want to cancel this order?"):
            self.db.update_order_status(order[0], "cancelled", "Cancelled by customer")
            self.render_customer_orders()
            self.render_order_history()
            messagebox.showinfo("Success", f"Order #{order[0]} has been cancelled.")
    
    def show_walkin_order_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Record Walk-in Order")
        modal.geometry("500x600")
        modal.configure(bg="white")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text="Record Walk-in Order",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        # Customer Name
        tk.Label(
            modal,
            text="Customer Name:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        name_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        name_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Phone
        tk.Label(
            modal,
            text="Phone:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        phone_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        phone_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Email
        tk.Label(
            modal,
            text="Email (optional):",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        email_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        email_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Cake selection
        tk.Label(
            modal,
            text="Select Cake:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        # Get available cakes
        cakes = self.db.get_cakes()
        cake_options = [f"{cake[1]} - ${cake[4]:.2f}" for cake in cakes]
        
        cake_var = tk.StringVar(value=cake_options[0] if cake_options else "")
        cake_combo = ttk.Combobox(
            modal,
            textvariable=cake_var,
            values=cake_options,
            state="readonly",
            font=("Arial", 12)
        )
        cake_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Quantity
        tk.Label(
            modal,
            text="Quantity:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        qty_var = tk.StringVar(value="1")
        qty_combo = ttk.Combobox(
            modal,
            textvariable=qty_var,
            values=["1", "2", "3", "4", "5"],
            state="readonly",
            font=("Arial", 12)
        )
        qty_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Special Instructions
        tk.Label(
            modal,
            text="Special Instructions:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        message_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        message_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Delivery Type
        tk.Label(
            modal,
            text="Service Type:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        service_var = tk.StringVar(value="pickup")
        service_combo = ttk.Combobox(
            modal,
            textvariable=service_var,
            values=["pickup", "delivery"],
            state="readonly",
            font=("Arial", 12)
        )
        service_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Delivery Address (only show if delivery is selected)
        address_frame = tk.Frame(modal, bg="white")
        address_frame.pack(fill=tk.X, padx=20, pady=(5, 5))
        
        tk.Label(
            address_frame,
            text="Delivery Address:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W)
        
        address_entry = tk.Entry(
            address_frame,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        address_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Show/hide address based on service type
        def toggle_address(*args):
            if service_var.get() == "delivery":
                address_frame.pack(fill=tk.X, padx=20, pady=(5, 5))
            else:
                address_frame.pack_forget()
        
        service_var.trace("w", toggle_address)
        toggle_address()  # Initial call
        
        # Record Button
        record_btn = tk.Button(
            modal,
            text="Record Order",
            command=lambda: self.record_walkin_order(
                name_entry.get(),
                phone_entry.get(),
                email_entry.get(),
                cake_var.get(),
                qty_var.get(),
                message_entry.get(),
                service_var.get(),
                address_entry.get(),
                modal
            ),
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        record_btn.pack(pady=(20, 20))
    
    def record_walkin_order(self, name, phone, email, cake, quantity, message, service, address, modal):
        if not name or not phone or not cake:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return
        
        if service == "delivery" and not address:
            messagebox.showerror("Error", "Please provide a delivery address.")
            return
        
        try:
            qty_val = int(quantity)
            if qty_val <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return
        
        # Extract cake ID from the selected option
        cake_name = cake.split(" - $")[0]
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, price FROM cakes WHERE name = ?", (cake_name,))
        cake_data = cursor.fetchone()
        
        if not cake_data:
            messagebox.showerror("Error", "Selected cake not found.")
            return
        
        cake_id, cake_price = cake_data
        total_price = cake_price * qty_val
        
        # Add delivery fee if applicable
        if service == "delivery":
            total_price += 5  # $5 delivery fee
        
        # Create order
        order_id = self.db.create_order(
            customer_id=None,  # No user account
            customer_name=name,
            cake_id=cake_id,
            quantity=qty_val,
            total_price=total_price,
            status="pending",
            special_instructions=message,
            delivery_type=service,
            delivery_date=datetime.datetime.now().isoformat(),
            address=address,
            phone=phone,
            email=email
        )
        
        # Update cake stock
        self.db.update_cake_stock(cake_id, qty_val)
        
        modal.destroy()
        
        if self.current_role == "staff":
            self.render_incoming_orders()
        
        messagebox.showinfo("Success", f"Walk-in order recorded successfully! Order #{order_id}\nTotal: ${total_price:.2f}")
    
    def order_cake(self, cake):
        modal = tk.Toplevel(self.root)
        modal.title(f"Order {cake[1]}")  # name
        modal.geometry("500x600")
        modal.configure(bg="white")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text=f"Order: {cake[1]}",  # name
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        # Quantity
        tk.Label(
            modal,
            text="Quantity:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        qty_var = tk.StringVar(value="1")
        qty_combo = ttk.Combobox(
            modal,
            textvariable=qty_var,
            values=["1", "2", "3"],
            state="readonly",
            font=("Arial", 12)
        )
        qty_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Special Message
        tk.Label(
            modal,
            text="Special Message:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        message_entry = tk.Entry(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        message_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Design Request
        tk.Label(
            modal,
            text="Design Request:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        design_text = tk.Text(
            modal,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1,
            height=4
        )
        design_text.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Pickup/Delivery Date
        tk.Label(
            modal,
            text="Pickup/Delivery Date:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        # Create a frame for date and time entries
        date_frame = tk.Frame(modal, bg="white")
        date_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Date entry
        today = datetime.datetime.now()
        date_var = tk.StringVar(value=today.strftime("%Y-%m-%d"))
        date_entry = tk.Entry(
            date_frame,
            textvariable=date_var,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1,
            width=12
        )
        date_entry.pack(side=tk.LEFT)
        
        # Time entry
        time_var = tk.StringVar(value="12:00")
        time_entry = tk.Entry(
            date_frame,
            textvariable=time_var,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1,
            width=8
        )
        time_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Service Type
        tk.Label(
            modal,
            text="Service Type:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        service_var = tk.StringVar(value="pickup")
        service_combo = ttk.Combobox(
            modal,
            textvariable=service_var,
            values=["pickup", "delivery"],
            state="readonly",
            font=("Arial", 12)
        )
        service_combo.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Delivery Address (only show if delivery is selected)
        address_frame = tk.Frame(modal, bg="white")
        address_frame.pack(fill=tk.X, padx=20, pady=(5, 5))
        
        tk.Label(
            address_frame,
            text="Delivery Address:",
            font=("Arial", 12),
            bg="white"
        ).pack(anchor=tk.W)
        
        address_entry = tk.Entry(
            address_frame,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        address_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Show/hide address based on service type
        def toggle_address(*args):
            if service_var.get() == "delivery":
                address_frame.pack(fill=tk.X, padx=20, pady=(5, 5))
            else:
                address_frame.pack_forget()
        
        service_var.trace("w", toggle_address)
        toggle_address()  # Initial call
        
        # Price display
        price_frame = tk.Frame(modal, bg="white")
        price_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        tk.Label(
            price_frame,
            text="Base Price:",
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(side=tk.LEFT)
        
        tk.Label(
            price_frame,
            text=f"${cake[4]:.2f}",  # price
            font=("Arial", 12),
            bg="white"
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Delivery fee label (will be updated)
        delivery_label = tk.Label(
            price_frame,
            text="",
            font=("Arial", 12),
            bg="white",
            fg="green"
        )
        delivery_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Total price label (will be updated)
        total_label = tk.Label(
            price_frame,
            text=f"Total: ${cake[4]:.2f}",  # initial total
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#ff6b6b"
        )
        total_label.pack(side=tk.RIGHT)
        
        # Update prices when quantity or service type changes
        def update_prices(*args):
            try:
                qty = int(qty_var.get())
                base_price = cake[4] * qty
                delivery_fee = 5 if service_var.get() == "delivery" else 0
                total = base_price + delivery_fee
                
                if delivery_fee > 0:
                    delivery_label.config(text=f"+ ${delivery_fee:.2f} delivery")
                else:
                    delivery_label.config(text="")
                
                total_label.config(text=f"Total: ${total:.2f}")
            except:
                pass
        
        qty_var.trace("w", update_prices)
        service_var.trace("w", update_prices)
        update_prices()  # Initial call
        
        # Confirm Button
        confirm_btn = tk.Button(
            modal,
            text="Confirm Order",
            command=lambda: self.confirm_order(
                cake,
                int(qty_var.get()),
                message_entry.get(),
                design_text.get("1.0", tk.END).strip(),
                f"{date_var.get()} {time_var.get()}",
                service_var.get(),
                address_entry.get(),
                modal
            ),
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        confirm_btn.pack(pady=(20, 20))
    
    def confirm_order(self, cake, quantity, message, design, delivery, service, address, modal):
        if not delivery:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return
        
        if service == "delivery" and not address:
            messagebox.showerror("Error", "Please provide a delivery address.")
            return
        
        # Calculate total price
        base_price = cake[4] * quantity
        delivery_fee = 5 if service == "delivery" else 0
        total = base_price + delivery_fee
        
        # Get user info
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT email, phone FROM users WHERE id = ?", (self.current_user_id,))
        user_info = cursor.fetchone()
        email = user_info[0] if user_info else None
        phone = user_info[1] if user_info else None
        
        # Create order
        order_id = self.db.create_order(
            customer_id=self.current_user_id,
            customer_name=self.current_user_name,
            cake_id=cake[0],
            quantity=quantity,
            total_price=total,
            status="pending",
            special_instructions=f"{message}\n\nDesign: {design}",
            delivery_type=service,
            delivery_date=delivery,
            address=address,
            phone=phone,
            email=email
        )
        
        # Update cake stock
        self.db.update_cake_stock(cake[0], quantity)
        
        modal.destroy()
        
        self.render_customer_orders()
        self.render_customer_cakes()
        self.render_order_history()
        
        # Send confirmation email
        if email:
            subject = f"Sweet Dreams Bakery - Order Confirmation #{order_id}"
            body = f"Dear {self.current_user_name},\n\nThank you for your order!\n\nOrder Details:\n- Cake: {cake[1]}\n- Quantity: {quantity}\n- Total: ${total:.2f}\n- Delivery Type: {service}\n- Expected Date: {delivery}\n\nWe will notify you when your order status changes.\n\nThank you for choosing Sweet Dreams Bakery!"
            self.email_service.send_email(email, subject, body)
        
        messagebox.showinfo("Success", f"Order placed successfully! Order #{order_id}\nTotal: ${total:.2f}")
    
    def show_order_details(self, event):
        selection = self.orders_tree.selection()
        if not selection:
            return
        
        order_id = self.orders_tree.item(selection[0], "values")[0].replace("#", "")
        
        # Get order details from database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return
        
        # Get order history
        history = self.db.get_order_history(order_id)
        
        # Create details modal
        modal = tk.Toplevel(self.root)
        modal.title(f"Order Details #{order_id}")
        modal.geometry("500x400")
        modal.configure(bg="white")
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text=f"Order Details #{order_id}",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        # Create a text widget for details
        details_text = tk.Text(
            modal,
            font=("Arial", 11),
            relief=tk.SOLID,
            bd=1,
            height=15,
            width=50
        )
        details_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Add order details
        details_text.insert(tk.END, f"Customer: {order[2]}\n")
        details_text.insert(tk.END, f"Cake: {self.get_cake_name(order[3])}\n")
        details_text.insert(tk.END, f"Quantity: {order[4]}\n")
        details_text.insert(tk.END, f"Total: ${order[5]:.2f}\n")
        details_text.insert(tk.END, f"Status: {order[6]}\n")
        details_text.insert(tk.END, f"Order Date: {order[7].split('T')[0] if order[7] else ''}\n")
        details_text.insert(tk.END, f"Delivery Date: {order[9] if order[9] else 'N/A'}\n")
        details_text.insert(tk.END, f"Delivery Type: {order[10]}\n")
        
        if order[11]:  # special instructions
            details_text.insert(tk.END, f"\nSpecial Instructions:\n{order[11]}\n")
        
        details_text.insert(tk.END, f"\nStatus History:\n")
        for record in history:
            details_text.insert(tk.END, f"- {record[2]} on {record[3].split('T')[0]}\n")
            if record[4]:  # notes
                details_text.insert(tk.END, f"  Notes: {record[4]}\n")
        
        details_text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = tk.Button(
            modal,
            text="Close",
            command=modal.destroy,
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20
        )
        close_btn.pack(pady=(0, 20))
    
    def show_customer_order_details(self, event):
        selection = self.history_tree.selection()
        if not selection:
            return
        
        order_date = self.history_tree.item(selection[0], "values")[0]
        cake_name = self.history_tree.item(selection[0], "values")[1]
        
        # Get order details from database
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT * FROM orders WHERE customer_id = ? AND order_date LIKE ? AND cake_id IN (SELECT id FROM cakes WHERE name = ?)",
            (self.current_user_id, f"{order_date}%", cake_name)
        )
        order = cursor.fetchone()
        
        if not order:
            return
        
        # Get order history
        history = self.db.get_order_history(order[0])
        
        # Create details modal
        modal = tk.Toplevel(self.root)
        modal.title(f"Order Details #{order[0]}")
        modal.geometry("500x400")
        modal.configure(bg="white")
        modal.transient(self.root)
        modal.grab_set()
        
        # Center the modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - modal.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{x}+{y}")
        
        tk.Label(
            modal,
            text=f"Order Details #{order[0]}",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=(20, 10))
        
        # Create a text widget for details
        details_text = tk.Text(
            modal,
            font=("Arial", 11),
            relief=tk.SOLID,
            bd=1,
            height=15,
            width=50
        )
        details_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Add order details
        details_text.insert(tk.END, f"Customer: {order[2]}\n")
        details_text.insert(tk.END, f"Cake: {self.get_cake_name(order[3])}\n")
        details_text.insert(tk.END, f"Quantity: {order[4]}\n")
        details_text.insert(tk.END, f"Total: ${order[5]:.2f}\n")
        details_text.insert(tk.END, f"Status: {order[6]}\n")
        details_text.insert(tk.END, f"Order Date: {order[7].split('T')[0] if order[7] else ''}\n")
        details_text.insert(tk.END, f"Delivery Date: {order[9] if order[9] else 'N/A'}\n")
        details_text.insert(tk.END, f"Delivery Type: {order[10]}\n")
        
        if order[11]:  # special instructions
            details_text.insert(tk.END, f"\nSpecial Instructions:\n{order[11]}\n")
        
        details_text.insert(tk.END, f"\nStatus History:\n")
        for record in history:
            details_text.insert(tk.END, f"- {record[2]} on {record[3].split('T')[0]}\n")
            if record[4]:  # notes
                details_text.insert(tk.END, f"  Notes: {record[4]}\n")
        
        details_text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = tk.Button(
            modal,
            text="Close",
            command=modal.destroy,
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20
        )
        close_btn.pack(pady=(0, 20))
    
    def filter_cakes(self, event=None):
        self.render_admin_cakes()
    
    def filter_customer_cakes(self, event=None):
        self.render_customer_cakes()
    
    def filter_orders(self, event=None):
        self.render_all_orders()
    
    def get_cake_name(self, cake_id):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM cakes WHERE id = ?", (cake_id,))
        result = cursor.fetchone()
        return result[0] if result else "Unknown Cake"
    
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
    
    def get_status_color(self, status):
        color_map = {
            "pending": "#ffeaa7",
            "preparing": "#74b9ff",
            "ready": "#00b894",
            "completed": "#6c5ce7",
            "cancelled": "#ff6b6b"
        }
        return color_map.get(status, "#dfe6e9")

def main():
    root = tk.Tk()
    app = SweetDreamsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
