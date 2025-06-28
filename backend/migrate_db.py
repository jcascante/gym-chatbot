#!/usr/bin/env python3
"""
Database migration script to add citations column to existing chat_history table.
"""

import sqlite3
from config import DB_PATH

def migrate_database():
    """Add citations column to existing chat_history table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if citations column exists
        c.execute("PRAGMA table_info(chat_history)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'citations' not in columns:
            print("Adding citations column to chat_history table...")
            c.execute("ALTER TABLE chat_history ADD COLUMN citations TEXT")
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Citations column already exists. No migration needed.")
        
        conn.close()
        
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    print("Checking database schema...")
    migrate_database()
    print("Done!") 