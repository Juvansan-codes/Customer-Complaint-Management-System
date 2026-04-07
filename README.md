# Customer Complaint Management System (Micro Project)

Simple first-year level Python project using Tkinter + MySQL.

## Tech Stack

- Python
- Tkinter (GUI)
- MySQL (`mysql-connector-python`)
- Matplotlib (simple graph)

## Project Files

- `main.py`: complete application code
- `schema.sql`: database schema and sample users
- `requirements.txt`: required Python packages

## Features

- Register new user (Admin / Agent / Customer)
- Login using username and password from database
- Customer: add complaint, view own complaints
- Agent: view all complaints, update status
- Admin: view all complaints, update status
- Admin: export complaints to CSV
- Admin: show bar graph (Complaints by Status)

## Database Tables

1. `users(username, password, role)`
2. `complaints(id, username, issue, status)`

## Setup Steps

1. Create and activate virtual environment.
2. Install packages:
   - `pip install -r requirements.txt`
3. Run `schema.sql` in MySQL Workbench.
4. Open `main.py` and set database password:
   - `DB_PASS = "your_password"`
5. Run app:
   - `python main.py`

## Sample Login Users

- Admin: `admin` / `admin123`
- Agent: `agent1` / `agent123`
- Customer: `customer1` / `cust123`

## Note

This is a beginner-friendly micro project designed for easy explanation in viva.
