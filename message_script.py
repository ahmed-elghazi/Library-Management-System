import psycopg2

def connect_db():
    try:
        conn = psycopg2.connect(
            dbname='library_management',
            user='',          # Replace with your PostgreSQL username
            password='',  # Replace with your PostgreSQL password
            host='localhost',
            port='5432'
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def search_books(search_text):
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    cur = conn.cursor()
    try:
        # Explicitly cast parameter to text to match function signature
        cur.execute("SELECT * FROM search_books(%s::text)", (search_text,))
        books = cur.fetchall()
        return books
    except Exception as e:
        print(f"Search error: {e}")
        return "Error executing search."
    finally:
        conn.close()

def checkout_book(isbn, card_id):
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    cur = conn.cursor()
    try:
        # Pass parameters as text to match final SQL function signature
        cur.execute("SELECT checkout_book(%s::text, %s::text)", (isbn, card_id))
        message = cur.fetchone()[0]
        conn.commit()
        return message
    except Exception as e:
        print(f"Checkout error: {e}")
        return "Error processing checkout."
    finally:
        conn.close()

def return_book(loan_id):
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    cur = conn.cursor()
    try:
        cur.execute("SELECT return_book(%s)", (loan_id,))
        message = cur.fetchone()[0]
        conn.commit()
        return message
    except Exception as e:
        print(f"Return error: {e}")
        return "Error processing return."
    finally:
        conn.close()

def update_fines():
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    cur = conn.cursor()
    try:
        cur.execute("SELECT update_fines()")
        conn.commit()
        return "Fines updated successfully."
    except Exception as e:
        print(f"Fine update error: {e}")
        return "Error updating fines."
    finally:
        conn.close()

def pay_fine(loan_id):
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    cur = conn.cursor()
    try:
        cur.execute("SELECT pay_fine(%s)", (loan_id,))
        message = cur.fetchone()[0]
        conn.commit()
        return message
    except Exception as e:
        print(f"Fine payment error: {e}")
        return "Error processing fine payment."
    finally:
        conn.close()

def create_borrower(bname, ssn, address, phone):
    """
    Creates a new borrower.
    The final schema uses:
      - card_id as TEXT PRIMARY KEY,
      - bname for the borrower's name.
    This function generates a new numeric card_id (as a string).
    """
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    cur = conn.cursor()
    try:
        # Check for existing SSN
        cur.execute("SELECT * FROM borrower WHERE ssn = %s", (ssn,))
        if cur.fetchone():
            return "Error: A borrower with this SSN already exists."
        
        # Generate new card_id assuming existing IDs are numeric stored as text.
        cur.execute("SELECT MAX(CAST(card_id AS INTEGER)) FROM borrower")
        result = cur.fetchone()[0]
        new_card_id = str(int(result) + 1) if result is not None else "1000"
        
        cur.execute("""
            INSERT INTO borrower (card_id, bname, ssn, address, phone)
            VALUES (%s, %s, %s, %s, %s)
        """, (new_card_id, bname, ssn, address, phone))
        conn.commit()
        return f"Borrower created with Card ID: {new_card_id}"
    except Exception as e:
        print(f"Borrower creation error: {e}")
        return "Error creating borrower."
    finally:
        conn.close()

# ----------------------------
# Test Functions
# ----------------------------

def test_database_connection():
    print("=== Testing Database Connection ===")
    conn = connect_db()
    if conn:
        print("Database connection successful.")
        conn.close()
    else:
        print("Database connection failed.")

def test_book_search():
    print("=== Testing Book Search and Availability ===")
    results = search_books("william")
    print("Search Results:", results)

def test_book_loans():
    print("=== Testing Book Loans (Checkout) ===")
    # Create two borrowers
    borrower1 = create_borrower("John Doe", "123-45-6789", "123 Main St", "555-1234")
    borrower2 = create_borrower("Jane Smith", "987-65-4321", "456 Oak St", "555-5678")
    
    # Parse card IDs from the returned messages (format: "Borrower created with Card ID: <card_id>")
    try:
        card_id1 = borrower1.split(":")[1].strip()
        card_id2 = borrower2.split(":")[1].strip()
    except Exception as e:
        print("Error parsing card IDs:", e)
        return

    # Test valid checkout
    result = checkout_book("0923398364", card_id1)
    print("Checkout result (borrower1):", result)
    
    # Test checkout failure for an already checked out book
    result_dup = checkout_book("0923398364", card_id2)
    print("Checkout result (borrower2, duplicate):", result_dup)

def test_return_book():
    print("=== Testing Return Book ===")
    # For testing purposes, assume loan_id 1 exists
    result = return_book(1)
    print("Return result for loan_id 1:", result)

def test_update_fines():
    print("=== Testing Update Fines ===")
    result = update_fines()
    print(result)

def test_pay_fine():
    print("=== Testing Pay Fine ===")
    # For testing, assume loan_id 1 exists with an associated fine
    result = pay_fine(1)
    print("Pay Fine result for loan_id 1:", result)

def populate_database():
    """
    Inserts sample tuples into the database so that tests can run.
    Inserts sample rows into:
      - BOOK (with known ISBNs used in tests)
      - AUTHORS (sample author names)
      - BOOK_AUTHORS (associates each book with an author)
    """
    conn = connect_db()
    if not conn:
        print("Database connection failed in populate_database.")
        return
    cur = conn.cursor()
    try:
        # Insert sample books
        books = [
            ("0923398364", "Houses of Williamsburg"),
            ("ISBN2", "Book Two Title"),
            ("ISBN3", "Book Three Title"),
            ("ISBN4", "Book Four Title"),
            ("ISBN6", "Book Six Title"),
            ("ISBN7", "Book Seven Title")
        ]
        for isbn, title in books:
            # Use ON CONFLICT DO NOTHING to avoid duplicate errors on re-run
            cur.execute("INSERT INTO book (isbn, title) VALUES (%s, %s) ON CONFLICT DO NOTHING", (isbn, title))
        
        # Insert sample authors
        authors = [
            "William Jones",
            "Author Two",
            "Author Three",
            "Author Four",
            "Author Six",
            "Author Seven"
        ]
        author_ids = []
        for name in authors:
            cur.execute("INSERT INTO authors (name) VALUES (%s) RETURNING author_id", (name,))
            author_id = cur.fetchone()[0]
            author_ids.append(author_id)
        
        # Insert into BOOK_AUTHORS: assign one author per book (cycle through authors if needed)
        for i, (isbn, _) in enumerate(books):
            aid = author_ids[i % len(author_ids)]
            cur.execute("INSERT INTO book_authors (isbn, author_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (isbn, aid))
        
        conn.commit()
        print("Database populated with sample tuples.")
    except Exception as e:
        print("Error populating database:", e)
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    populate_database()
    test_database_connection()
    test_book_search()
    test_book_loans()
    test_return_book()
    test_update_fines()
    test_pay_fine()
