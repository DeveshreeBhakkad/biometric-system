"""
database.py
SQLite database layer for Biometric KYC System
Jalgaon People's Co-operative Bank
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "biometric_kyc.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def create_tables():
    """Run once on app startup — creates all tables if not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: customers — stores KYC info
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name       TEXT NOT NULL,
            mobile          TEXT,
            photo           BLOB,
            fingerprint_img BLOB,
            enrolled_date   TEXT,
            enrolled_time   TEXT
        )
    """)

    # Table 2: loans — linked to customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            loan_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id     INTEGER NOT NULL,
            loan_type       TEXT,
            loan_amount     REAL,
            account_number  TEXT,
            loan_date       TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Table 3: payments — every visit recorded here
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id     INTEGER NOT NULL,
            amount_paid     REAL,
            fingerprint_img BLOB,
            payment_date    TEXT,
            payment_time    TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables created successfully.")


# ─────────────────────────────────────────
#  ENROLLMENT FUNCTIONS
# ─────────────────────────────────────────

def save_customer(full_name, mobile, photo_bytes, fingerprint_bytes):
    """Save a new customer and return their generated customer_id."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("""
        INSERT INTO customers (full_name, mobile, photo, fingerprint_img, enrolled_date, enrolled_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        full_name,
        mobile,
        photo_bytes,
        fingerprint_bytes,
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M:%S")
    ))
    conn.commit()
    customer_id = cursor.lastrowid
    conn.close()
    print(f"[DB] Customer saved — ID: {customer_id}")
    return customer_id


def save_loan(customer_id, loan_type, loan_amount, account_number):
    """Save loan details linked to a customer."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO loans (customer_id, loan_type, loan_amount, account_number, loan_date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        customer_id,
        loan_type,
        loan_amount,
        account_number,
        datetime.now().strftime("%Y-%m-%d")
    ))
    conn.commit()
    conn.close()
    print(f"[DB] Loan saved for customer ID: {customer_id}")


# ─────────────────────────────────────────
#  FINGERPRINT CHECK
# ─────────────────────────────────────────

def get_all_fingerprints():
    """
    Returns list of (customer_id, fingerprint_bytes) for all enrolled customers.
    Used during payment scan to check if fingerprint is already registered.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id, fingerprint_img FROM customers")
    rows = cursor.fetchall()
    conn.close()
    return [(row["customer_id"], row["fingerprint_img"]) for row in rows]


def get_customer_by_id(customer_id):
    """Fetch full customer details by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, l.loan_type, l.loan_amount, l.account_number
        FROM customers c
        LEFT JOIN loans l ON c.customer_id = l.customer_id
        WHERE c.customer_id = ?
    """, (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def search_customers(name):
    """Search customers by name (partial match)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.customer_id, c.full_name, c.mobile, c.enrolled_date,
               l.loan_type, l.loan_amount, l.account_number
        FROM customers c
        LEFT JOIN loans l ON c.customer_id = l.customer_id
        WHERE c.full_name LIKE ?
    """, (f"%{name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ─────────────────────────────────────────
#  PAYMENT FUNCTIONS
# ─────────────────────────────────────────

def save_payment(customer_id, amount_paid, fingerprint_bytes):
    """Record a payment with fingerprint proof and timestamp."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("""
        INSERT INTO payments (customer_id, amount_paid, fingerprint_img, payment_date, payment_time)
        VALUES (?, ?, ?, ?, ?)
    """, (
        customer_id,
        amount_paid,
        fingerprint_bytes,
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M:%S")
    ))
    conn.commit()
    conn.close()
    print(f"[DB] Payment saved — Customer: {customer_id}, Amount: {amount_paid}")


def get_payment_history(customer_id):
    """Get all payments for a customer, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT payment_id, amount_paid, payment_date, payment_time
        FROM payments
        WHERE customer_id = ?
        ORDER BY payment_date DESC, payment_time DESC
    """, (customer_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_total_paid(customer_id):
    """Get total amount paid by a customer across all payments."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(amount_paid) as total FROM payments
        WHERE customer_id = ?
    """, (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return row["total"] if row["total"] else 0.0


# ─────────────────────────────────────────
#  ENTRY POINT — test it directly
# ─────────────────────────────────────────

if __name__ == "__main__":
    create_tables()
    print("[DB] Database initialized at:", DB_PATH)
    print("[DB] All tables ready.")