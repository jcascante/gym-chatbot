import React, { useEffect, useState, useRef } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import MarkdownRenderer from './components/MarkdownRenderer';
import LoginForm from './components/LoginForm';
import UserProfile from './components/UserProfile';
import { apiGet, apiPost, apiPut, apiDelete } from './utils/api';
import './App.css';

function ChatApp() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const chatHistoryRef = useRef(null);
  
  const { user, token, loading: authLoading } = useAuth();

  // Fetch conversations when user is authenticated
  useEffect(() => {
    if (user && token) {
      fetchConversations();
    }
  }, [user, token]);

  // Fetch chat history when active conversation changes
  useEffect(() => {
    if (activeConversationId && token) {
      fetchChatHistory(activeConversationId);
    } else {
      setChatHistory([]);
    }
  }, [activeConversationId, token]);

  // Auto-scroll to show new messages when chat history changes
  useEffect(() => {
    if (chatHistoryRef.current && chatHistory.length > 0) {
      // Get the last message element
      const lastMessage = chatHistoryRef.current.lastElementChild;
      if (lastMessage) {
        // Check if the last message is already visible
        const rect = lastMessage.getBoundingClientRect();
        const chatHistoryRect = chatHistoryRef.current.getBoundingClientRect();
        
        // Only scroll if the last message is not fully visible
        if (rect.bottom > chatHistoryRect.bottom || rect.top < chatHistoryRect.top) {
          // Scroll to show the beginning of the last message with a small offset
          lastMessage.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start',
            inline: 'nearest'
          });
        }
      }
    }
  }, [chatHistory]);

  // Debug: Log active conversation state
  useEffect(() => {
    console.log('Active conversation ID:', activeConversationId);
    console.log('Conversations count:', conversations.length);
    console.log('Chat history length:', chatHistory.length);
    
    // Debug header visibility
    const header = document.querySelector('.chat-header');
    if (header) {
      console.log('Header found:', header);
      console.log('Header visible:', header.offsetParent !== null);
      console.log('Header rect:', header.getBoundingClientRect());
    } else {
      console.log('Header not found!');
    }
  }, [activeConversationId, conversations, chatHistory]);

  const fetchConversations = async () => {
    try {
      const data = await apiGet('/conversations', token);
      setConversations(data);
      if (!activeConversationId && data.length > 0) {
        setActiveConversationId(data[0].id);
      } else if (data.length === 0) {
        // Auto-create a conversation if none exists
        handleCreateConversation();
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
      setConversations([]);
    }
  };

  const fetchChatHistory = async (conversationId) => {
    try {
      const data = await apiGet(`/conversations/${conversationId}/history`, token);
      setChatHistory(data);
    } catch (error) {
      console.error('Error fetching chat history:', error);
      setChatHistory([]);
    }
  };

  const handleSelectConversation = (id) => {
    setActiveConversationId(id);
    // Close sidebar on mobile after selecting conversation
    setSidebarOpen(false);
  };

  const handleCreateConversation = async () => {
    try {
      const data = await apiPost('/conversations', { title: null }, token);
      fetchConversations();
      setActiveConversationId(data.conversation_id);
      // Close sidebar on mobile after creating conversation
      setSidebarOpen(false);
    } catch (error) {
      console.error('Error creating conversation:', error);
    }
  };

  const handleRenameConversation = async (id, title) => {
    try {
      await apiPut(`/conversations/${id}`, { title }, token);
      fetchConversations();
    } catch (error) {
      console.error('Error renaming conversation:', error);
    }
  };

  const handleDeleteConversation = async (id) => {
    try {
      await apiDelete(`/conversations/${id}`, token);
      fetchConversations();
      if (id === activeConversationId) {
        setActiveConversationId(null);
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !activeConversationId) return;
    
    setLoading(true);
    
    try {
      await apiPost('/chat', { 
        message: input, 
        conversation_id: activeConversationId 
      }, token);
      
      setInput('');
      setLoading(false);
      
      // Refresh chat history immediately
      await fetchChatHistory(activeConversationId);
      
      // Optionally update conversations (for updated_at)
      fetchConversations();
    } catch (error) {
      console.error('Error sending message:', error);
      setLoading(false);
    }
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  const handleBackdropClick = (e) => {
    // Only close if clicking directly on the backdrop, not on its children
    if (e.target === e.currentTarget) {
      setSidebarOpen(false);
    }
  };

  // Show loading screen while checking authentication
  if (authLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Show authentication form if not authenticated
  if (!user) {
    return (
      <div className="auth-wrapper">
        <LoginForm />
      </div>
    );
  }

  // Show chat interface if authenticated
  return (
    <div className="app-container">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onCreateConversation={handleCreateConversation}
        onRenameConversation={handleRenameConversation}
        onDeleteConversation={handleDeleteConversation}
        isOpen={sidebarOpen}
        onClose={closeSidebar}
      />
      {sidebarOpen && (
        <div 
          className="sidebar-backdrop" 
          onClick={handleBackdropClick}
        />
      )}
      <main className="chat-main">
        <div className="chat-header">
          <button className="mobile-menu-btn" onClick={toggleSidebar}>
            ☰
          </button>
          <h2>MTC Assistant</h2>
          <UserProfile />
        </div>
        <div className="chat-history" ref={chatHistoryRef}>
          {chatHistory.map((msg, idx) => (
            <div key={idx} className="chat-message">
              <div className="user-message"><b>You:</b> {msg.user_message}</div>
              <div className="bot-response">
                <b>Bot:</b> 
                <MarkdownRenderer content={msg.bot_response} />
              </div>
              {msg.citations && msg.citations.length > 0 && (
                <div className="citations">
                  <b>Citations:</b> {msg.citations.join(', ')}
                </div>
              )}
              <div className="timestamp">{msg.timestamp}</div>
            </div>
          ))}
        </div>
        <form className="chat-input-form" onSubmit={handleSend}>
          {!activeConversationId ? (
            <div className="no-conversation-message">
              Click "New Conversation" to start chatting
            </div>
          ) : (
            <>
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Type your message..."
                disabled={loading}
              />
              <button type="submit" disabled={loading || !input.trim()}>
                {loading ? 'Sending...' : 'Send'}
              </button>
            </>
          )}
        </form>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <ChatApp />
    </AuthProvider>
  );
}

export default App;
