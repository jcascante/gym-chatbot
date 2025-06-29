"""
Pytest configuration and fixtures for gym chatbot tests
"""

import pytest
import asyncio
import aiosqlite
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add the parent directory to the path so we can import from main
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from config import DB_PATH

@pytest.fixture
def test_db_path():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db = tmp.name
    
    yield test_db
    
    # Cleanup
    if os.path.exists(test_db):
        os.unlink(test_db)

@pytest.fixture
async def test_db(test_db_path):
    """Create and initialize a test database"""
    async with aiosqlite.connect(test_db_path) as conn:
        # Create conversations table
        await conn.execute('''CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')
        
        # Create chat_history table
        await conn.execute('''CREATE TABLE chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            citations TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )''')
        
        await conn.commit()
    
    return test_db_path

@pytest.fixture
def mock_bedrock_client():
    """Mock AWS Bedrock client for testing"""
    mock_client = AsyncMock()
    mock_client.invoke_model.return_value = {
        'body': MagicMock(
            read=lambda: b'{"completion": "This is a test response"}'
        )
    }
    return mock_client

@pytest.fixture
def mock_knowledge_base():
    """Mock knowledge base responses"""
    return [
        "Test document 1 content",
        "Test document 2 content"
    ]

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing"""
    return {
        "title": "Test Conversation",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }

@pytest.fixture
def sample_chat_message():
    """Sample chat message data for testing"""
    return {
        "user_message": "What is strength training?",
        "bot_response": "Strength training is a form of exercise...",
        "citations": ["document1.pdf", "document2.pdf"],
        "timestamp": "2024-01-01T00:00:00"
    }

# Configure pytest for async tests
pytest_plugins = ['pytest_asyncio'] 