import sqlite3
import json
import os
from typing import Dict, Any, List, Tuple

# Define the database file path
DB_PATH = 'kernel_monitor.db'

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    # The database file will be created in the main project directory
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name (e.g., row['username'])
    return conn

def initialize_db():
    """Creates the necessary tables if they do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table (Stores user credentials)
    # password_hash will store the hashed and salted password (using a library like bcrypt later)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)
    
    # 2. History Table (Stores session snapshots for graphing/comparison)
    # metrics_json stores the full dictionary of metrics as a JSON string
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            metrics_json TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialization complete: Tables (users, history) checked/created.")

def save_session_snapshot(user_id: int, metrics: Dict[str, Any], status: str) -> None:
    """Saves a single snapshot of system metrics and health status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert the complex metrics dictionary into a JSON string for storage
    metrics_str = json.dumps(metrics)
    
    cursor.execute(
        "INSERT INTO history (user_id, timestamp, metrics_json, status) VALUES (?, ?, ?, ?)",
        (user_id, metrics['timestamp'], metrics_str, status)
    )
    
    conn.commit()
    conn.close()

def get_user_history(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves the last N metric snapshots for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Order by ID descending to get the newest snapshots first
    cursor.execute(
        "SELECT * FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    )
    
    history_records = []
    for row in cursor.fetchall():
        # Re-convert the JSON string back into a Python dictionary
        record = dict(row)
        record['metrics_json'] = json.loads(record['metrics_json'])
        history_records.append(record)
        
    conn.close()
    return history_records

if __name__ == '__main__':
    # Initialize the database file when running this script directly
    initialize_db()