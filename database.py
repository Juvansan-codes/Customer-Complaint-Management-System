import mysql.connector

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "mysql123"
DB_NAME = "complaint_db"


class Database:
    """Handle all MySQL operations for the application."""

    def __init__(self):
        """Initialize empty connection and cursor objects."""
        self.connection = None
        self.cursor = None

    def connect(self):
        """Connect to the MySQL database using configured constants."""
        try:
            self.connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
            )
            self.cursor = self.connection.cursor(dictionary=True)
            print("Connected")
        except mysql.connector.Error as db_error:
            print(f"Database connection error: {db_error}")

    def execute_query(self, sql, params=None):
        """Execute write query and commit the transaction safely."""
        try:
            self.cursor.execute(sql, params or ())
            self.connection.commit()
            if sql.strip().lower().startswith("insert"):
                return self.cursor.lastrowid
            return True
        except mysql.connector.Error as db_error:
            print(f"Query execution error: {db_error}")
            return None

    def fetch_all(self, sql, params=None):
        """Fetch and return all rows as a list of dictionaries."""
        try:
            self.cursor.execute(sql, params or ())
            return self.cursor.fetchall()
        except mysql.connector.Error as db_error:
            print(f"Fetch all error: {db_error}")
            return []

    def fetch_one(self, sql, params=None):
        """Fetch and return one row as dictionary or None."""
        try:
            self.cursor.execute(sql, params or ())
            return self.cursor.fetchone()
        except mysql.connector.Error as db_error:
            print(f"Fetch one error: {db_error}")
            return None

    def close(self):
        """Close cursor and connection if open."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except mysql.connector.Error as db_error:
            print(f"Close connection error: {db_error}")


if __name__ == "__main__":
    db = Database()
    db.connect()
    db.close()
