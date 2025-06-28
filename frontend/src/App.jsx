import React, { useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Fetch conversations on mount
  useEffect(() => {
    fetchConversations();
  }, []);

  // Fetch chat history when active conversation changes
  useEffect(() => {
    if (activeConversationId) {
      fetch(`http://localhost:8000/conversations/${activeConversationId}/history`)
        .then(res => res.json())
        .then(setChatHistory);
    } else {
      setChatHistory([]);
    }
  }, [activeConversationId]);

  const fetchConversations = () => {
    fetch('http://localhost:8000/conversations')
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('Fetched conversations:', data);
        setConversations(data);
        if (!activeConversationId && data.length > 0) {
          setActiveConversationId(data[0].id);
        }
      })
      .catch(error => {
        console.error('Error fetching conversations:', error);
        setConversations([]);
      });
  };

  const handleSelectConversation = (id) => {
    console.log('Selecting conversation:', id);
    setActiveConversationId(id);
  };

  const handleCreateConversation = () => {
    console.log('Creating new conversation...');
    fetch('http://localhost:8000/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: null })
    })
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('Created conversation:', data);
        fetchConversations();
        setActiveConversationId(data.conversation_id);
      })
      .catch(error => {
        console.error('Error creating conversation:', error);
      });
  };

  const handleRenameConversation = (id, title) => {
    fetch(`http://localhost:8000/conversations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    }).then(() => fetchConversations());
  };

  const handleDeleteConversation = (id) => {
    fetch(`http://localhost:8000/conversations/${id}`, { method: 'DELETE' })
      .then(() => {
        fetchConversations();
        if (id === activeConversationId) {
          setActiveConversationId(null);
        }
      });
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !activeConversationId) return;
    setLoading(true);
    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input, conversation_id: activeConversationId })
    });
    const data = await res.json();
    setInput('');
    setLoading(false);
    // Refresh chat history
    fetch(`http://localhost:8000/conversations/${activeConversationId}/history`)
      .then(res => res.json())
      .then(setChatHistory);
    // Optionally update conversations (for updated_at)
    fetchConversations();
  };

  return (
    <div className="app-container">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onCreateConversation={handleCreateConversation}
        onRenameConversation={handleRenameConversation}
        onDeleteConversation={handleDeleteConversation}
      />
      <main className="chat-main">
        <div className="chat-history">
          {chatHistory.map((msg, idx) => (
            <div key={idx} className="chat-message">
              <div className="user-message"><b>You:</b> {msg.user_message}</div>
              <div className="bot-response"><b>Bot:</b> {msg.bot_response}</div>
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

export default App;
