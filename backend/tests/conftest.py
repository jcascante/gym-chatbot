"""
Pytest configuration and fixtures for gym chatbot tests
"""

import tempfile
import os
import sys

# Patch config.DB_PATH before any backend imports
import importlib
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import config
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
    test_db = tmp.name
original_db_path = config.DB_PATH
config.DB_PATH = test_db

def pytest_sessionfinish(session, exitstatus):
    config.DB_PATH = original_db_path
    if os.path.exists(test_db):
        os.unlink(test_db)

# Now import the rest
import pytest
import asyncio
import aiosqlite
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Add the parent directory to the path so we can import from main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app, init_db_async
from config import DB_PATH as PROD_DB_PATH
from auth import create_access_token, hash_password

@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database for the whole test session and patch config.DB_PATH globally."""
    try:
        # Initialize schema and test user
        async def setup():
            async with aiosqlite.connect(test_db) as conn:
                await conn.execute('''CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    is_guest BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )''')
                await conn.execute('''CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')
                await conn.execute('''CREATE TABLE chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    citations TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )''')
                # Create test user
                test_user_id = "test_user_123"
                password_hash = hash_password("testpassword")
                now = datetime.now().isoformat()
                await conn.execute('''INSERT INTO users (id, username, email, password_hash, is_guest, created_at, updated_at) 
                                     VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                                 (test_user_id, "testuser", "testuser@example.com", password_hash, False, now, now))
                await conn.commit()
        asyncio.get_event_loop().run_until_complete(setup())
        yield test_db
    finally:
        if os.path.exists(test_db):
            os.unlink(test_db)

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
def client(test_db_path):
    """Create a test client for the FastAPI app, using the test DB."""
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def auth_headers(test_db_path):
    """Create authentication headers for testing, using the test user in the test DB."""
    test_user_id = "test_user_123"
    token = create_access_token(data={"sub": test_user_id})
    return {"Authorization": f"Bearer {token}"}

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

# Helper to clear all tables before each DB test
@pytest.fixture(autouse=True)
def clear_tables(test_db_path):
    import aiosqlite
    async def clear():
        async with aiosqlite.connect(test_db_path) as conn:
            await conn.execute('DELETE FROM chat_history')
            await conn.execute('DELETE FROM conversations')
            await conn.execute('DELETE FROM users WHERE id != "test_user_123"')
            await conn.commit()
    import asyncio
    asyncio.get_event_loop().run_until_complete(clear())
    yield

# Configure pytest for async tests
pytest_plugins = ['pytest_asyncio'] 