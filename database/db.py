import sqlite3
from pathlib import Path

# Assuming data directory is relative to the project root
DB_PATH = Path("data/tms.db")

def get_connection() -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database."""
    # Ensure the parent directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Enable dict-like row access
    conn.row_factory = sqlite3.Row
    
    # Enforce foreign keys (good practice for SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    
    return conn
