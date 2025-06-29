import React, { useState } from 'react';

export default function Sidebar({
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onCreateConversation,
  onRenameConversation,
  onDeleteConversation
}) {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const handleRename = (id, title) => {
    setEditingId(id);
    setEditTitle(title);
  };

  const handleRenameSubmit = (id) => {
    if (editTitle.trim()) {
      onRenameConversation(id, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle('');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Conversations</h2>
        <button className="new-convo-btn" onClick={onCreateConversation} title="New Conversation">＋</button>
      </div>
      <ul className="conversation-list">
        {conversations.map((conv) => (
          <li
            key={conv.id}
            className={conv.id === activeConversationId ? 'active' : ''}
            onClick={() => onSelectConversation(conv.id)}
          >
            {editingId === conv.id ? (
              <form
                onSubmit={e => {
                  e.preventDefault();
                  handleRenameSubmit(conv.id);
                }}
                className="rename-form"
              >
                <input
                  type="text"
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  autoFocus
                  onBlur={() => setEditingId(null)}
                  onKeyDown={e => {
                    if (e.key === 'Escape') setEditingId(null);
                  }}
                />
              </form>
            ) : (
              <span className="conversation-title">
                {conv.title}
                <span className="message-count">({conv.message_count})</span>
              </span>
            )}
            <div className="conversation-actions">
              <button
                className="rename-btn"
                title="Rename"
                onClick={e => {
                  e.stopPropagation();
                  handleRename(conv.id, conv.title);
                }}
              >✏️</button>
              <button
                className="delete-btn"
                title="Delete"
                onClick={e => {
                  e.stopPropagation();
                  if (window.confirm('Delete this conversation?')) {
                    onDeleteConversation(conv.id);
                  }
                }}
              >🗑️</button>
            </div>
          </li>
        ))}
      </ul>
    </aside>
  );
} 