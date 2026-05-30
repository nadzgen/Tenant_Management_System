"""SQLite integration stub.

Replace the in-memory accessors in tms.mock_data with real sqlite3 calls.

Suggested schema:
    CREATE TABLE tenants  (id TEXT PRIMARY KEY, name TEXT, contact TEXT,
                           age INTEGER, sex TEXT, move_in DATE, room TEXT);
    CREATE TABLE rooms    (id TEXT PRIMARY KEY, number TEXT, type TEXT,
                           capacity INTEGER, rent REAL, status TEXT);
    CREATE TABLE payments (id TEXT PRIMARY KEY, tenant_id TEXT, amount REAL,
                           due_date DATE, paid_on DATE, status TEXT);

Example connection helper:

    import sqlite3
    def connect(path="tms.db"):
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn
"""
# TODO: implement real DB layer and swap mock_data calls for these.
