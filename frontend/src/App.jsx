import { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Fetch chat history on mount
  useEffect(() => {
    fetch('http://localhost:8000/history')
      .then(res => res.json())
      .then(data => setMessages(data.reverse()))
      .catch(() => setMessages([]));
  }, []);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const detectLanguage = (text) => {
    // Simple Spanish detection based on common words
    const spanishWords = ['qué', 'cómo', 'dónde', 'cuándo', 'por qué', 'quién', 'cuál', 'cuáles', 'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas', 'con', 'para', 'por', 'sin', 'sobre', 'entre', 'hacia', 'desde', 'hasta', 'durante', 'según', 'mediante', 'contra', 'bajo', 'tras', 'ante', 'bajo', 'cabe', 'so', 'través', 'versus', 'vía'];
    const spanishChars = ['ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü', '¿', '¡'];
    
    const textLower = text.toLowerCase();
    const spanishWordCount = spanishWords.filter(word => textLower.includes(word)).length;
    const spanishCharCount = spanishChars.filter(char => text.includes(char)).length;
    
    return (spanishWordCount > 0 || spanishCharCount > 0) ? 'es' : 'en';
  };

  const getCitationLabel = (language) => {
    return language === 'es' ? 'Fuentes:' : 'Sources:';
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    const userMsg = { user_message: input, bot_response: '', citations: [], timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });
      const data = await res.json();
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...userMsg,
          bot_response: data.response,
          citations: data.citations || []
        };
        return updated;
      });
    } catch {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...userMsg,
          bot_response: 'Error: Could not reach backend.',
          citations: []
        };
        return updated;
      });
    }
    setInput('');
    setLoading(false);
  };

  const clearHistory = async () => {
    if (!window.confirm('Are you sure you want to clear all chat history?')) {
      return;
    }
    
    try {
      const res = await fetch('http://localhost:8000/history', {
        method: 'DELETE'
      });
      
      if (res.ok) {
        setMessages([]);
        alert('Chat history cleared successfully!');
      } else {
        alert('Failed to clear chat history.');
      }
    } catch (error) {
      alert('Error clearing chat history: ' + error.message);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Gym AI Chatbot</h2>
        <button 
          onClick={clearHistory} 
          className="clear-history-btn"
          title="Clear all chat history"
        >
          Clear History
        </button>
      </div>
      <div className="chat-history">
        {messages.map((msg, idx) => (
          <div key={idx} className="chat-message">
            <div className="user-msg"><b>You:</b> {msg.user_message}</div>
            {msg.bot_response && (
              <>
                <div className="bot-msg"><b>Bot:</b> {msg.bot_response}</div>
                {msg.citations && msg.citations.length > 0 && (
                  <div className="citations">
                    <small><b>{getCitationLabel(detectLanguage(msg.bot_response))}</b> {msg.citations.join(', ')}</small>
                  </div>
                )}
              </>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <form className="chat-input" onSubmit={sendMessage}>
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
      </form>
    </div>
  );
}

export default App;
