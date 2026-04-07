import os
import tkinter as tk

from database import Database
from login_window import LoginWindow


def main():
    """Start the application by creating DB connection and login window."""
    os.makedirs("assets/screenshots", exist_ok=True)
    db = Database()
    db.connect()
    root = tk.Tk()
    root.title("Customer Complaint Ticketing System")
    root.geometry("900x600")
    LoginWindow(root, db)
    root.mainloop()


if __name__ == "__main__":
    main()
