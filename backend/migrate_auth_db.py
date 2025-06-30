#!/usr/bin/env python3
"""
Database migration script for authentication system.
Adds users table and user_id columns to existing tables.
"""

import asyncio
import aiosqlite
import os
import secrets
from datetime import datetime
from config import DB_PATH

def generate_user_id() -> str:
    """Generate a unique user ID"""
    return secrets.token_urlsafe(16)

async def migrate_auth_database():
    """Migrate database to support authentication system."""
    db_path = DB_PATH
    
    print(f"🔄 Migrating database: {db_path}")
    
    async with aiosqlite.connect(db_path) as conn:
        # Check if users table exists
        cursor = await conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        users_table_exists = await cursor.fetchone()
        
        if not users_table_exists:
            print("📝 Creating users table...")
            await conn.execute("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    is_guest BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            print("✅ Users table created")
        else:
            print("✅ Users table already exists")
        
        # Check if conversations table has user_id column
        cursor = await conn.execute("PRAGMA table_info(conversations)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'user_id' not in column_names:
            print("📝 Adding user_id column to conversations table...")
            await conn.execute("""
                ALTER TABLE conversations 
                ADD COLUMN user_id TEXT REFERENCES users(id)
            """)
            print("✅ user_id column added to conversations table")
        else:
            print("✅ user_id column already exists in conversations table")
        
        # Check if chat_history table has user_id column
        cursor = await conn.execute("PRAGMA table_info(chat_history)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'user_id' not in column_names:
            print("📝 Adding user_id column to chat_history table...")
            await conn.execute("""
                ALTER TABLE chat_history 
                ADD COLUMN user_id TEXT REFERENCES users(id)
            """)
            print("✅ user_id column added to chat_history table")
        else:
            print("✅ user_id column already exists in chat_history table")
        
        await conn.commit()
        print("✅ Database migration completed successfully!")

async def create_default_guest_user():
    """Create a default guest user for existing data."""
    db_path = DB_PATH
    
    print("👤 Creating default guest user for existing data...")
    
    async with aiosqlite.connect(db_path) as conn:
        # Check if default guest user exists
        cursor = await conn.execute("""
            SELECT id FROM users WHERE username = 'default_guest'
        """)
        existing_user = await cursor.fetchone()
        
        if not existing_user:
            user_id = generate_user_id()
            now = datetime.now().isoformat()
            
            await conn.execute("""
                INSERT INTO users (id, username, password_hash, is_guest, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, 'default_guest', None, True, now, now))
            
            # Update existing conversations to use default guest user
            await conn.execute("""
                UPDATE conversations 
                SET user_id = ? 
                WHERE user_id IS NULL
            """, (user_id,))
            
            # Update existing chat history to use default guest user
            await conn.execute("""
                UPDATE chat_history 
                SET user_id = ? 
                WHERE user_id IS NULL
            """, (user_id,))
            
            await conn.commit()
            print(f"✅ Default guest user created with ID: {user_id}")
            print("✅ Existing data migrated to default guest user")
        else:
            print("✅ Default guest user already exists")

async def main():
    """Run the complete migration."""
    print("🚀 Starting authentication database migration...")
    
    try:
        await migrate_auth_database()
        await create_default_guest_user()
        print("🎉 Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 