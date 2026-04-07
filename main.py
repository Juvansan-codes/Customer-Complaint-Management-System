import tkinter as tk
from tkinter import messagebox
import csv

import mysql.connector
import matplotlib.pyplot as plt

# Basic database settings
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "mysql123"
DB_NAME = "complaint_db"


class Complaint:
    """Store complaint values in a simple object."""

    def __init__(self, complaint_id, username, issue, status, priority="Low"):
        """Create complaint object with id, username, issue, status and priority."""
        self.complaint_id = complaint_id
        self.username = username
        self.issue = issue
        self.status = status
        self.priority = priority


def get_connection():
    """Create and return database connection."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
    )


def setup_database():
    """Create required tables if they do not exist."""
    connection = get_connection()
    cursor = connection.cursor()

    # Create users table only if missing (keeps existing data)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "username VARCHAR(50) PRIMARY KEY, "
        "password VARCHAR(50), "
        "role VARCHAR(20))"
    )

    # Create complaints table only if missing (keeps existing data)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS complaints ("
        "id INT AUTO_INCREMENT PRIMARY KEY, "
        "username VARCHAR(50), "
        "issue TEXT, "
        "status VARCHAR(50), "
        "priority VARCHAR(20))"
    )

    # Add priority column for old tables that do not have it
    cursor.execute("SHOW COLUMNS FROM complaints LIKE 'priority'")
    priority_column = cursor.fetchall()
    if len(priority_column) == 0:
        cursor.execute("ALTER TABLE complaints ADD COLUMN priority VARCHAR(20) DEFAULT 'Low'")

    # If old schema has users.email NOT NULL, make it nullable for this simple app
    cursor.execute("SHOW COLUMNS FROM users LIKE 'email'")
    email_column = cursor.fetchall()
    if len(email_column) > 0:
        cursor.execute("ALTER TABLE users MODIFY email VARCHAR(100) NULL")

    connection.commit()


def clear_window():
    """Remove all widgets from main window."""
    for widget in root.winfo_children():
        widget.destroy()


def show_login_page():
    """Show login page widgets."""
    clear_window()

    # Keep one center cell so form stays in the middle of the window
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0)
    root.grid_rowconfigure(2, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=0)
    root.grid_columnconfigure(2, weight=1)

    # Simple form group for clean alignment
    form_frame = tk.Frame(root)
    form_frame.grid(row=1, column=1)

    tk.Label(form_frame, text="Login Page", font=("Arial", 16, "bold")).grid(
        row=0, column=0, columnspan=2, pady=(0, 15)
    )
    tk.Label(form_frame, text="Username").grid(row=1, column=0, padx=(0, 10), pady=6, sticky="e")
    username_entry = tk.Entry(form_frame, width=30)
    username_entry.grid(row=1, column=1, pady=6, sticky="w")
    tk.Label(form_frame, text="Password").grid(row=2, column=0, padx=(0, 10), pady=6, sticky="e")
    password_entry = tk.Entry(form_frame, width=30, show="*")
    password_entry.grid(row=2, column=1, pady=6, sticky="w")
    tk.Button(
        form_frame,
        text="Login",
        bg="#4CAF50",
        fg="white",
        command=lambda: login_user(username_entry.get(), password_entry.get()),
    ).grid(row=3, column=0, columnspan=2, pady=(12, 6))
    tk.Button(form_frame, text="Go to Register", bg="#4CAF50", fg="white", command=show_register_page).grid(
        row=4, column=0, columnspan=2, pady=(4, 0)
    )


def show_register_page():
    """Show register page widgets."""
    clear_window()
    tk.Label(root, text="Register Page", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(root, text="Username").grid(row=1, column=0, padx=8, pady=8, sticky="w")
    username_entry = tk.Entry(root, width=30)
    username_entry.grid(row=1, column=1, padx=8, pady=8)
    tk.Label(root, text="Password").grid(row=2, column=0, padx=8, pady=8, sticky="w")
    password_entry = tk.Entry(root, width=30, show="*")
    password_entry.grid(row=2, column=1, padx=8, pady=8)
    tk.Label(root, text="Role").grid(row=3, column=0, padx=8, pady=8, sticky="w")
    role_var = tk.StringVar(value="Customer")
    tk.OptionMenu(root, role_var, "Admin", "Agent", "Customer").grid(row=3, column=1, padx=8, pady=8, sticky="w")
    tk.Button(
        root,
        text="Register",
        bg="#4CAF50",
        fg="white",
        command=lambda: register_user(username_entry.get(), password_entry.get(), role_var.get()),
    ).grid(row=4, column=1, padx=8, pady=8, sticky="w")
    tk.Button(root, text="Back to Login", bg="#2196F3", fg="white", command=show_login_page).grid(
        row=5, column=1, padx=8, pady=8, sticky="w"
    )


def register_user(username, password, role):
    """Register a new user after simple validation."""
    username = username.strip()
    password = password.strip()
    if username == "" or password == "":
        messagebox.showinfo("Input", "Please fill all fields.")
        return
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
    rows = cursor.fetchall()
    if len(rows) > 0:
        messagebox.showinfo("Register", "Username already exists.")
        return
    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
    connection.commit()
    messagebox.showinfo("Register", "Registration successful.")
    show_login_page()


def login_user(username, password):
    """Check login and open page based on user role."""
    username = username.strip()
    password = password.strip()
    if username == "" or password == "":
        messagebox.showinfo("Input", "Please enter username and password.")
        return
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT username, role FROM users WHERE username = %s AND password = %s", (username, password))
    rows = cursor.fetchall()
    if len(rows) == 0:
        messagebox.showinfo("Login", "Invalid username or password.")
        return
    role = rows[0][1]
    if role == "Admin":
        show_admin_page(username)
    elif role == "Agent":
        show_agent_page(username)
    else:
        show_customer_page(username)


def show_customer_page(username):
    """Show customer page for adding and viewing own complaints."""
    clear_window()
    tk.Label(root, text=f"Customer Page - {username}", font=("Arial", 14, "bold")).grid(
        row=0, column=0, columnspan=2, pady=10
    )
    tk.Label(root, text="Issue").grid(row=1, column=0, padx=8, pady=8, sticky="w")
    issue_entry = tk.Entry(root, width=40)
    issue_entry.grid(row=1, column=1, padx=8, pady=8, sticky="w")
    tk.Button(root, text="Add Complaint", bg="#4CAF50", fg="white", command=lambda: add_complaint(username, issue_entry)).grid(
        row=2, column=1, padx=8, pady=8, sticky="w"
    )
    complaint_list = tk.Listbox(root, width=90, height=12)
    complaint_list.grid(row=3, column=0, columnspan=2, padx=8, pady=8)
    tk.Button(
        root,
        text="View My Complaints",
        bg="#2196F3",
        fg="white",
        command=lambda: view_my_complaints(username, complaint_list),
    ).grid(
        row=4, column=1, padx=8, pady=8, sticky="w"
    )
    tk.Button(root, text="Logout", bg="#f44336", fg="white", command=show_login_page).grid(
        row=5, column=1, padx=8, pady=8, sticky="w"
    )


def detect_priority(issue):
    """Return complaint priority from simple keyword matching."""
    # Convert to lowercase so matching is easier
    text = issue.lower()

    # High priority keywords
    if "urgent" in text or "immediately" in text or "asap" in text:
        return "High"

    # Medium priority keywords
    if "delay" in text or "problem" in text or "error" in text:
        return "Medium"

    # Default priority
    return "Low"


def add_complaint(username, issue_entry):
    """Add complaint row from customer input."""
    issue = issue_entry.get().strip()
    if issue == "":
        messagebox.showinfo("Input", "Please write your issue.")
        return

    # Detect priority from complaint text
    priority = detect_priority(issue)
    complaint = Complaint(None, username, issue, "Open", priority)

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO complaints (username, issue, status, priority) VALUES (%s, %s, %s, %s)",
        (complaint.username, complaint.issue, complaint.status, complaint.priority),
    )
    connection.commit()
    issue_entry.delete(0, tk.END)
    messagebox.showinfo("Complaint", "Complaint added successfully.")


def view_my_complaints(username, complaint_list):
    """View only complaints of the logged-in customer."""
    complaint_list.delete(0, tk.END)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, username, issue, status, priority FROM complaints WHERE username = %s", (username,))
    rows = cursor.fetchall()
    for row in rows:
        complaint = Complaint(row[0], row[1], row[2], row[3], row[4])
        line = (
            f"ID: {complaint.complaint_id} | "
            f"Issue: {complaint.issue} | "
            f"Status: {complaint.status} | "
            f"Priority: {complaint.priority}"
        )
        complaint_list.insert(tk.END, line)


def show_agent_page(username):
    """Show agent page for viewing and updating complaint status."""
    clear_window()
    tk.Label(root, text=f"Agent Page - {username}", font=("Arial", 14, "bold")).grid(
        row=0, column=0, columnspan=2, pady=10
    )
    complaint_list = tk.Listbox(root, width=90, height=12)
    complaint_list.grid(row=1, column=0, columnspan=2, padx=8, pady=8)
    tk.Button(
        root,
        text="View All Complaints",
        bg="#2196F3",
        fg="white",
        command=lambda: view_all_complaints(complaint_list),
    ).grid(
        row=2, column=1, padx=8, pady=8, sticky="w"
    )
    tk.Label(root, text="Complaint ID").grid(row=3, column=0, padx=8, pady=8, sticky="w")
    id_entry = tk.Entry(root, width=20)
    id_entry.grid(row=3, column=1, padx=8, pady=8, sticky="w")

    # Dropdown for fixed status values (prevents typing mistakes)
    tk.Label(root, text="New Status").grid(row=4, column=0, padx=8, pady=8, sticky="w")
    status_var = tk.StringVar()
    status_var.set("Pending")
    tk.OptionMenu(root, status_var, "Pending", "In Progress", "Resolved", "Closed").grid(
        row=4, column=1, padx=8, pady=8, sticky="w"
    )
    tk.Button(
        root,
        text="Update Status",
        bg="#FF9800",
        fg="white",
        command=lambda: update_status(id_entry.get(), status_var.get()),
    ).grid(
        row=5, column=1, padx=8, pady=8, sticky="w"
    )
    tk.Button(root, text="Logout", bg="#f44336", fg="white", command=show_login_page).grid(
        row=6, column=1, padx=8, pady=8, sticky="w"
    )


def show_admin_page(username):
    """Show admin page for viewing and updating complaint status."""
    clear_window()
    tk.Label(root, text=f"Admin Page - {username}", font=("Arial", 14, "bold")).grid(
        row=0, column=0, columnspan=2, pady=10
    )
    complaint_list = tk.Listbox(root, width=90, height=12)
    complaint_list.grid(row=1, column=0, columnspan=2, padx=8, pady=8)
    tk.Button(
        root,
        text="View All Complaints",
        bg="#2196F3",
        fg="white",
        command=lambda: view_all_complaints(complaint_list),
    ).grid(
        row=2, column=1, padx=8, pady=8, sticky="w"
    )
    tk.Label(root, text="Complaint ID").grid(row=3, column=0, padx=8, pady=8, sticky="w")
    id_entry = tk.Entry(root, width=20)
    id_entry.grid(row=3, column=1, padx=8, pady=8, sticky="w")

    # Dropdown for fixed status values (prevents typing mistakes)
    tk.Label(root, text="New Status").grid(row=4, column=0, padx=8, pady=8, sticky="w")
    status_var = tk.StringVar()
    status_var.set("Pending")
    tk.OptionMenu(root, status_var, "Pending", "In Progress", "Resolved", "Closed").grid(
        row=4, column=1, padx=8, pady=8, sticky="w"
    )
    tk.Button(
        root,
        text="Update Status",
        bg="#FF9800",
        fg="white",
        command=lambda: update_status(id_entry.get(), status_var.get()),
    ).grid(
        row=5, column=1, padx=8, pady=8, sticky="w"
    )

    # NEW FEATURE 1: Export all complaints to CSV file
    tk.Button(root, text="Export to CSV", bg="#2196F3", fg="white", command=export_to_csv).grid(
        row=6, column=1, padx=8, pady=8, sticky="w"
    )

    # NEW FEATURE 2: Show bar graph of complaints by status
    tk.Button(root, text="Show Graph", bg="#2196F3", fg="white", command=show_graph).grid(
        row=7, column=1, padx=8, pady=8, sticky="w"
    )

    tk.Button(root, text="Logout", bg="#f44336", fg="white", command=show_login_page).grid(
        row=8, column=1, padx=8, pady=8, sticky="w"
    )


def view_all_complaints(complaint_list):
    """Show all complaints in listbox for agent/admin."""
    complaint_list.delete(0, tk.END)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, username, issue, status, priority FROM complaints")
    rows = cursor.fetchall()
    for row in rows:
        complaint = Complaint(row[0], row[1], row[2], row[3], row[4])
        line = (
            f"ID: {complaint.complaint_id} | "
            f"User: {complaint.username} | "
            f"Issue: {complaint.issue} | "
            f"Status: {complaint.status} | "
            f"Priority: {complaint.priority}"
        )
        complaint_list.insert(tk.END, line)


def update_status(complaint_id, new_status):
    """Update complaint status by complaint ID."""
    complaint_id = complaint_id.strip()
    new_status = new_status.strip()
    if not complaint_id.isdigit() or new_status == "":
        messagebox.showinfo("Input", "Please enter valid complaint ID and status.")
        return
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE complaints SET status = %s WHERE id = %s", (new_status, int(complaint_id)))
    connection.commit()
    messagebox.showinfo("Update", "Status updated successfully.")


def export_to_csv():
    """Export all complaints to complaints.csv file."""
    # Get all complaint records from database
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, username, issue, status FROM complaints")
    rows = cursor.fetchall()

    # Write records to CSV file with header row
    with open("complaints.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Username", "Issue", "Status"])
        writer.writerows(rows)

    messagebox.showinfo("CSV Export", "Data exported to complaints.csv")


def show_graph():
    """Show bar graph with complaint counts by status."""
    # Get complaint count grouped by status
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM complaints GROUP BY status")
    rows = cursor.fetchall()

    # Build simple lists for graph axes
    status_list = []
    count_list = []
    for row in rows:
        status_list.append(row[0])
        count_list.append(row[1])

    # Draw simple bar graph
    plt.bar(status_list, count_list)
    plt.xlabel("Status")
    plt.ylabel("Count")
    plt.title("Complaints by Status")
    plt.show()


# Create root window
root = tk.Tk()
root.title("Simple Complaint Management System")
root.geometry("760x560")

# Create tables and open login page
setup_database()
show_login_page()

# Start GUI
root.mainloop()
