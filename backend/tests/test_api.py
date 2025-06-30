"""
Tests for FastAPI endpoints
"""

import pytest
import json
from unittest.mock import patch, AsyncMock

class TestChatEndpoints:
    """Test chat-related endpoints"""
    
    def test_chat_endpoint_success(self, client, mock_bedrock_client, auth_headers):
        """Test successful chat request"""
        # Create a conversation first
        create_resp = client.post("/conversations", json={"title": "Test Chat"}, headers=auth_headers)
        conversation_id = create_resp.json()["conversation_id"]
        
        with patch('main.bedrock_session', mock_bedrock_client):
            response = client.post("/chat", json={
                "message": "What is strength training?",
                "conversation_id": conversation_id
            }, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "citations" in data
            assert "conversation_id" in data
    
    def test_chat_endpoint_no_message(self, client, auth_headers):
        """Test chat endpoint with empty message"""
        # Create a conversation first
        create_resp = client.post("/conversations", json={"title": "Test Chat"}, headers=auth_headers)
        conversation_id = create_resp.json()["conversation_id"]
        
        response = client.post("/chat", json={
            "message": "",
            "conversation_id": conversation_id
        }, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_no_conversation_id(self, client, mock_bedrock_client, auth_headers):
        """Test chat endpoint without conversation ID - should create one automatically"""
        with patch('main.bedrock_session', mock_bedrock_client):
            response = client.post("/chat", json={
                "message": "Test message"
            }, headers=auth_headers)
            
            assert response.status_code == 200  # Should create conversation automatically
            data = response.json()
            assert "response" in data
            assert "citations" in data
            assert "conversation_id" in data

class TestConversationEndpoints:
    """Test conversation management endpoints"""
    
    def test_get_conversations(self, client, auth_headers):
        """Test getting all conversations"""
        response = client.get("/conversations", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_conversation(self, client, auth_headers):
        """Test creating a new conversation"""
        response = client.post("/conversations", json={
            "title": "Test Conversation"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "title" in data
    
    def test_create_conversation_no_title(self, client, auth_headers):
        """Test creating conversation without title"""
        response = client.post("/conversations", json={}, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
    
    def test_get_conversation_history(self, client, auth_headers):
        """Test getting conversation history"""
        # Create a conversation first
        create_resp = client.post("/conversations", json={"title": "Test Conversation"}, headers=auth_headers)
        conversation_id = create_resp.json()["conversation_id"]
        # Now get history
        response = client.get(f"/conversations/{conversation_id}/history", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_update_conversation_title(self, client, auth_headers):
        """Test updating conversation title"""
        # Create a conversation first
        create_resp = client.post("/conversations", json={"title": "To Update"}, headers=auth_headers)
        conversation_id = create_resp.json()["conversation_id"]
        # Now update
        response = client.put(f"/conversations/{conversation_id}", json={"title": "Updated Title"}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_delete_conversation(self, client, auth_headers):
        """Test deleting a conversation"""
        # Create a conversation first
        create_resp = client.post("/conversations", json={"title": "To Delete"}, headers=auth_headers)
        conversation_id = create_resp.json()["conversation_id"]
        # Now delete
        response = client.delete(f"/conversations/{conversation_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

class TestHistoryEndpoints:
    """Test chat history endpoints"""
    
    def test_get_history(self, client, auth_headers):
        """Test getting chat history"""
        response = client.get("/history", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_clear_history(self, client, auth_headers):
        """Test clearing chat history"""
        response = client.delete("/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json(self, client, auth_headers):
        """Test handling of invalid JSON"""
        response = client.post("/chat", data="invalid json", headers=auth_headers)
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client, auth_headers):
        """Test handling of missing required fields"""
        response = client.post("/chat", json={}, headers=auth_headers)
        assert response.status_code == 422
    
    def test_nonexistent_conversation(self, client, auth_headers):
        """Test accessing nonexistent conversation"""
        response = client.get("/conversations/999999/history", headers=auth_headers)
        assert response.status_code == 404  # Should return 404 for nonexistent conversation 