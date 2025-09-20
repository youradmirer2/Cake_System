import tkinter as tk
from tkinter import ttk, messagebox

# Demo admin user
ADMIN_USER = ("admin", "admin")

# In-memory cake storage (for demo)
cakes = [
    {"name": "Chocolate Cake", "flavor": "Chocolate", "size": "Medium", "price": 35.0, "stock": 5, "category": "Birthday", "description": "Rich chocolate cake."},
    {"name": "Vanilla Cake", "flavor": "Vanilla", "size": "Large", "price": 45.0, "stock": 3, "category": "Wedding", "description": "Elegant vanilla wedding cake."}
]

class SweetDreamsAdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sweet Dreams Login")
        self.root.geometry("430x550")
        self.root.configure(bg="#fffafc")
        self.root.resizable(False, False)
        self.create_login_ui()

    def create_login_ui(self):
        self.login_frame = ttk.Frame(self.root, padding=30)
        self.login_frame.pack(expand=True, fill='both')

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', font=('Arial', 12))
        style.configure('Title.TLabel', font=('Arial', 22, 'bold'), foreground='#c9407a', background="#fffafc")
        style.configure('TButton', font=('Arial', 12), padding=6)
        style.configure('Accent.TButton', font=('Arial', 12, 'bold'), background='#c9407a', foreground='white')
        style.map('Accent.TButton',
                  background=[('active', '#a82f61'), ('pressed', '#8c254e')])

        ttk.Label(self.login_frame, text="🎂 Sweet Dreams Login", style='Title.TLabel').pack(pady=(0, 28))

        ttk.Label(self.login_frame, text="Username").pack(anchor='w')
        self.username_entry = ttk.Entry(self.login_frame, font=('Arial', 12))
        self.username_entry.pack(fill='x', pady=(0, 16))
        self.username_entry.insert(0, "Enter your username")
        self.username_entry.bind("<FocusIn>", self.clear_username)

        ttk.Label(self.login_frame, text="Password").pack(anchor='w')
        self.password_entry = ttk.Entry(self.login_frame, font=('Arial', 12), show="")
        self.password_entry.pack(fill='x', pady=(0, 16))
        self.password_entry.insert(0, "Enter your password")
        self.password_entry.bind("<FocusIn>", self.clear_password)

        ttk.Label(self.login_frame, text="User Type").pack(anchor='w')
        self.user_type_var = tk.StringVar(value="Admin")
        user_type_combo = ttk.Combobox(self.login_frame, textvariable=self.user_type_var,
            values=["Admin"], state="readonly", font=('Arial', 12))
        user_type_combo.pack(fill='x', pady=(0, 22))

        login_btn = ttk.Button(self.login_frame, text="Login", style='Accent.TButton', command=self.login)
        login_btn.pack(fill='x', pady=(0, 18))

        demo_frame = ttk.LabelFrame(self.login_frame, text="Demo Credentials", padding=12)
        demo_frame.pack(fill='x', pady=(18, 0))
        demo_text = "Admin: admin / admin"
        ttk.Label(demo_frame, text=demo_text, font=('Arial', 10), foreground='#555').pack(anchor='w')

    def clear_username(self, e):
        if self.username_entry.get() == "Enter your username":
            self.username_entry.delete(0, 'end')

    def clear_password(self, e):
        if self.password_entry.get() == "Enter your password":
            self.password_entry.delete(0, 'end')
            self.password_entry.config(show="*")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = self.user_type_var.get()
        if (username, password) == ADMIN_USER and role == "Admin":
            self.login_frame.pack_forget()
            self.show_admin_dashboard()
        else:
            messagebox.showerror("Login failed", "Invalid credentials. Please try again.")

    def show_admin_dashboard(self):
        self.dash = tk.Toplevel(self.root)
        self.dash.title("Admin Dashboard")
        self.dash.geometry("850x500")
        self.dash.configure(bg="#fffafc")
        self.dash.protocol("WM_DELETE_WINDOW", self.root.destroy)

        ttk.Label(self.dash, text="🎂 Sweet Dreams Admin Dashboard", font=('Arial', 20, 'bold'), foreground="#c9407a").pack(pady=20)
        ttk.Button(self.dash, text="Logout", command=self.logout, style='Accent.TButton').pack(side="bottom", pady=15)

        # Cake management section
        cake_section = ttk.LabelFrame(self.dash, text="Cake Management", padding=15)
        cake_section.pack(fill="both", expand=True, padx=30, pady=10)

        # Add cake button
        ttk.Button(cake_section, text="Add Cake", command=self.add_cake, style='Accent.TButton').pack(anchor="ne", pady=(0, 10))

        # Cake list
        self.cake_tree = ttk.Treeview(cake_section, columns=("Name", "Flavor", "Size", "Price", "Stock", "Category", "Description"), show="headings", height=8)
        for col in self.cake_tree["columns"]:
            self.cake_tree.heading(col, text=col)
            self.cake_tree.column(col, width=100)
        self.cake_tree.column("Description", width=180)
        self.cake_tree.pack(fill="both", expand=True)
        self.refresh_cake_list()

        # Delete button
        ttk.Button(cake_section, text="Delete Selected Cake", command=self.delete_cake, style='Accent.TButton').pack(anchor="ne", pady=(10, 0))

    def refresh_cake_list(self):
        for row in self.cake_tree.get_children():
            self.cake_tree.delete(row)
        for cake in cakes:
            self.cake_tree.insert("", "end", values=(cake["name"], cake["flavor"], cake["size"], f"${cake['price']:.2f}", cake["stock"], cake["category"], cake["description"]))

    def add_cake(self):
        def do_add():
            name = name_var.get()
            flavor = flavor_var.get()
            size = size_var.get()
            price = price_var.get()
            stock = stock_var.get()
            category = category_var.get()
            desc = desc_text.get("1.0", "end").strip()

            try:
                price = float(price)
                stock = int(stock)
            except ValueError:
                messagebox.showerror("Error", "Price must be a number and stock an integer.")
                return
            if not name or not flavor or not size or price < 0 or stock < 0 or not category:
                messagebox.showerror("Error", "All fields except description are required.")
                return
            cakes.append({
                "name": name,
                "flavor": flavor,
                "size": size,
                "price": price,
                "stock": stock,
                "category": category,
                "description": desc
            })
            add_win.destroy()
            self.refresh_cake_list()
            messagebox.showinfo("Success", f"Cake '{name}' added!")

        add_win = tk.Toplevel(self.dash)
        add_win.title("Add Cake")
        add_win.geometry("400x480")
        add_win.transient(self.dash)
        add_win.grab_set()
        main_frame = ttk.Frame(add_win, padding=20)
        main_frame.pack(fill="both", expand=True)

        name_var = tk.StringVar()
        flavor_var = tk.StringVar()
        size_var = tk.StringVar()
        price_var = tk.StringVar()
        stock_var = tk.StringVar()
        category_var = tk.StringVar()
        desc_text = tk.Text(main_frame, height=3, width=30)

        items = [
            ("Name", name_var),
            ("Flavor", flavor_var),
            ("Size", size_var),
            ("Price", price_var),
            ("Stock", stock_var),
            ("Category", category_var)
        ]
        for label, var in items:
            ttk.Label(main_frame, text=label).pack(anchor="w", pady=(8, 0))
            ttk.Entry(main_frame, textvariable=var).pack(fill="x")

        ttk.Label(main_frame, text="Description").pack(anchor="w", pady=(8, 0))
        desc_text.pack(fill="x")

        ttk.Button(main_frame, text="Add Cake", command=do_add, style='Accent.TButton').pack(pady=15)

    def delete_cake(self):
        selected = self.cake_tree.selection()
        if not selected:
            messagebox.showerror("Delete Cake", "Please select a cake to delete.")
            return
        idx = self.cake_tree.index(selected[0])
        cake_name = cakes[idx]["name"]
        if messagebox.askyesno("Delete Cake", f"Delete '{cake_name}'?"):
            cakes.pop(idx)
            self.refresh_cake_list()
            messagebox.showinfo("Deleted", f"Cake '{cake_name}' deleted.")

    def logout(self):
        self.dash.destroy()
        self.login_frame.pack(expand=True, fill='both')

if __name__ == "__main__":
    root = tk.Tk()
    app = SweetDreamsAdminApp(root)
    root.mainloop()