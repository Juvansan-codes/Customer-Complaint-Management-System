import csv
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, simpledialog, ttk
from tkinter.filedialog import asksaveasfilename

import bcrypt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils import check_sla_color, format_datetime


class AdminWindow(ttk.Frame):
    """Provide admin dashboard for analytics and system management tasks."""

    def __init__(self, root, db, user):
        """Initialize admin state, tabs, and initial data load."""
        super().__init__(root, padding=12)
        self.root = root
        self.db = db
        self.user = user
        self._init_variables()
        self._configure_window()
        self._build_layout()
        self._load_agents()
        self._render_dashboard()
        self._refresh_all_tickets()
        self._refresh_assign_tab()
        self._refresh_users()

    def _init_variables(self):
        """Initialize admin dashboard state variables and in-memory caches."""
        self.agent_lookup = {}
        self.all_ticket_rows = []
        self.report_rows = []
        self.selected_assign_ticket_id = None
        self.disabled_marker = "__DISABLED__"
        self.search_var = tk.StringVar(value="")
        self.status_filter_var = tk.StringVar(value="All")
        self.priority_filter_var = tk.StringVar(value="All")
        self.agent_filter_var = tk.StringVar(value="All")
        self.assign_agent_var = tk.StringVar(value="")
        self.report_status_var = tk.StringVar(value="All")
        self.report_priority_var = tk.StringVar(value="All")
        self.report_start_var = tk.StringVar(value="")
        self.report_end_var = tk.StringVar(value="")

    def _configure_window(self):
        """Configure root title and frame expansion behavior."""
        self.root.title("Admin Dashboard")
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def _build_layout(self):
        """Create notebook tabs for dashboard, tickets, assign, reports, and users."""
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew")
        self.dashboard_tab = ttk.Frame(notebook, padding=10)
        self.all_tickets_tab = ttk.Frame(notebook, padding=10)
        self.assign_tab = ttk.Frame(notebook, padding=10)
        self.reports_tab = ttk.Frame(notebook, padding=10)
        self.users_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.dashboard_tab, text="Dashboard")
        notebook.add(self.all_tickets_tab, text="All Tickets")
        notebook.add(self.assign_tab, text="Assign Ticket")
        notebook.add(self.reports_tab, text="Reports")
        notebook.add(self.users_tab, text="Users")
        self._build_dashboard_tab()
        self._build_all_tickets_tab()
        self._build_assign_tab()
        self._build_reports_tab()
        self._build_users_tab()

    def _build_dashboard_tab(self):
        """Build dashboard tab controls and chart host frame."""
        self.dashboard_tab.columnconfigure(0, weight=1)
        self.dashboard_tab.rowconfigure(1, weight=1)
        ttk.Button(self.dashboard_tab, text="Refresh Charts", command=self._render_dashboard).grid(
            row=0, column=0, sticky="ew", pady=(0, 8)
        )
        self.chart_frame = ttk.Frame(self.dashboard_tab)
        self.chart_frame.grid(row=1, column=0, sticky="nsew")
        self.chart_frame.columnconfigure(0, weight=1)
        self.chart_frame.rowconfigure(0, weight=1)

    def _render_dashboard(self):
        """Render status pie, category bar, and 7-day volume line charts."""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        status = self._fetch_status_counts()
        category = self._fetch_category_counts()
        days, counts = self._fetch_daily_counts()
        figure, axes = plt.subplots(1, 3, figsize=(12, 3), tight_layout=True)
        axes[0].pie(status.values(), labels=status.keys(), autopct="%1.0f%%")
        axes[0].set_title("Status")
        axes[1].bar(category.keys(), category.values(), color="#5DADE2")
        axes[1].set_title("Category")
        axes[2].plot(days, counts, marker="o", color="#27AE60")
        axes[2].set_title("7-Day Volume")
        canvas = FigureCanvasTkAgg(figure, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def _fetch_status_counts(self):
        """Fetch grouped ticket counts by status with defaults for missing labels."""
        rows = self.db.fetch_all("SELECT status, COUNT(*) AS total FROM tickets GROUP BY status")
        data = {"Open": 0, "In Progress": 0, "Closed": 0}
        for row in rows:
            data[row["status"]] = row["total"]
        return data

    def _fetch_category_counts(self):
        """Fetch grouped ticket counts by category for bar chart rendering."""
        rows = self.db.fetch_all("SELECT category, COUNT(*) AS total FROM tickets GROUP BY category")
        if not rows:
            return {"No Data": 0}
        return {row["category"] or "Unspecified": row["total"] for row in rows}

    def _fetch_daily_counts(self):
        """Fetch and map ticket volume data for the last seven calendar days."""
        query = (
            "SELECT DATE(created_at) AS day_key, COUNT(*) AS total FROM tickets "
            "WHERE created_at >= NOW() - INTERVAL 7 DAY GROUP BY DATE(created_at)"
        )
        rows = self.db.fetch_all(query)
        lookup = {str(row["day_key"]): row["total"] for row in rows}
        labels = []
        counts = []
        for index in range(6, -1, -1):
            day_value = date.today() - timedelta(days=index)
            labels.append(day_value.strftime("%d %b"))
            counts.append(lookup.get(str(day_value), 0))
        return labels, counts

    def _build_all_tickets_tab(self):
        """Create searchable and filterable all-tickets table section."""
        self.all_tickets_tab.columnconfigure(0, weight=1)
        self.all_tickets_tab.rowconfigure(1, weight=1)
        filter_frame = ttk.Frame(self.all_tickets_tab)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._build_ticket_filter_controls(filter_frame)
        self._bind_ticket_filter_traces()
        self._build_all_tickets_tree()

    def _build_ticket_filter_controls(self, filter_frame):
        """Create search and dropdown filter controls for ticket list."""
        ttk.Entry(filter_frame, textvariable=self.search_var).grid(row=0, column=0, padx=4)
        ttk.OptionMenu(filter_frame, self.status_filter_var, "All", "All", "Open", "In Progress", "Closed").grid(
            row=0, column=1, padx=4
        )
        ttk.OptionMenu(filter_frame, self.priority_filter_var, "All", "All", "High", "Medium", "Low").grid(
            row=0, column=2, padx=4
        )
        self.agent_filter_menu = ttk.OptionMenu(filter_frame, self.agent_filter_var, "All")
        self.agent_filter_menu.grid(row=0, column=3, padx=4)
        ttk.Button(filter_frame, text="Refresh", command=self._refresh_all_tickets).grid(row=0, column=4, padx=4)

    def _bind_ticket_filter_traces(self):
        """Bind filter variable changes to table filtering callback."""
        self.search_var.trace_add("write", lambda *_: self._filter_tickets())
        self.status_filter_var.trace_add("write", lambda *_: self._filter_tickets())
        self.priority_filter_var.trace_add("write", lambda *_: self._filter_tickets())
        self.agent_filter_var.trace_add("write", lambda *_: self._filter_tickets())

    def _build_all_tickets_tree(self):
        """Create all-tickets treeview and configure SLA color tags."""
        columns = ("ID", "Customer", "Category", "Priority", "Status", "Agent", "Created")
        self.all_tree = ttk.Treeview(self.all_tickets_tab, columns=columns, show="headings")
        for name in columns:
            self.all_tree.heading(name, text=name)
            self.all_tree.column(name, width=120, anchor="center")
        self.all_tree.grid(row=1, column=0, sticky="nsew")
        self.all_tree.tag_configure("red", background="#FADBD8")
        self.all_tree.tag_configure("orange", background="#FDEBD0")
        self.all_tree.tag_configure("yellow", background="#FEFDE7")

    def _refresh_all_tickets(self):
        """Reload all ticket rows and update table based on active filters."""
        self._load_agents()
        query = (
            "SELECT t.*, c.username AS customer_name, a.username AS agent_name "
            "FROM tickets t JOIN users c ON t.customer_id = c.user_id "
            "LEFT JOIN users a ON t.assigned_to = a.user_id ORDER BY t.created_at DESC"
        )
        self.all_ticket_rows = self.db.fetch_all(query)
        self._set_agent_menu(self.agent_filter_menu, self.agent_filter_var)
        self._filter_tickets()

    def _filter_tickets(self):
        """Apply search and dropdown filters and repaint all-tickets treeview."""
        for item in self.all_tree.get_children():
            self.all_tree.delete(item)
        for row in self.all_ticket_rows:
            if not self._row_matches_filters(row):
                continue
            tag = check_sla_color(row["priority"], row["created_at"])
            values = (
                row["ticket_id"],
                row["customer_name"],
                row["category"],
                row["priority"],
                row["status"],
                row.get("agent_name") or "Unassigned",
                format_datetime(row["created_at"]),
            )
            self.all_tree.insert("", "end", values=values, tags=(tag,))

    def _row_matches_filters(self, row):
        """Return True when row satisfies search text and selected filters."""
        search_text = self.search_var.get().strip().lower()
        if search_text and search_text not in str(row).lower():
            return False
        if self.status_filter_var.get() not in ["All", row["status"]]:
            return False
        if self.priority_filter_var.get() not in ["All", row["priority"]]:
            return False
        agent_name = row.get("agent_name") or "Unassigned"
        return self.agent_filter_var.get() in ["All", agent_name]

    def _build_assign_tab(self):
        """Create assign-ticket table, agent selector, and action button."""
        self.assign_tab.columnconfigure(0, weight=1)
        self.assign_tab.rowconfigure(0, weight=1)
        columns = ("ID", "Customer", "Category", "Priority", "Created")
        self.assign_tree = ttk.Treeview(self.assign_tab, columns=columns, show="headings")
        for name in columns:
            self.assign_tree.heading(name, text=name)
            self.assign_tree.column(name, width=140, anchor="center")
        self.assign_tree.grid(row=0, column=0, sticky="nsew")
        self.assign_tree.bind("<<TreeviewSelect>>", self._on_assign_select)
        controls = ttk.Frame(self.assign_tab)
        controls.grid(row=1, column=0, sticky="ew", pady=8)
        self.assign_agent_menu = ttk.OptionMenu(controls, self.assign_agent_var, "")
        self.assign_agent_menu.grid(row=0, column=0, padx=4)
        ttk.Button(controls, text="Assign", command=self._assign_selected_ticket).grid(row=0, column=1, padx=4)

    def _refresh_assign_tab(self):
        """Reload open tickets table and update assign-agent option menu."""
        for item in self.assign_tree.get_children():
            self.assign_tree.delete(item)
        query = (
            "SELECT t.ticket_id, u.username AS customer_name, t.category, t.priority, t.created_at "
            "FROM tickets t JOIN users u ON t.customer_id = u.user_id WHERE t.status = %s"
        )
        rows = self.db.fetch_all(query, ("Open",))
        for row in rows:
            values = (
                row["ticket_id"],
                row["customer_name"],
                row["category"],
                row["priority"],
                format_datetime(row["created_at"]),
            )
            self.assign_tree.insert("", "end", values=values)
        self._set_agent_menu(self.assign_agent_menu, self.assign_agent_var, include_all=False)

    def _on_assign_select(self, _event=None):
        """Store selected open ticket id for assignment action."""
        selected = self.assign_tree.selection()
        if not selected:
            self.selected_assign_ticket_id = None
            return
        self.selected_assign_ticket_id = int(self.assign_tree.item(selected[0], "values")[0])

    def _assign_selected_ticket(self):
        """Assign selected open ticket to selected agent user."""
        agent_name = self.assign_agent_var.get()
        agent_id = self.agent_lookup.get(agent_name)
        if not self.selected_assign_ticket_id or not agent_id:
            messagebox.showerror("Assign Error", "Select an open ticket and an agent.")
            return
        success = self.user.assign_ticket(self.db, self.selected_assign_ticket_id, agent_id)
        if not success:
            messagebox.showerror("Assign Error", "Could not assign ticket.")
            return
        messagebox.showinfo("Success", "Ticket assigned successfully.")
        self._refresh_assign_tab()
        self._refresh_all_tickets()
        self._render_dashboard()

    def _build_reports_tab(self):
        """Create report filters, preview table, and CSV export actions."""
        self.reports_tab.columnconfigure(0, weight=1)
        self.reports_tab.rowconfigure(1, weight=1)
        filters = ttk.Frame(self.reports_tab)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Entry(filters, textvariable=self.report_start_var).grid(row=0, column=0, padx=4)
        ttk.Entry(filters, textvariable=self.report_end_var).grid(row=0, column=1, padx=4)
        ttk.OptionMenu(filters, self.report_status_var, "All", "All", "Open", "In Progress", "Closed").grid(
            row=0, column=2, padx=4
        )
        ttk.OptionMenu(filters, self.report_priority_var, "All", "All", "High", "Medium", "Low").grid(
            row=0, column=3, padx=4
        )
        ttk.Button(filters, text="Preview", command=self._preview_report).grid(row=0, column=4, padx=4)
        ttk.Button(filters, text="Export CSV", command=self._export_report).grid(row=0, column=5, padx=4)
        columns = ("ID", "Category", "Priority", "Status", "Agent", "Created")
        self.report_tree = ttk.Treeview(self.reports_tab, columns=columns, show="headings")
        for name in columns:
            self.report_tree.heading(name, text=name)
            self.report_tree.column(name, width=130, anchor="center")
        self.report_tree.grid(row=1, column=0, sticky="nsew")

    def _preview_report(self):
        """Generate filtered report rows and display them in preview table."""
        filters = {
            "status": self.report_status_var.get(),
            "priority": self.report_priority_var.get(),
            "agent": "All",
        }
        rows = self.user.generate_report(self.db, filters)
        self.report_rows = [row for row in rows if self._within_date_range(row["created_at"])]
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        for row in self.report_rows:
            values = (
                row["ticket_id"],
                row["category"],
                row["priority"],
                row["status"],
                row.get("assigned_to") or "",
                format_datetime(row["created_at"]),
            )
            self.report_tree.insert("", "end", values=values)

    def _within_date_range(self, created_at):
        """Check if ticket date falls between optional start and end dates."""
        created_date = created_at.date() if hasattr(created_at, "date") else datetime.fromisoformat(created_at).date()
        start_text = self.report_start_var.get().strip()
        end_text = self.report_end_var.get().strip()
        if start_text:
            start_date = datetime.strptime(start_text, "%Y-%m-%d").date()
            if created_date < start_date:
                return False
        if end_text:
            end_date = datetime.strptime(end_text, "%Y-%m-%d").date()
            if created_date > end_date:
                return False
        return True

    def _export_report(self):
        """Export currently previewed report rows to CSV file."""
        if not self.report_rows:
            messagebox.showerror("Export Error", "No report data to export.")
            return
        file_path = asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not file_path:
            return
        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Ticket ID", "Category", "Priority", "Status", "Assigned To", "Created At"])
            for row in self.report_rows:
                writer.writerow(
                    [
                        row["ticket_id"],
                        row["category"],
                        row["priority"],
                        row["status"],
                        row.get("assigned_to") or "",
                        format_datetime(row["created_at"]),
                    ]
                )
        messagebox.showinfo("Success", "Report exported successfully.")

    def _build_users_tab(self):
        """Create user management table with add-agent and toggle controls."""
        self.users_tab.columnconfigure(0, weight=1)
        self.users_tab.rowconfigure(0, weight=1)
        columns = ("ID", "Username", "Email", "Role", "State")
        self.users_tree = ttk.Treeview(self.users_tab, columns=columns, show="headings")
        for name in columns:
            self.users_tree.heading(name, text=name)
            self.users_tree.column(name, width=140, anchor="center")
        self.users_tree.grid(row=0, column=0, sticky="nsew")
        buttons = ttk.Frame(self.users_tab)
        buttons.grid(row=1, column=0, sticky="ew", pady=8)
        ttk.Button(buttons, text="Add Agent", command=self._add_agent).grid(row=0, column=0, padx=4)
        ttk.Button(buttons, text="Disable/Enable", command=self._toggle_user_state).grid(row=0, column=1, padx=4)
        ttk.Button(buttons, text="Refresh", command=self._refresh_users).grid(row=0, column=2, padx=4)

    def _refresh_users(self):
        """Reload users table with computed enabled or disabled state label."""
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        rows = self.db.fetch_all("SELECT * FROM users ORDER BY created_at DESC")
        for row in rows:
            avatar = row.get("avatar") or ""
            state = "Disabled" if avatar.startswith(self.disabled_marker) else "Enabled"
            values = (row["user_id"], row["username"], row["email"], row["role"], state)
            self.users_tree.insert("", "end", values=values)

    def _add_agent(self):
        """Prompt admin for agent details and create a new agent account."""
        username = simpledialog.askstring("Add Agent", "Username:", parent=self.root)
        email = simpledialog.askstring("Add Agent", "Email:", parent=self.root)
        password = simpledialog.askstring("Add Agent", "Temporary Password:", parent=self.root, show="*")
        if not all([username, email, password]):
            messagebox.showerror("Input Error", "All fields are required.")
            return
        existing = self.db.fetch_one("SELECT user_id FROM users WHERE username = %s", (username.strip(),))
        if existing:
            messagebox.showerror("Input Error", "Username already exists.")
            return
        hashed = bcrypt.hashpw(password.strip().encode(), bcrypt.gensalt()).decode()
        query = "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)"
        success = self.db.execute_query(query, (username.strip(), hashed, email.strip(), "Agent"))
        if not success:
            messagebox.showerror("Database Error", "Could not create agent.")
            return
        self._load_agents()
        self._refresh_users()
        self._set_agent_menu(self.assign_agent_menu, self.assign_agent_var, include_all=False)
        self._set_agent_menu(self.agent_filter_menu, self.agent_filter_var)

    def _toggle_user_state(self):
        """Toggle selected non-admin user enabled state using avatar marker."""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Select a user first.")
            return
        values = self.users_tree.item(selected[0], "values")
        user_id, username, _, role, state = values
        if role == "Admin":
            messagebox.showerror("Permission Error", "Admin account cannot be disabled.")
            return
        new_avatar = None if state == "Disabled" else f"{self.disabled_marker}{username}"
        updated = self.db.execute_query("UPDATE users SET avatar = %s WHERE user_id = %s", (new_avatar, int(user_id)))
        if not updated:
            messagebox.showerror("Update Error", "Could not update user state.")
            return
        self._refresh_users()

    def _load_agents(self):
        """Load all agent accounts into lookup dictionary by username."""
        rows = self.db.fetch_all("SELECT user_id, username FROM users WHERE role = %s", ("Agent",))
        self.agent_lookup = {row["username"]: row["user_id"] for row in rows}

    def _set_agent_menu(self, option_menu, variable, include_all=True):
        """Populate agent option menu entries from latest lookup mapping."""
        options = list(self.agent_lookup.keys())
        if include_all:
            options = ["All"] + options
        if not options:
            options = ["No Agents"]
        variable.set(options[0])
        menu = option_menu["menu"]
        menu.delete(0, "end")
        for option in options:
            menu.add_command(label=option, command=tk._setit(variable, option))
