"""
Tests for database operations
"""

import pytest
import aiosqlite
from datetime import datetime
import sys
from pathlib import Path
import json

# Add the parent directory to the path so we can import from main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import (
    init_db_async, get_chat_history_async, save_chat_async, 
    create_conversation_async, get_conversations_async,
    update_conversation_title_async, delete_conversation_async
)

class TestDatabaseOperations:
    """Test database operations"""
    
    @pytest.mark.asyncio
    async def test_init_database(self, test_db_path):
        """Test database initialization"""
        # Initialize the database
        await init_db_async()
        
        # Check that tables exist
        async with aiosqlite.connect(test_db_path) as conn:
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] async for row in cursor]
            
            assert 'users' in tables
            assert 'conversations' in tables
            assert 'chat_history' in tables
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, test_db_path):
        """Test creating a conversation"""
        user_id = "test_user_123"
        title = "Test Conversation"
        
        conversation_id = await create_conversation_async(user_id, title)
        
        assert conversation_id is not None
        assert isinstance(conversation_id, int)
        
        # Verify the conversation was created
        async with aiosqlite.connect(test_db_path) as conn:
            cursor = await conn.execute(
                'SELECT title FROM conversations WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            result = await cursor.fetchone()
            assert result is not None
            assert result[0] == title
    
    @pytest.mark.asyncio
    async def test_create_conversation_no_title(self, test_db_path):
        """Test creating conversation without title"""
        user_id = "test_user_123"
        
        conversation_id = await create_conversation_async(user_id)
        
        assert conversation_id is not None
        assert isinstance(conversation_id, int)
        
        # Verify the conversation was created with default title
        async with aiosqlite.connect(test_db_path) as conn:
            cursor = await conn.execute(
                'SELECT title FROM conversations WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            result = await cursor.fetchone()
            assert result is not None
            assert "Conversation" in result[0]
    
    @pytest.mark.asyncio
    async def test_save_chat_message(self, test_db_path):
        """Test saving chat message"""
        user_id = "test_user_123"
        conversation_id = await create_conversation_async(user_id, "Test Conversation")
        user_message = "What is strength training?"
        bot_response = "Strength training is a form of exercise..."
        citations = ["document1.pdf", "document2.pdf"]
        
        await save_chat_async(user_id, conversation_id, user_message, bot_response, citations)
        
        # Verify the message was saved
        async with aiosqlite.connect(test_db_path) as conn:
            cursor = await conn.execute(
                'SELECT user_message, bot_response, citations FROM chat_history WHERE conversation_id = ?',
                (conversation_id,)
            )
            result = await cursor.fetchone()
            assert result is not None
            assert result[0] == user_message
            assert result[1] == bot_response
            assert result[2] == json.dumps(citations)
    
    @pytest.mark.asyncio
    async def test_get_chat_history(self, test_db_path):
        """Test getting chat history"""
        user_id = "test_user_123"
        conversation_id = await create_conversation_async(user_id, "Test Conversation")
        
        # Save some messages
        user_msg = "What is strength training?"
        bot_msg = "Strength training is a form of exercise..."
        citations = ["document1.pdf"]
        
        await save_chat_async(user_id, conversation_id, user_msg, bot_msg, citations)
        
        # Get chat history
        history = await get_chat_history_async(user_id, conversation_id)
        
        assert len(history) == 1
        assert history[0]['user_message'] == user_msg
        assert history[0]['bot_response'] == bot_msg
        assert history[0]['citations'] == citations
    
    @pytest.mark.asyncio
    async def test_get_conversations(self, test_db_path):
        """Test getting conversations for a user"""
        user_id = "test_user_123"
        
        # Create multiple conversations
        await create_conversation_async(user_id, "Conversation 1")
        await create_conversation_async(user_id, "Conversation 2")
        await create_conversation_async(user_id, "Conversation 3")
        
        conversations = await get_conversations_async(user_id)
        
        assert len(conversations) == 3
        assert all(conv['user_id'] == user_id for conv in conversations)
        assert any(conv['title'] == "Conversation 1" for conv in conversations)
        assert any(conv['title'] == "Conversation 2" for conv in conversations)
        assert any(conv['title'] == "Conversation 3" for conv in conversations)
    
    @pytest.mark.asyncio
    async def test_update_conversation_title(self, test_db_path):
        """Test updating conversation title"""
        user_id = "test_user_123"
        conversation_id = await create_conversation_async(user_id, "Original Title")
        new_title = "Updated Title"
        
        await update_conversation_title_async(user_id, conversation_id, new_title)
        
        # Verify the title was updated
        async with aiosqlite.connect(test_db_path) as conn:
            cursor = await conn.execute(
                'SELECT title FROM conversations WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            result = await cursor.fetchone()
            assert result is not None
            assert result[0] == new_title
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, test_db_path):
        """Test deleting a conversation"""
        user_id = "test_user_123"
        conversation_id = await create_conversation_async(user_id, "To Delete")
        
        # Add some chat messages
        await save_chat_async(user_id, conversation_id, "Test", "Response", [])
        
        # Delete the conversation
        await delete_conversation_async(user_id, conversation_id)
        
        # Verify the conversation was deleted
        async with aiosqlite.connect(test_db_path) as conn:
            cursor = await conn.execute(
                'SELECT id FROM conversations WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            result = await cursor.fetchone()
            assert result is None
            
            # Verify chat messages were also deleted
            cursor = await conn.execute(
                'SELECT id FROM chat_history WHERE conversation_id = ?',
                (conversation_id,)
            )
            result = await cursor.fetchone()
            assert result is None
    
    @pytest.mark.asyncio
    async def test_chat_history_limit(self, test_db_path):
        """Test chat history limit"""
        user_id = "test_user_123"
        conversation_id = await create_conversation_async(user_id, "Test Conversation")
        
        # Add more than 50 messages
        for i in range(60):
            await save_chat_async(user_id, conversation_id, f"Message {i}", f"Response {i}", [])
        
        # Get chat history with default limit (50)
        history = await get_chat_history_async(user_id, conversation_id)
        
        assert len(history) == 50
        # Should get the most recent messages
        assert history[0]['user_message'] == "Message 59"
        assert history[-1]['user_message'] == "Message 10"
    
    @pytest.mark.asyncio
    async def test_conversation_updated_at_timestamp(self, test_db_path):
        """Test that conversation updated_at timestamp is updated"""
        user_id = "test_user_123"
        conversation_id = await create_conversation_async(user_id, "Test Conversation")
        
        # Get initial timestamp
        async with aiosqlite.connect(test_db_path) as conn:
            cursor = await conn.execute(
                'SELECT updated_at FROM conversations WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            initial_timestamp = (await cursor.fetchone())[0]
        
        # Update the conversation
        await update_conversation_title_async(user_id, conversation_id, "Updated Title")
        
        # Get updated timestamp
        async with aiosqlite.connect(test_db_path) as conn:
            cursor = await conn.execute(
                'SELECT updated_at FROM conversations WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            updated_timestamp = (await cursor.fetchone())[0]
        
        # Timestamp should be different
        assert initial_timestamp != updated_timestamp 