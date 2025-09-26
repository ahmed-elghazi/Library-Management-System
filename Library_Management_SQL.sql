-- Library Management System SQL File

-- DROP tables if they exist
DROP TABLE IF EXISTS FINES, BOOK_LOANS, BOOK_AUTHORS, AUTHORS, BOOK, BORROWER CASCADE;

-- BOOK
CREATE TABLE BOOK (
    isbn TEXT PRIMARY KEY,
    title TEXT NOT NULL
);

-- AUTHORS
CREATE TABLE AUTHORS (
    author_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

-- BOOK_AUTHORS
CREATE TABLE BOOK_AUTHORS (
    isbn TEXT REFERENCES BOOK(isbn),
    author_id INT REFERENCES AUTHORS(author_id),
    PRIMARY KEY (isbn, author_id)
);

-- BORROWER
CREATE TABLE BORROWER (
    card_id TEXT PRIMARY KEY,
    bname TEXT NOT NULL,
    ssn TEXT UNIQUE NOT NULL,
    address TEXT NOT NULL,
    phone TEXT
);

-- BOOK_LOANS
CREATE TABLE BOOK_LOANS (
    loan_id SERIAL PRIMARY KEY,
    isbn TEXT REFERENCES BOOK(isbn),
    card_id TEXT REFERENCES BORROWER(card_id),
    date_out DATE DEFAULT CURRENT_DATE,
    due_date DATE,
    date_in DATE
);

-- FINES
CREATE TABLE FINES (
    loan_id INT PRIMARY KEY REFERENCES BOOK_LOANS(loan_id),
    fine_amt NUMERIC(5,2) DEFAULT 0.00,
    paid BOOLEAN DEFAULT FALSE
);

-- -----------------------------------------------------
-- FUNCTIONS
-- -----------------------------------------------------

-- 1. Search Books
CREATE OR REPLACE FUNCTION search_books(search_text TEXT)
RETURNS TABLE (
    isbn TEXT,
    title TEXT,
    authors TEXT,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.isbn,
        b.title,
        STRING_AGG(a.name, ', ') AS authors,
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM book_loans bl WHERE bl.isbn = b.isbn AND bl.date_in IS NULL
            ) THEN 'OUT'
            ELSE 'IN'
        END AS status
    FROM book b
    JOIN book_authors ba ON ba.isbn = b.isbn
    JOIN authors a ON a.author_id = ba.author_id
    WHERE 
        LOWER(b.title) LIKE LOWER('%' || search_text || '%')
        OR LOWER(a.name) LIKE LOWER('%' || search_text || '%')
        OR b.isbn = search_text
    GROUP BY b.isbn, b.title;
END;
$$ LANGUAGE plpgsql;

-- 2. Checkout Book
CREATE OR REPLACE FUNCTION checkout_book(p_isbn TEXT, p_card_id TEXT)
RETURNS TEXT AS $$
DECLARE
    active_loans INT;
    unpaid_fine_exists BOOLEAN;
    book_unavailable BOOLEAN;
BEGIN
    SELECT COUNT(*) INTO active_loans 
    FROM book_loans WHERE card_id = p_card_id AND date_in IS NULL;

    IF active_loans >= 3 THEN
        RETURN 'Checkout failed: Borrower has 3 active loans.';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM fines f
        JOIN book_loans bl ON bl.loan_id = f.loan_id
        WHERE bl.card_id = p_card_id AND f.paid = FALSE
    ) INTO unpaid_fine_exists;

    IF unpaid_fine_exists THEN
        RETURN 'Checkout failed: Borrower has unpaid fines.';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM book_loans 
        WHERE isbn = p_isbn AND date_in IS NULL
    ) INTO book_unavailable;

    IF book_unavailable THEN
        RETURN 'Checkout failed: Book is currently unavailable.';
    END IF;

    INSERT INTO book_loans(isbn, card_id, date_out, due_date)
    VALUES (p_isbn, p_card_id, CURRENT_DATE, CURRENT_DATE + INTERVAL '14 days');

    RETURN 'Checkout successful';
END;
$$ LANGUAGE plpgsql;

-- 3. Return Book
CREATE OR REPLACE FUNCTION return_book(p_loan_id INT)
RETURNS TEXT AS $$
BEGIN
    UPDATE book_loans 
    SET date_in = CURRENT_DATE 
    WHERE loan_id = p_loan_id AND date_in IS NULL;

    IF FOUND THEN
        RETURN 'Return successful';
    ELSE
        RETURN 'Return failed: Book already returned or invalid loan ID';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 4. Update Fines
CREATE OR REPLACE FUNCTION update_fines()
RETURNS VOID AS $$
BEGIN
    -- Update existing fines for returned books: use the actual overdue days (date_in - due_date)
    UPDATE fines f
    SET fine_amt = ROUND(GREATEST(bl.date_in - bl.due_date, 0) * 0.25, 2)
    FROM book_loans bl
    WHERE f.loan_id = bl.loan_id 
      AND bl.date_in IS NOT NULL 
      AND f.paid = FALSE;

    -- Update fines for books not yet returned: use CURRENT_DATE as the reference for overdue days
    UPDATE fines f
    SET fine_amt = ROUND(GREATEST(CURRENT_DATE - bl.due_date, 0) * 0.25, 2)
    FROM book_loans bl
    WHERE f.loan_id = bl.loan_id 
      AND bl.date_in IS NULL 
      AND f.paid = FALSE;

    -- Insert new fines for overdue loans that don't already have a fine record.
    INSERT INTO fines (loan_id, fine_amt, paid)
    SELECT bl.loan_id,
           ROUND(GREATEST(CURRENT_DATE - bl.due_date, 0) * 0.25, 2),
           FALSE
    FROM book_loans bl
    LEFT JOIN fines f ON f.loan_id = bl.loan_id
    WHERE f.loan_id IS NULL 
      AND (
            (bl.date_in IS NULL AND CURRENT_DATE > bl.due_date)
         OR (bl.date_in IS NOT NULL AND bl.date_in > bl.due_date)
      );
END;
$$ LANGUAGE plpgsql;

-- 5. Pay Fine
CREATE OR REPLACE FUNCTION pay_fine(p_loan_id INT)
RETURNS TEXT AS $$
DECLARE
    already_returned BOOLEAN;
BEGIN
    SELECT date_in IS NOT NULL INTO already_returned FROM book_loans WHERE loan_id = p_loan_id;

    IF NOT already_returned THEN
        RETURN 'Payment failed: Book not returned yet';
    END IF;

    UPDATE fines 
    SET paid = TRUE, fine_amt = 0 
    WHERE loan_id = p_loan_id AND paid = FALSE;

    IF FOUND THEN
        RETURN 'Payment successful';
    ELSE
        RETURN 'Payment failed: No unpaid fine found';
    END IF;
END;
$$ LANGUAGE plpgsql;