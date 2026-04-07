import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from image_utils import resize_avatar
from utils import check_sla_color, format_datetime


class AgentWindow(ttk.Frame):
    """Provide agent interface for managing assigned customer tickets."""

    def __init__(self, root, db, user):
        """Initialize agent dashboard state and build widgets."""
        super().__init__(root, padding=12)
        self.root = root
        self.db = db
        self.user = user
        self.avatar_image = None
        self.selected_ticket_id = None
        self.status_var = tk.StringVar(value="In Progress")
        self.remark_var = tk.StringVar(value="")
        self.selected_label_var = tk.StringVar(value="Selected Ticket: None")
        self.root.title("Agent Dashboard")
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_layout()
        self._refresh_tickets()

    def _build_layout(self):
        """Build header, assigned tickets treeview, and action panel."""
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._build_header(header)
        self._build_treeview()
        self._build_action_panel()

    def _build_header(self, parent):
        """Render welcome label and optional avatar image for agent."""
        avatar_path = getattr(self.user, "avatar", None)
        if avatar_path and os.path.exists(avatar_path):
            self.avatar_image = resize_avatar(avatar_path)
            ttk.Label(parent, image=self.avatar_image).grid(row=0, column=0, padx=(0, 8))
        ttk.Label(parent, text=f"Welcome, {self.user.username}").grid(row=0, column=1, sticky="w")
        ttk.Button(parent, text="Refresh", command=self._refresh_tickets).grid(row=0, column=2, padx=8)

    def _build_treeview(self):
        """Create assigned ticket table with SLA color tags."""
        frame = ttk.Frame(self)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        columns = ("ID", "Customer", "Category", "Priority", "Status", "Age")
        self.ticket_tree = ttk.Treeview(frame, columns=columns, show="headings")
        for name in columns:
            self.ticket_tree.heading(name, text=name)
            self.ticket_tree.column(name, width=130, anchor="center")
        self.ticket_tree.grid(row=0, column=0, sticky="nsew")
        self.ticket_tree.tag_configure("red", background="#FADBD8")
        self.ticket_tree.tag_configure("orange", background="#FDEBD0")
        self.ticket_tree.tag_configure("yellow", background="#FEFDE7")
        self.ticket_tree.bind("<<TreeviewSelect>>", self._on_row_select)

    def _build_action_panel(self):
        """Build ticket update controls below the treeview."""
        panel = ttk.Frame(self)
        panel.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        panel.columnconfigure(4, weight=1)
        ttk.Label(panel, textvariable=self.selected_label_var).grid(row=0, column=0, sticky="w", padx=4)
        ttk.OptionMenu(panel, self.status_var, "In Progress", "In Progress", "Closed").grid(
            row=0, column=1, padx=4
        )
        ttk.Entry(panel, textvariable=self.remark_var).grid(row=0, column=2, sticky="ew", padx=4)
        ttk.Button(panel, text="Update", command=self._update_ticket).grid(row=0, column=3, padx=4)

    def _refresh_tickets(self):
        """Reload assigned tickets and repaint treeview rows."""
        for item in self.ticket_tree.get_children():
            self.ticket_tree.delete(item)
        rows = self.user.view_assigned(self.db)
        for row in rows:
            age_text = self._format_age(row["created_at"])
            tag = check_sla_color(row["priority"], row["created_at"])
            values = (
                row["ticket_id"],
                row.get("customer_name", ""),
                row["category"],
                row["priority"],
                row["status"],
                age_text,
            )
            self.ticket_tree.insert("", "end", values=values, tags=(tag,))

    def _format_age(self, created_at):
        """Return compact age text in hours and minutes for display."""
        ticket_time = datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at
        delta = datetime.now() - ticket_time
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"

    def _on_row_select(self, _event=None):
        """Store selected ticket id from tree selection event."""
        selected = self.ticket_tree.selection()
        if not selected:
            return
        self.selected_ticket_id = int(self.ticket_tree.item(selected[0], "values")[0])
        self.selected_label_var.set(f"Selected Ticket: {self.selected_ticket_id}")

    def _update_ticket(self):
        """Apply selected status update and optional remark to a ticket."""
        if not self.selected_ticket_id:
            messagebox.showerror("Selection Error", "Select a ticket first.")
            return
        status_updated = self.user.update_status(self.db, self.selected_ticket_id, self.status_var.get())
        if not status_updated:
            messagebox.showerror("Update Error", "Could not update ticket status.")
            return
        note = self.remark_var.get().strip()
        if note:
            self.user.add_remark(self.db, self.selected_ticket_id, note)
        self.remark_var.set("")
        messagebox.showinfo("Success", "Ticket updated successfully.")
        self._refresh_tickets()
