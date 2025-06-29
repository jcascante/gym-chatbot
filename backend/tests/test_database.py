"""
Tests for database operations
"""

import pytest
import aiosqlite
import datetime
from main import (
    init_db_async, 
    get_chat_history_async, 
    save_chat_async, 
    create_conversation_async,
    get_conversations_async,
    update_conversation_title_async,
    delete_conversation_async
)

class TestDatabaseOperations:
    """Test database operations"""
    
    @pytest.mark.asyncio
    async def test_init_database(self, test_db):
        """Test database initialization"""
        # Test that tables are created
        async with aiosqlite.connect(test_db) as conn:
            cursor = await conn.execute("PRAGMA table_info(conversations)")
            conversations_columns = [column[1] async for column in cursor]
            
            assert 'id' in conversations_columns
            assert 'title' in conversations_columns
            assert 'created_at' in conversations_columns
            assert 'updated_at' in conversations_columns
            
            cursor = await conn.execute("PRAGMA table_info(chat_history)")
            chat_columns = [column[1] async for column in cursor]
            
            assert 'id' in chat_columns
            assert 'conversation_id' in chat_columns
            assert 'user_message' in chat_columns
            assert 'bot_response' in chat_columns
            assert 'citations' in chat_columns
            assert 'timestamp' in chat_columns
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, test_db):
        """Test creating a conversation"""
        conversation_id = await create_conversation_async("Test Conversation")
        assert conversation_id > 0
        
        # Verify conversation was created
        async with aiosqlite.connect(test_db) as conn:
            cursor = await conn.execute(
                "SELECT title FROM conversations WHERE id = ?", 
                (conversation_id,)
            )
            result = await cursor.fetchone()
            assert result[0] == "Test Conversation"
    
    @pytest.mark.asyncio
    async def test_create_conversation_no_title(self, test_db):
        """Test creating conversation without title"""
        conversation_id = await create_conversation_async()
        assert conversation_id > 0
        
        # Verify conversation was created with default title
        async with aiosqlite.connect(test_db) as conn:
            cursor = await conn.execute(
                "SELECT title FROM conversations WHERE id = ?", 
                (conversation_id,)
            )
            result = await cursor.fetchone()
            assert "Conversation" in result[0]
    
    @pytest.mark.asyncio
    async def test_save_chat_message(self, test_db):
        """Test saving a chat message"""
        # Create a conversation first
        conversation_id = await create_conversation_async("Test Conversation")
        
        # Save a chat message
        user_message = "What is strength training?"
        bot_response = "Strength training is a form of exercise..."
        citations = ["doc1.pdf", "doc2.pdf"]
        
        await save_chat_async(conversation_id, user_message, bot_response, citations)
        
        # Verify message was saved
        async with aiosqlite.connect(test_db) as conn:
            cursor = await conn.execute(
                "SELECT user_message, bot_response, citations FROM chat_history WHERE conversation_id = ?",
                (conversation_id,)
            )
            result = await cursor.fetchone()
            assert result[0] == user_message
            assert result[1] == bot_response
            assert "doc1.pdf" in result[2]  # citations is JSON string
    
    @pytest.mark.asyncio
    async def test_get_chat_history(self, test_db):
        """Test getting chat history"""
        # Create conversation and add messages
        conversation_id = await create_conversation_async("Test Conversation")
        
        messages = [
            ("Hello", "Hi there!", ["doc1.pdf"]),
            ("How are you?", "I'm doing well!", ["doc2.pdf"]),
            ("What's the weather?", "It's sunny!", ["doc3.pdf"])
        ]
        
        for user_msg, bot_msg, citations in messages:
            await save_chat_async(conversation_id, user_msg, bot_msg, citations)
        
        # Get chat history
        history = await get_chat_history_async(conversation_id)
        
        assert len(history) == 3
        assert history[0]['user_message'] == "Hello"
        assert history[1]['user_message'] == "How are you?"
        assert history[2]['user_message'] == "What's the weather?"
    
    @pytest.mark.asyncio
    async def test_get_conversations(self, test_db):
        """Test getting all conversations"""
        # Create multiple conversations
        conv1_id = await create_conversation_async("Conversation 1")
        conv2_id = await create_conversation_async("Conversation 2")
        conv3_id = await create_conversation_async("Conversation 3")
        
        conversations = await get_conversations_async()
        
        assert len(conversations) >= 3
        titles = [conv['title'] for conv in conversations]
        assert "Conversation 1" in titles
        assert "Conversation 2" in titles
        assert "Conversation 3" in titles
    
    @pytest.mark.asyncio
    async def test_update_conversation_title(self, test_db):
        """Test updating conversation title"""
        conversation_id = await create_conversation_async("Original Title")
        
        # Update title
        await update_conversation_title_async(conversation_id, "Updated Title")
        
        # Verify title was updated
        async with aiosqlite.connect(test_db) as conn:
            cursor = await conn.execute(
                "SELECT title FROM conversations WHERE id = ?", 
                (conversation_id,)
            )
            result = await cursor.fetchone()
            assert result[0] == "Updated Title"
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, test_db):
        """Test deleting a conversation"""
        conversation_id = await create_conversation_async("To Delete")
        
        # Add some messages
        await save_chat_async(conversation_id, "Test", "Response", [])
        
        # Delete conversation
        await delete_conversation_async(conversation_id)
        
        # Verify conversation was deleted
        async with aiosqlite.connect(test_db) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM conversations WHERE id = ?", 
                (conversation_id,)
            )
            result = await cursor.fetchone()
            assert result[0] == 0
            
            # Verify associated messages were also deleted
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM chat_history WHERE conversation_id = ?", 
                (conversation_id,)
            )
            result = await cursor.fetchone()
            assert result[0] == 0
    
    @pytest.mark.asyncio
    async def test_chat_history_limit(self, test_db):
        """Test chat history limit"""
        conversation_id = await create_conversation_async("Test Conversation")
        
        # Add more than 50 messages
        for i in range(60):
            await save_chat_async(conversation_id, f"Message {i}", f"Response {i}", [])
        
        # Get history with default limit (50)
        history = await get_chat_history_async(conversation_id)
        assert len(history) == 50
        
        # Get history with custom limit
        history = await get_chat_history_async(conversation_id, limit=10)
        assert len(history) == 10
    
    @pytest.mark.asyncio
    async def test_conversation_updated_at_timestamp(self, test_db):
        """Test that conversation updated_at is updated when messages are added"""
        conversation_id = await create_conversation_async("Test Conversation")
        
        # Get initial updated_at
        async with aiosqlite.connect(test_db) as conn:
            cursor = await conn.execute(
                "SELECT updated_at FROM conversations WHERE id = ?", 
                (conversation_id,)
            )
            initial_updated_at = (await cursor.fetchone())[0]
        
        # Add a message
        await save_chat_async(conversation_id, "Test message", "Test response", [])
        
        # Get updated_at after adding message
        async with aiosqlite.connect(test_db) as conn:
            cursor = await conn.execute(
                "SELECT updated_at FROM conversations WHERE id = ?", 
                (conversation_id,)
            )
            new_updated_at = (await cursor.fetchone())[0]
        
        # Verify timestamp was updated
        assert new_updated_at > initial_updated_at 