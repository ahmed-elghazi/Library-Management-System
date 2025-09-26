# Library Management System – Milestone 2

## Description
This is the Milestone 2 submission for the CS-4347 SQL Library Project. This version includes:
- A PostgreSQL-based backend with an updated schema and stored procedures for managing a library system.
- A Python script that tests all core functionalities including search, checkout, return, borrower management, and fine handling.
- Improvements in fine calculation logic and error messaging.

## Requirements
- Python 3.8+
- PostgreSQL 13+
- `psycopg2` Python package

## Setup Instructions

### 1. Install Dependencies
```bash
pip install psycopg2
```

### 2. Create PostgreSQL Database
```bash
createdb library_management
```

### 3. Execute the SQL File
```bash
psql -U your_user -d library_management -f Library_Management_SQL.sql
```
- replace your_user with your PostgreSQL username

### 4. Run Python Tests
```bash
python message_script.py
```

### Test Cases Implemented in Main
- `Database Connection Test`: Verifies that the connection to the PostgreSQL database is successful.
- `Book Search Test`: Tests searching by a substring, by full ISBN, and verifies case insensitivity. Confirms that search results include four columns: ISBN, title, authors, and status.
- `Book Loans (Checkout) Test`: Validates that a book can be successfully checked out. Prevents duplicate checkout for the same book. Enforces that a borrower cannot have more than three active loans or check out if they have an unpaid fine.
- `Return Book Test`: Confirms that returning a book updates the record correctly and provides appropriate feedback.
- `Update Fines Test`: Updates fines for both returned and overdue loans using correct date arithmetic.
- `Pay Fine Test`: Ensures that fine payment occurs only if a fine exists and the book has been returned.
- `Check-In Test`: Validates that loans can be located and checked in successfully.



## Files
- `Library_Management_SQL.sql`: Contains schema + all required stored functions.
- `library_management_python.py`: Python code that performs testing on all milestone functionalities.
- `README.md`: This file.

## Notes
- Make sure PostgreSQL is running and accessible at `localhost:5432`.
- Default database user is `username` with password 'testing-password`. Update `connect_db()` in Python script if needed.
- The final version includes improved error handling, robust fine calculation (with corrected date arithmetic), and consistent data types (using TEXT where appropriate).
