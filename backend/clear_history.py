#!/usr/bin/env python3
"""
Utility script to clear the chat history database.
"""

import sqlite3
from config import DB_PATH

def clear_chat_history():
    """Clear all chat history from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if table exists and has data
        c.execute("SELECT COUNT(*) FROM chat_history")
        count = c.fetchone()[0]
        
        if count == 0:
            print("Chat history is already empty.")
            return
        
        # Clear all records
        c.execute('DELETE FROM chat_history')
        conn.commit()
        conn.close()
        
        print(f"Successfully cleared {count} chat history records.")
        
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("Chat history table doesn't exist yet. No history to clear.")
        else:
            print(f"Database error: {e}")
    except Exception as e:
        print(f"Error clearing chat history: {e}")

if __name__ == "__main__":
    print("Clearing chat history...")
    clear_chat_history()
    print("Done!") 