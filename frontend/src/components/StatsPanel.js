import React, { useState, useEffect } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

function StatsPanel({ agentId }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!agentId) return;
    setLoading(true);
    fetch(`${API_BASE}/agents/${agentId}/stats`)
      .then(r => r.json())
      .then(data => { setStats(data); setLoading(false); })
      .catch(() => { setError('Failed to load stats'); setLoading(false); });
  }, [agentId]);

  if (loading) return <div className="loading">Loading stats...</div>;
  if (error) return <div className="error-msg">{error}</div>;
  if (!stats) return null;

  return (
    <div className="stats-card">
      <div className="stat-row">
        <span className="stat-label">Agent Name</span>
        <span className="stat-value">{stats.name}</span>
      </div>
      <div className="stat-row">
        <span className="stat-label">Games Played</span>
        <span className="stat-value">{stats.games_played}</span>
      </div>
      <div className="stat-row">
        <span className="stat-label">Games Won</span>
        <span className="stat-value">{stats.games_won}</span>
      </div>
      <div className="stat-row">
        <span className="stat-label">Win Rate</span>
        <span className="stat-value">{(stats.win_rate * 100).toFixed(1)}%</span>
      </div>
      <div className="stat-row">
        <span className="stat-label">Total Chips</span>
        <span className="stat-value">💰 {stats.total_chips}</span>
      </div>
      <div className="stat-row">
        <span className="stat-label">Member Since</span>
        <span className="stat-value">{new Date(stats.created_at).toLocaleDateString()}</span>
      </div>
    </div>
  );
}

export default StatsPanel;
