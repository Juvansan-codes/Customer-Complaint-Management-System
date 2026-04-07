from datetime import datetime

import bcrypt

from database import Database as CoreDatabase
from utils import auto_priority, check_sla_color


class User:
    """Represent a base user entity with shared authentication behavior."""

    def __init__(self, user_id, username, password, email, role, avatar=None):
        """Initialize common user attributes for all roles."""
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.avatar = avatar

    @staticmethod
    def login(db, username, password):
        """Authenticate user and return a role-specific object if valid."""
        query = "SELECT * FROM users WHERE username = %s"
        row = db.fetch_one(query, (username,))
        if not row:
            return None
        avatar_value = row.get("avatar") or ""
        if avatar_value.startswith("__DISABLED__"):
            return None
        if not bcrypt.checkpw(password.encode(), row["password"].encode()):
            return None
        return User._build_user(row)

    @staticmethod
    def _build_user(row):
        """Build and return an object of the matching role subclass."""
        role_map = {"Customer": Customer, "Agent": Agent, "Admin": Admin}
        role_class = role_map.get(row["role"], User)
        return role_class(
            row["user_id"],
            row["username"],
            row["password"],
            row["email"],
            row["role"],
            row.get("avatar"),
        )

    def logout(self):
        """Return a logout status indicator for UI flow."""
        return True

    def get_details(self):
        """Return common user information as a dictionary."""
        return {"user_id": self.user_id, "username": self.username, "role": self.role}


class Customer(User):
    """Represent customer actions such as ticket creation and feedback."""

    def __init__(self, user_id, username, password, email, role, avatar=None):
        """Initialize customer with local complaint history list."""
        super().__init__(user_id, username, password, email, role, avatar)
        self.complaint_history = []

    def submit_ticket(self, db, category, complaint, screenshot=None):
        """Create a ticket, store it in DB, and append to complaint history."""
        priority = auto_priority(complaint)
        query = (
            "INSERT INTO tickets (customer_id, category, complaint, screenshot, priority) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        params = (self.user_id, category, complaint, screenshot, priority)
        ticket_id = db.execute_query(query, params)
        if ticket_id:
            self.complaint_history.append(
                {"ticket_id": ticket_id, "category": category, "priority": priority}
            )
        return ticket_id

    def track_ticket(self, db, ticket_id):
        """Return one owned ticket detail by ticket identifier."""
        query = "SELECT * FROM tickets WHERE ticket_id = %s AND customer_id = %s"
        return db.fetch_one(query, (ticket_id, self.user_id))

    def rate_ticket(self, db, ticket_id, rating, comment):
        """Save ticket feedback for a closed customer ticket."""
        query = (
            "INSERT INTO feedback (ticket_id, customer_id, rating, comments) "
            "VALUES (%s, %s, %s, %s)"
        )
        params = (ticket_id, self.user_id, rating, comment)
        return db.execute_query(query, params)


class Agent(User):
    """Represent agent workflow for assigned tickets and remarks."""

    def __init__(self, user_id, username, password, email, role, avatar=None):
        """Initialize agent with assigned ticket cache list."""
        super().__init__(user_id, username, password, email, role, avatar)
        self.assigned_tickets = []

    def update_status(self, db, ticket_id, new_status):
        """Update assigned ticket status and manage resolved timestamp."""
        resolved_at = datetime.now() if new_status == "Closed" else None
        query = "UPDATE tickets SET status = %s, resolved_at = %s WHERE ticket_id = %s"
        return db.execute_query(query, (new_status, resolved_at, ticket_id))

    def add_remark(self, db, ticket_id, note):
        """Add an agent remark entry for a ticket."""
        query = "INSERT INTO remarks (ticket_id, agent_id, note) VALUES (%s, %s, %s)"
        return db.execute_query(query, (ticket_id, self.user_id, note))

    def view_assigned(self, db):
        """Load assigned tickets list and return it."""
        query = (
            "SELECT t.*, u.username AS customer_name FROM tickets t "
            "JOIN users u ON t.customer_id = u.user_id WHERE t.assigned_to = %s"
        )
        self.assigned_tickets = db.fetch_all(query, (self.user_id,))
        return self.assigned_tickets

    def get_details(self):
        """Return agent details including a simple performance score metric."""
        total = len(self.assigned_tickets)
        closed = sum(1 for ticket in self.assigned_tickets if ticket["status"] == "Closed")
        score = 0 if total == 0 else round((closed / total) * 100, 2)
        details = super().get_details()
        details["performance_score"] = score
        return details


class Admin(User):
    """Represent administrative actions for system-wide operations."""

    def assign_ticket(self, db, ticket_id, agent_id):
        """Assign open ticket to an agent and mark it in progress."""
        query = "UPDATE tickets SET assigned_to = %s, status = %s WHERE ticket_id = %s"
        return db.execute_query(query, (agent_id, "In Progress", ticket_id))

    def delete_ticket(self, db, ticket_id):
        """Delete ticket and dependent rows from feedback and remarks tables."""
        db.execute_query("DELETE FROM remarks WHERE ticket_id = %s", (ticket_id,))
        db.execute_query("DELETE FROM feedback WHERE ticket_id = %s", (ticket_id,))
        return db.execute_query("DELETE FROM tickets WHERE ticket_id = %s", (ticket_id,))

    def generate_report(self, db, filters):
        """Return filtered ticket report rows using list-comprehension filtering."""
        rows = db.fetch_all("SELECT * FROM tickets ORDER BY created_at DESC")
        return [row for row in rows if self._match_report_filter(row, filters)]

    def _match_report_filter(self, row, filters):
        """Evaluate if a ticket row satisfies selected report filters."""
        status_ok = filters.get("status", "All") in ["All", row["status"]]
        priority_ok = filters.get("priority", "All") in ["All", row["priority"]]
        agent_ok = filters.get("agent", "All") in ["All", str(row.get("assigned_to") or "")]
        return status_ok and priority_ok and agent_ok

    def get_details(self):
        """Return admin details including quick system counters."""
        details = super().get_details()
        details["system_stats"] = {"scope": "global"}
        return details


class Ticket:
    """Represent a single ticket row with utility helper behaviors."""

    def __init__(self, **kwargs):
        """Store incoming ticket fields as instance attributes."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def auto_priority(self, text):
        """Return auto-detected priority from complaint text."""
        return auto_priority(text)

    def check_sla_breach(self):
        """Return SLA color tag based on current age and priority."""
        created_at = self.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return check_sla_color(self.priority, created_at)

    def get_age(self):
        """Return age timedelta from creation to current timestamp."""
        created_at = self.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return datetime.now() - created_at


class Database(CoreDatabase):
    """Expose database class in models module for OOP checklist compatibility."""

    pass
