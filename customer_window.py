import os
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.filedialog import askopenfilename

from image_utils import attach_screenshot, resize_avatar, show_screenshot
from utils import auto_priority, check_sla_color, format_datetime


class CustomerWindow(ttk.Frame):
    """Provide customer workflow for submitting, tracking, and rating tickets."""

    def __init__(self, root, db, user):
        """Initialize customer dashboard with notebook tabs and state."""
        super().__init__(root, padding=12)
        self.root = root
        self.db = db
        self.user = user
        self.avatar_image = None
        self.screenshot_source = ""
        self.category_var = tk.StringVar(value="Technical")
        self.priority_var = tk.StringVar(value="Priority: Low")
        self.submit_error_var = tk.StringVar(value="")
        self.rate_error_var = tk.StringVar(value="")
        self.rating_ticket_var = tk.StringVar(value="No Closed Tickets")
        self.rating_value_var = tk.IntVar(value=5)
        self.rating_comment_var = tk.StringVar(value="")
        self.root.title("Customer Dashboard")
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_layout()
        self._refresh_my_tickets()
        self._refresh_rating_options()

    def _build_layout(self):
        """Build dashboard header and notebook tabs using grid only."""
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(1, weight=1)
        self._build_header(header)
        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew")
        self.submit_tab = ttk.Frame(notebook, padding=10)
        self.tickets_tab = ttk.Frame(notebook, padding=10)
        self.rate_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.submit_tab, text="Submit Ticket")
        notebook.add(self.tickets_tab, text="My Tickets")
        notebook.add(self.rate_tab, text="Rate Ticket")
        self._build_submit_tab()
        self._build_tickets_tab()
        self._build_rate_tab()

    def _build_header(self, parent):
        """Render customer title section with optional avatar image."""
        avatar_path = getattr(self.user, "avatar", None)
        if avatar_path and os.path.exists(avatar_path):
            self.avatar_image = resize_avatar(avatar_path)
            ttk.Label(parent, image=self.avatar_image).grid(row=0, column=0, padx=(0, 8))
        ttk.Label(parent, text=f"Welcome, {self.user.username}").grid(row=0, column=1, sticky="w")

    def _build_submit_tab(self):
        """Create submit ticket tab widgets and actions."""
        self.submit_tab.columnconfigure(1, weight=1)
        categories = ["Technical", "Billing", "Service", "General"]
        ttk.Label(self.submit_tab, text="Category").grid(row=0, column=0, sticky="w", pady=6)
        ttk.OptionMenu(self.submit_tab, self.category_var, categories[0], *categories).grid(
            row=0, column=1, sticky="w", pady=6
        )
        ttk.Label(self.submit_tab, text="Complaint").grid(row=1, column=0, sticky="nw", pady=6)
        self.complaint_text = tk.Text(self.submit_tab, height=6)
        self.complaint_text.grid(row=1, column=1, sticky="ew", pady=6)
        self.complaint_text.bind("<KeyRelease>", self._update_priority_preview)
        ttk.Label(self.submit_tab, textvariable=self.priority_var).grid(row=2, column=1, sticky="w")
        self.screenshot_label = ttk.Label(self.submit_tab, text="No screenshot attached")
        self.screenshot_label.grid(row=3, column=1, sticky="w", pady=6)
        ttk.Button(self.submit_tab, text="Attach Screenshot", command=self._attach_screenshot).grid(
            row=3, column=0, sticky="ew", pady=6
        )
        ttk.Label(self.submit_tab, textvariable=self.submit_error_var, foreground="red").grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        ttk.Button(self.submit_tab, text="Submit", command=self._submit_ticket).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=8
        )

    def _build_tickets_tab(self):
        """Create ticket list tab with treeview and refresh controls."""
        self.tickets_tab.columnconfigure(0, weight=1)
        self.tickets_tab.rowconfigure(0, weight=1)
        columns = ("ID", "Category", "Priority", "Status", "Created")
        self.ticket_tree = ttk.Treeview(self.tickets_tab, columns=columns, show="headings")
        for name in columns:
            self.ticket_tree.heading(name, text=name)
            self.ticket_tree.column(name, width=120, anchor="center")
        self.ticket_tree.grid(row=0, column=0, sticky="nsew")
        self.ticket_tree.tag_configure("red", background="#FADBD8")
        self.ticket_tree.tag_configure("orange", background="#FDEBD0")
        self.ticket_tree.tag_configure("yellow", background="#FEFDE7")
        self.ticket_tree.bind("<Double-1>", self._open_ticket_detail)
        ttk.Button(self.tickets_tab, text="Refresh", command=self._refresh_my_tickets).grid(
            row=1, column=0, sticky="ew", pady=8
        )

    def _build_rate_tab(self):
        """Create rating tab controls for closed customer tickets."""
        self.rate_tab.columnconfigure(1, weight=1)
        ttk.Label(self.rate_tab, text="Closed Ticket").grid(row=0, column=0, sticky="w", pady=6)
        self.rating_menu = ttk.OptionMenu(self.rate_tab, self.rating_ticket_var, "No Closed Tickets")
        self.rating_menu.grid(row=0, column=1, sticky="w", pady=6)
        ttk.Label(self.rate_tab, text="Rating").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Scale(self.rate_tab, from_=1, to=5, variable=self.rating_value_var).grid(
            row=1, column=1, sticky="ew", pady=6
        )
        ttk.Label(self.rate_tab, text="Comment").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(self.rate_tab, textvariable=self.rating_comment_var).grid(
            row=2, column=1, sticky="ew", pady=6
        )
        ttk.Label(self.rate_tab, textvariable=self.rate_error_var, foreground="red").grid(
            row=3, column=0, columnspan=2, sticky="w"
        )
        ttk.Button(self.rate_tab, text="Submit Rating", command=self._submit_rating).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=8
        )

    def _update_priority_preview(self, _event=None):
        """Update priority preview label while customer types complaint text."""
        complaint = self.complaint_text.get("1.0", "end").strip()
        detected = auto_priority(complaint) if complaint else "Low"
        self.priority_var.set(f"Priority: {detected}")

    def _attach_screenshot(self):
        """Open image dialog and store selected screenshot source path."""
        selected = askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if not selected:
            return
        self.screenshot_source = selected
        self.screenshot_label.config(text="Screenshot attached")

    def _submit_ticket(self):
        """Validate input, insert ticket, and save screenshot if selected."""
        complaint = self.complaint_text.get("1.0", "end").strip()
        if not complaint:
            self.submit_error_var.set("Complaint text is required.")
            return
        ticket_id = self.user.submit_ticket(self.db, self.category_var.get(), complaint)
        if not ticket_id:
            self.submit_error_var.set("Ticket submission failed.")
            return
        self._save_ticket_screenshot(ticket_id)
        self.submit_error_var.set("")
        self.complaint_text.delete("1.0", "end")
        self.screenshot_source = ""
        self.screenshot_label.config(text="No screenshot attached")
        self._update_priority_preview()
        self._refresh_my_tickets()
        self._refresh_rating_options()
        messagebox.showinfo("Success", f"Ticket #{ticket_id} submitted.")

    def _save_ticket_screenshot(self, ticket_id):
        """Persist screenshot file and store saved path to ticket row."""
        if not self.screenshot_source:
            return
        saved_path = attach_screenshot(ticket_id, self.screenshot_source)
        query = "UPDATE tickets SET screenshot = %s WHERE ticket_id = %s"
        self.db.execute_query(query, (saved_path, ticket_id))

    def _refresh_my_tickets(self):
        """Reload ticket list for the current customer with SLA colors."""
        for item in self.ticket_tree.get_children():
            self.ticket_tree.delete(item)
        query = "SELECT * FROM tickets WHERE customer_id = %s ORDER BY created_at DESC"
        rows = self.db.fetch_all(query, (self.user.user_id,))
        for row in rows:
            created_at = row["created_at"]
            tag = check_sla_color(row["priority"], created_at)
            values = (
                row["ticket_id"],
                row["category"],
                row["priority"],
                row["status"],
                format_datetime(created_at),
            )
            self.ticket_tree.insert("", "end", values=values, tags=(tag,))

    def _open_ticket_detail(self, _event=None):
        """Open detail popup for selected ticket row on double click."""
        selected = self.ticket_tree.selection()
        if not selected:
            return
        ticket_id = int(self.ticket_tree.item(selected[0], "values")[0])
        ticket = self.user.track_ticket(self.db, ticket_id)
        if ticket:
            self._show_ticket_popup(ticket)

    def _show_ticket_popup(self, ticket):
        """Display selected ticket details and screenshot preview popup."""
        popup = tk.Toplevel(self.root)
        popup.title(f"Ticket #{ticket['ticket_id']}")
        popup.geometry("420x420")
        popup.columnconfigure(0, weight=1)
        row_index = 0
        fields = ["category", "priority", "status", "created_at", "complaint"]
        for field in fields:
            value = ticket[field]
            text = format_datetime(value) if field == "created_at" else str(value)
            ttk.Label(popup, text=f"{field.title()}: {text}").grid(
                row=row_index, column=0, sticky="w", padx=10, pady=4
            )
            row_index += 1
        if ticket.get("screenshot") and os.path.exists(ticket["screenshot"]):
            image_label = show_screenshot(ticket["screenshot"], popup)
            image_label.grid(row=row_index, column=0, padx=10, pady=8, sticky="nsew")

    def _refresh_rating_options(self):
        """Refresh closed ticket option menu entries for rating form."""
        query = "SELECT ticket_id FROM tickets WHERE customer_id = %s AND status = %s"
        rows = self.db.fetch_all(query, (self.user.user_id, "Closed"))
        options = [str(row["ticket_id"]) for row in rows] or ["No Closed Tickets"]
        self.rating_ticket_var.set(options[0])
        menu = self.rating_menu["menu"]
        menu.delete(0, "end")
        for option in options:
            menu.add_command(label=option, command=tk._setit(self.rating_ticket_var, option))

    def _submit_rating(self):
        """Save rating for selected closed ticket with optional comment."""
        selected_ticket = self.rating_ticket_var.get()
        if selected_ticket == "No Closed Tickets":
            self.rate_error_var.set("No closed tickets available for rating.")
            return
        rating = int(round(self.rating_value_var.get()))
        comment = self.rating_comment_var.get().strip()
        success = self.user.rate_ticket(self.db, int(selected_ticket), rating, comment)
        if not success:
            self.rate_error_var.set("Rating submission failed.")
            return
        self.rate_error_var.set("")
        self.rating_comment_var.set("")
        messagebox.showinfo("Success", "Rating submitted successfully.")
