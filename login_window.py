import tkinter as tk
from tkinter import messagebox, ttk

from admin_window import AdminWindow
from agent_window import AgentWindow
from customer_window import CustomerWindow
from image_utils import load_logo
from models import User
from register_window import RegisterWindow


class LoginWindow(ttk.Frame):
    """Display login form and route users to role-based windows."""

    def __init__(self, root, db):
        """Initialize login frame with database dependency."""
        super().__init__(root, padding=16)
        self.root = root
        self.db = db
        self.logo_image = None
        self.error_var = tk.StringVar(value="")
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        self.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self._build_layout()

    def _build_layout(self):
        """Create logo, entries, action buttons, and error label."""
        self.columnconfigure(1, weight=1)
        self._load_logo_widget()
        ttk.Label(self, text="Username").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(self, textvariable=self.username_var).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Label(self, text="Password").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(self, textvariable=self.password_var, show="*").grid(
            row=2, column=1, sticky="ew", pady=6
        )
        ttk.Label(self, textvariable=self.error_var, foreground="red").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=4
        )
        ttk.Button(self, text="Login", command=self._login).grid(row=4, column=0, sticky="ew", pady=8)
        ttk.Button(self, text="Register", command=self._open_register).grid(
            row=4, column=1, sticky="ew", pady=8
        )

    def _load_logo_widget(self):
        """Load and render the login header logo using image utilities."""
        try:
            self.logo_image = load_logo("assets/logo.png", (200, 60))
            ttk.Label(self, image=self.logo_image).grid(row=0, column=0, columnspan=2, pady=(0, 12))
        except Exception:
            ttk.Label(self, text="Customer Complaint System").grid(
                row=0, column=0, columnspan=2, pady=(0, 12)
            )

    def _open_register(self):
        """Open customer registration dialog window."""
        RegisterWindow(self.root, self.db)

    def _login(self):
        """Validate credentials and open role-specific dashboard."""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        if not username or not password:
            self.error_var.set("Please enter username and password.")
            return
        user = User.login(self.db, username, password)
        if not user:
            self.error_var.set("Invalid credentials.")
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return
        self.error_var.set("")
        self._open_role_window(user)

    def _open_role_window(self, user):
        """Route user to matching role dashboard in a new top-level window."""
        role_map = {"Customer": CustomerWindow, "Agent": AgentWindow, "Admin": AdminWindow}
        window_class = role_map.get(user.role)
        if not window_class:
            messagebox.showerror("Role Error", "Unsupported role.")
            return
        self.root.withdraw()
        role_root = tk.Toplevel(self.root)
        role_root.title(f"{user.role} Dashboard")
        role_root.geometry("900x600")
        role_root.rowconfigure(0, weight=1)
        role_root.columnconfigure(0, weight=1)
        window_class(role_root, self.db, user)
        role_root.protocol("WM_DELETE_WINDOW", lambda: self._on_role_close(role_root))

    def _on_role_close(self, role_root):
        """Restore login window when a role dashboard is closed."""
        role_root.destroy()
        self.root.deiconify()
        self.password_var.set("")
