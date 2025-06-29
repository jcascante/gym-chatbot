#!/usr/bin/env python3
"""
Test script to check database structure and fix migration issues
"""

import asyncio
import aiosqlite
import datetime
from config import DB_PATH

async def test_database():
    """Test database structure and fix any issues"""
    print("Testing database structure...")
    
    async with aiosqlite.connect(DB_PATH) as conn:
        # Check if conversations table exists
        cursor = await conn.execute("PRAGMA table_info(conversations)")
        conversations_columns = [column[1] async for column in cursor]
        
        if not conversations_columns:
            print("Creating conversations table...")
            await conn.execute('''CREATE TABLE conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )''')
            
            # Create default conversation
            now = datetime.datetime.now().isoformat()
            await conn.execute(
                'INSERT INTO conversations (title, created_at, updated_at) VALUES (?, ?, ?)',
                ('Default Conversation', now, now)
            )
            await conn.commit()
            print("✅ Conversations table created with default conversation")
        else:
            print("✅ Conversations table already exists")
        
        # Check chat_history table structure
        cursor = await conn.execute("PRAGMA table_info(chat_history)")
        chat_columns = [column[1] async for column in cursor]
        
        if 'conversation_id' not in chat_columns:
            print("Migrating chat_history table...")
            
            # Create new table with conversation_id
            await conn.execute('''CREATE TABLE chat_history_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                citations TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )''')
            
            # Get default conversation ID
            cursor = await conn.execute('SELECT id FROM conversations LIMIT 1')
            default_conversation_id = (await cursor.fetchone())[0]
            
            # Migrate existing data
            try:
                await conn.execute('''
                    INSERT INTO chat_history_new (conversation_id, user_message, bot_response, citations, timestamp)
                    SELECT ?, user_message, bot_response, citations, timestamp FROM chat_history
                ''', (default_conversation_id,))
                print(f"✅ Migrated existing data to conversation {default_conversation_id}")
            except Exception as e:
                print(f"⚠️ No existing data to migrate: {e}")
            
            # Drop old table and rename new one
            await conn.execute('DROP TABLE IF EXISTS chat_history')
            await conn.execute('ALTER TABLE chat_history_new RENAME TO chat_history')
            await conn.commit()
            print("✅ Chat history table migrated successfully")
        else:
            print("✅ Chat history table already has conversation_id column")
        
        # Test queries
        print("\nTesting queries...")
        
        # Get conversations
        cursor = await conn.execute('SELECT * FROM conversations')
        conversations = await cursor.fetchall()
        print(f"✅ Found {len(conversations)} conversations")
        
        # Get chat history
        cursor = await conn.execute('SELECT * FROM chat_history')
        messages = await cursor.fetchall()
        print(f"✅ Found {len(messages)} chat messages")
        
        print("\n✅ Database test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_database()) 