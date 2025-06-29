"""
Tests for FastAPI endpoints
"""

import pytest
import json
from unittest.mock import patch, AsyncMock

class TestChatEndpoints:
    """Test chat-related endpoints"""
    
    def test_chat_endpoint_success(self, client, mock_bedrock_client):
        """Test successful chat request"""
        with patch('main.bedrock_session', mock_bedrock_client):
            response = client.post("/chat", json={
                "message": "What is strength training?",
                "conversation_id": 1
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "citations" in data
            assert "conversation_id" in data
    
    def test_chat_endpoint_no_message(self, client):
        """Test chat endpoint with empty message"""
        response = client.post("/chat", json={
            "message": "",
            "conversation_id": 1
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_no_conversation_id(self, client):
        """Test chat endpoint without conversation ID"""
        response = client.post("/chat", json={
            "message": "Test message"
        })
        
        assert response.status_code == 422  # Validation error

class TestConversationEndpoints:
    """Test conversation management endpoints"""
    
    def test_get_conversations(self, client):
        """Test getting all conversations"""
        response = client.get("/conversations")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_conversation(self, client):
        """Test creating a new conversation"""
        response = client.post("/conversations", json={
            "title": "Test Conversation"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "title" in data
    
    def test_create_conversation_no_title(self, client):
        """Test creating conversation without title"""
        response = client.post("/conversations", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
    
    def test_get_conversation_history(self, client):
        """Test getting conversation history"""
        response = client.get("/conversations/1/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_update_conversation_title(self, client):
        """Test updating conversation title"""
        response = client.put("/conversations/1", json={
            "title": "Updated Title"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_delete_conversation(self, client):
        """Test deleting a conversation"""
        response = client.delete("/conversations/1")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

class TestHistoryEndpoints:
    """Test chat history endpoints"""
    
    def test_get_history(self, client):
        """Test getting chat history"""
        response = client.get("/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_clear_history(self, client):
        """Test clearing chat history"""
        response = client.delete("/history")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post("/chat", data="invalid json")
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        response = client.post("/chat", json={})
        assert response.status_code == 422
    
    def test_nonexistent_conversation(self, client):
        """Test accessing nonexistent conversation"""
        response = client.get("/conversations/999999/history")
        assert response.status_code == 200  # Should return empty list
        assert response.json() == [] 