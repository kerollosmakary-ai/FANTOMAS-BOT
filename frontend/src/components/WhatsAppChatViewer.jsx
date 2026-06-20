import React, { useEffect, useState } from 'react';

const API_URL = '/api/whatsapp';

export default function WhatsAppChatViewer() {
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState('');
  const [messages, setMessages] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/chats`)
      .then(r => r.json())
      .then(setChats);
  }, []);

  useEffect(() => {
    if (!selectedChat) return;
    setLoading(true);
    const url = search
      ? `${API_URL}/${encodeURIComponent(selectedChat)}?search=${encodeURIComponent(search)}`
      : `${API_URL}/${encodeURIComponent(selectedChat)}`;
    fetch(url)
      .then(r => r.json())
      .then(data => {
        setMessages(data);
        setLoading(false);
      });
  }, [selectedChat, search]);

  const handleDeleteChat = () => {
    if (!window.confirm(`Delete all messages from "${selectedChat}"?`)) return;
    fetch(`${API_URL}/${encodeURIComponent(selectedChat)}/delete`, { method: 'DELETE' })
      .then(() => {
        setMessages([]);
        setChats(prev => prev.filter(c => c !== selectedChat));
        setSelectedChat('');
      });
  };

  return (
    <div style={{ padding: 16, maxWidth: 800, margin: '0 auto', fontFamily: 'sans-serif' }}>
      <h2>WhatsApp Chat Viewer</h2>

      <div style={{ marginBottom: 12 }}>
        <label>Select Chat: </label>
        <select value={selectedChat} onChange={e => setSelectedChat(e.target.value)} style={{ padding: 6, minWidth: 200 }}>
          <option value="">-- choose --</option>
          {chats.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {selectedChat && (
        <>
          <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
            <input
              placeholder="Search sender or message..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ flex: 1, padding: 6 }}
            />
            <button onClick={handleDeleteChat} style={{ background: '#e53935', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: 4 }}>
              Delete Chat
            </button>
          </div>

          {loading && <p>Loading...</p>}

          <div style={{ border: '1px solid #ddd', borderRadius: 8, maxHeight: 500, overflowY: 'auto' }}>
            {messages.length === 0 && !loading && <p style={{ padding: 12, color: '#888' }}>No messages found.</p>}
            {messages.map((m, i) => (
              <div key={i} style={{ padding: '10px 12px', borderBottom: '1px solid #eee' }}>
                <div style={{ fontSize: 12, color: '#555', marginBottom: 4 }}>
                  <strong>{m.sender}</strong> · {m.timestamp}
                </div>
                <div style={{ fontSize: 14, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{m.message}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
