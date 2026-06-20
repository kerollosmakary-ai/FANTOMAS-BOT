import React, { useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const API = 'http://167.233.103.236:8000';
const WS = 'ws://167.233.103.236:8000/ws/chat';

function App() {
  const [adminKey, setAdminKey] = useState('change-me-admin-key');
  const [apiToken, setApiToken] = useState('');
  const [owner, setOwner] = useState('client_a');
  const [balance, setBalance] = useState(1000);
  const [provider, setProvider] = useState('auto');
  const [useRag, setUseRag] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('Disconnected');
  const [tokensLeft, setTokensLeft] = useState(null);
  const wsRef = useRef(null);

  async function createToken() {
    const res = await fetch(`${API}/admin/tokens`, {
      method: 'POST',
      headers: {'Content-Type':'application/json', 'x-admin-key': adminKey},
      body: JSON.stringify({owner_name: owner, balance: Number(balance)})
    });
    const data = await res.json();
    if (data.api_token) setApiToken(data.api_token);
    else alert(JSON.stringify(data));
  }

  function connect() {
    if (!apiToken) return alert('Paste or create an API token first');
    const socket = new WebSocket(`${WS}?token=${encodeURIComponent(apiToken)}`);
    wsRef.current = socket;
    socket.onopen = () => setStatus('Connected');
    socket.onclose = () => setStatus('Disconnected');
    socket.onerror = () => setStatus('Error');
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'ready') setTokensLeft(data.tokens_remaining);
      if (data.type === 'chunk') {
        setMessages(prev => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          if (last && last.role === 'assistant' && last.streaming) last.content += data.content;
          else copy.push({role:'assistant', content:data.content, streaming:true});
          return copy;
        });
      }
      if (data.type === 'done') {
        setTokensLeft(data.tokens_remaining);
        setMessages(prev => prev.map((m, i) => i === prev.length - 1 ? {...m, streaming:false, provider:data.provider} : m));
      }
      if (data.type === 'error') setMessages(prev => [...prev, {role:'system', content:data.message}]);
    };
  }

  function send() {
    if (!wsRef.current || wsRef.current.readyState !== 1) return alert('Connect first');
    if (!input.trim()) return;
    setMessages(prev => [...prev, {role:'user', content:input}]);
    wsRef.current.send(JSON.stringify({content: input, provider, addons: useRag ? ['rag'] : []}));
    setInput('');
  }

  return <div className="app">
    <h1>Advanced AI Bot</h1>
    <p className="muted">Real-time chat, customer tokens, provider fallback, and safe addons.</p>

    <section className="card">
      <h2>Admin: Create Customer Token</h2>
      <input value={adminKey} onChange={e=>setAdminKey(e.target.value)} placeholder="Admin key" />
      <input value={owner} onChange={e=>setOwner(e.target.value)} placeholder="Owner name" />
      <input type="number" value={balance} onChange={e=>setBalance(e.target.value)} placeholder="Balance" />
      <button onClick={createToken}>Create Token</button>
    </section>

    <section className="card">
      <h2>Chat</h2>
      <textarea value={apiToken} onChange={e=>setApiToken(e.target.value)} placeholder="Customer API token sk_live_..." />
      <div className="row">
        <select value={provider} onChange={e=>setProvider(e.target.value)}>
          <option value="auto">Auto fallback</option>
          <option value="groq">Groq</option>
          <option value="openrouter">OpenRouter</option>
          <option value="deepseek">DeepSeek</option>
          <option value="openai">OpenAI</option>
        </select>
        <label><input type="checkbox" checked={useRag} onChange={e=>setUseRag(e.target.checked)} /> RAG addon</label>
        <button onClick={connect}>Connect</button>
      </div>
      <p>Status: <b>{status}</b> {tokensLeft !== null && <> | Tokens: <b>{tokensLeft}</b></>}</p>
      <div className="chatbox">
        {messages.map((m,i)=><div key={i} className={`msg ${m.role}`}><b>{m.role}</b>: {m.content}</div>)}
      </div>
      <div className="row">
        <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter') send()}} placeholder="Type a message..." />
        <button onClick={send}>Send</button>
      </div>
    </section>
  </div>
}

createRoot(document.getElementById('root')).render(<App />);
