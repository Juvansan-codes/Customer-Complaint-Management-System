import tkinter as tk
from tkinter import messagebox, ttk

import bcrypt


class RegisterWindow(tk.Toplevel):
    """Display and handle new customer account registration."""

    def __init__(self, parent, db):
        """Create registration dialog and initialize form state."""
        super().__init__(parent)
        self.db = db
        self.title("Register Customer")
        self.geometry("420x320")
        self.resizable(False, False)
        self.columnconfigure(0, weight=1)
        self.error_var = tk.StringVar(value="")
        self.fields = {}
        self._build_form()

    def _build_form(self):
        """Build registration form widgets using grid layout only."""
        form = ttk.Frame(self, padding=16)
        form.grid(row=0, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)
        labels = ["Username", "Password", "Confirm Password", "Email"]
        keys = ["username", "password", "confirm", "email"]
        for index, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=index, column=0, sticky="w", pady=6)
            show_char = "*" if "Password" in label else ""
            entry = ttk.Entry(form, show=show_char)
            entry.grid(row=index, column=1, sticky="ew", pady=6)
            self.fields[keys[index]] = entry
        ttk.Label(form, textvariable=self.error_var, foreground="red").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(4, 10)
        )
        ttk.Button(form, text="Create Account", command=self._register_customer).grid(
            row=5, column=0, columnspan=2, sticky="ew"
        )

    def _register_customer(self):
        """Validate form input and insert a new customer account."""
        username = self.fields["username"].get().strip()
        password = self.fields["password"].get().strip()
        confirm = self.fields["confirm"].get().strip()
        email = self.fields["email"].get().strip()
        if not all([username, password, confirm, email]):
            self.error_var.set("All fields are required.")
            return
        if password != confirm:
            self.error_var.set("Passwords do not match.")
            return
        if self.db.fetch_one("SELECT user_id FROM users WHERE username = %s", (username,)):
            self.error_var.set("Username already exists.")
            return
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        query = "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)"
        success = self.db.execute_query(query, (username, hashed, email, "Customer"))
        if not success:
            self.error_var.set("Could not create account.")
            return
        messagebox.showinfo("Success", "Customer account created successfully.")
        self.destroy()
