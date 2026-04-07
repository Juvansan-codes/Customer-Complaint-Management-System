# Customer Complaint Management System

Desktop application for complaint ticket lifecycle management with role-based access for **Customer**, **Agent**, and **Admin**.

## Tech Stack

- Python 3.10+
- Tkinter + ttk (desktop UI)
- MySQL 8.x (`mysql-connector-python`)
- Matplotlib (embedded admin dashboard charts)
- Pillow (image handling)
- bcrypt (password hashing)

## Features

- Role-based login and routing (Admin, Agent, Customer)
- Customer ticket submission with auto-priority detection
- Screenshot attachment and preview for tickets
- Agent ticket assignment workflow, status updates, and remarks
- Admin dashboard with charts, filters, reports, and CSV export
- SLA color coding in ticket tables

## Project Structure

- `main.py` - Entry point
- `database.py` - Database connection and query layer
- `models.py` - OOP domain models and role logic
- `utils.py` - Utility functions and constants
- `image_utils.py` - All Pillow image operations
- `login_window.py` - Login and role routing
- `register_window.py` - Customer registration
- `customer_window.py` - Customer dashboard
- `agent_window.py` - Agent dashboard
- `admin_window.py` - Admin dashboard
- `schema.sql` - MySQL schema and admin seed
- `requirements.txt` - Python dependencies

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run `schema.sql` in MySQL Workbench or MySQL CLI.
4. Update DB credentials in `database.py`:
   - `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`
5. Add your logo file:
   - `assets/logo.png`
6. Run the app:
   - `python main.py`

## Default Admin

A seed admin user is inserted by `schema.sql`.

- Username: `admin`
- Password: `admin123`

## Notes

- Ensure MySQL service is running before launching the app.
- Ticket screenshots are saved under `assets/screenshots/`.
- Grid layout is used for Tkinter window composition.
