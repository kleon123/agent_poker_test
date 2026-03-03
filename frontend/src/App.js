import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import './App.css';
import PokerTable from './components/PokerTable';
import StatsPanel from './components/StatsPanel';
import GameLog from './components/GameLog';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// ── Lobby Page ─────────────────────────────────────────────────────────────────

function Lobby() {
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState(localStorage.getItem('poker_api_key') || '');
  const [agentName, setAgentName] = useState('');
  const [registered, setRegistered] = useState(!!localStorage.getItem('poker_api_key'));
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchTables = React.useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/tables`);
      const data = await resp.json();
      setTables(data);
    } catch (e) {
      setError('Failed to fetch tables');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => { fetchTables(); }, [fetchTables]);

  const register = async () => {
    if (!agentName.trim()) { setError('Enter a name'); return; }
    try {
      const resp = await fetch(`${API_BASE}/agents/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: agentName }),
      });
      const data = await resp.json();
      if (resp.ok) {
        localStorage.setItem('poker_api_key', data.api_key);
        localStorage.setItem('poker_agent_id', data.id);
        localStorage.setItem('poker_agent_name', data.name);
        setApiKey(data.api_key);
        setRegistered(true);
        setError('');
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (e) {
      setError('Failed to register');
    }
  };

  const createTable = async () => {
    const name = prompt('Table name:', 'My Table');
    if (!name) return;
    try {
      const resp = await fetch(`${API_BASE}/tables`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
        body: JSON.stringify({ name, max_players: 6, small_blind: 10, big_blind: 20 }),
      });
      const data = await resp.json();
      if (resp.ok) {
        navigate(`/table/${data.id}`);
      } else {
        setError(data.detail || 'Failed to create table');
      }
    } catch (e) {
      setError('Failed to create table');
    }
  };

  const joinTable = async (tableId) => {
    try {
      const resp = await fetch(`${API_BASE}/tables/${tableId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
        body: JSON.stringify({}),
      });
      if (resp.ok) {
        navigate(`/table/${tableId}`);
      } else {
        const data = await resp.json();
        setError(data.detail || 'Failed to join table');
      }
    } catch (e) {
      setError('Failed to join table');
    }
  };

  return (
    <div className="lobby">
      <h1>♠ Poker Lobby ♥</h1>
      {error && <div className="error-msg">{error}</div>}
      {!registered ? (
        <div className="register-box">
          <h2>Register Agent</h2>
          <input
            type="text"
            placeholder="Your agent name"
            value={agentName}
            onChange={e => setAgentName(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && register()}
          />
          <button onClick={register}>Register</button>
        </div>
      ) : (
        <div className="lobby-content">
          <div className="lobby-header">
            <span>Welcome, {localStorage.getItem('poker_agent_name') || 'Agent'}!</span>
            <button onClick={createTable} className="btn-primary">+ Create Table</button>
            <button onClick={fetchTables} className="btn-secondary">Refresh</button>
          </div>
          {loading ? (
            <div className="loading">Loading tables...</div>
          ) : (
            <div className="tables-list">
              {tables.length === 0 ? (
                <p className="no-tables">No tables available. Create one!</p>
              ) : (
                tables.map(table => (
                  <div key={table.id} className="table-card">
                    <div className="table-info">
                      <h3>{table.name}</h3>
                      <span>{table.player_count}/{table.max_players} players</span>
                      <span>Blinds: {table.small_blind}/{table.big_blind}</span>
                      <span className={`status-badge status-${table.status}`}>{table.status}</span>
                    </div>
                    <button onClick={() => joinTable(table.id)} className="btn-join">Join</button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Table Page ─────────────────────────────────────────────────────────────────

function TablePage() {
  return <PokerTable />;
}

// ── Stats Page ─────────────────────────────────────────────────────────────────

function StatsPage() {
  const agentId = localStorage.getItem('poker_agent_id');
  return (
    <div className="stats-page">
      <h1>Statistics</h1>
      {agentId ? <StatsPanel agentId={agentId} /> : <p>Please register first.</p>}
    </div>
  );
}

// ── App ────────────────────────────────────────────────────────────────────────

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <Link to="/" className="nav-logo">♠ Poker Platform</Link>
          <div className="nav-links">
            <Link to="/">Lobby</Link>
            <Link to="/stats">Stats</Link>
          </div>
        </nav>
        <main>
          <Routes>
            <Route path="/" element={<Lobby />} />
            <Route path="/table/:tableId" element={<TablePage />} />
            <Route path="/stats" element={<StatsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
