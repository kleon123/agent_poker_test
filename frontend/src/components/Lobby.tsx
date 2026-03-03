import React, { useState, useEffect, useCallback } from 'react';
import { TableInfo, PlatformStats, AgentInfo } from '../types/game';
import { api } from '../api/client';

interface LobbyProps {
  onWatchTable: (tableId: string) => void;
}

const STATUS_COLOR: Record<string, string> = {
  waiting: '#2196f3',
  playing: '#4caf50',
  finished: '#888',
};

const STATUS_LABEL: Record<string, string> = {
  waiting: 'Waiting',
  playing: '● Live',
  finished: 'Finished',
};

function StatCard({ label, value, color = '#ffd700' }: { label: string; value: string | number; color?: string }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.05)',
      border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: '10px',
      padding: '14px 20px',
      textAlign: 'center',
      minWidth: '110px',
    }}>
      <div style={{ fontSize: '1.6rem', fontWeight: 800, color }}>{value}</div>
      <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
    </div>
  );
}

export const Lobby: React.FC<LobbyProps> = ({ onWatchTable }) => {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateTable, setShowCreateTable] = useState(false);
  const [showCreateAgent, setShowCreateAgent] = useState(false);

  // Create table form state
  const [tableName, setTableName] = useState('Table 1');
  const [smallBlind, setSmallBlind] = useState(10);
  const [bigBlind, setBigBlind] = useState(20);
  const [maxPlayers, setMaxPlayers] = useState(6);
  const [creating, setCreating] = useState(false);

  // Agent registration form
  const [agentName, setAgentName] = useState('');
  const [agentType, setAgentType] = useState('random');
  const [agentEndpoint, setAgentEndpoint] = useState('');
  const [registeringAgent, setRegisteringAgent] = useState(false);
  const [agentSuccess, setAgentSuccess] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [t, s, a] = await Promise.allSettled([
        api.getTables(),
        api.getStats(),
        api.getAgents(),
      ]);
      if (t.status === 'fulfilled') setTables(t.value);
      if (s.status === 'fulfilled') setStats(s.value);
      if (a.status === 'fulfilled') setAgents(a.value);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleCreateTable = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.createTable({ name: tableName, small_blind: smallBlind, big_blind: bigBlind, max_players: maxPlayers });
      setShowCreateTable(false);
      setTableName('Table 1');
      await fetchData();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create table');
    } finally {
      setCreating(false);
    }
  };

  const handleRegisterAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegisteringAgent(true);
    setAgentSuccess(null);
    try {
      const agent = await api.registerAgent({
        name: agentName,
        type: agentType,
        endpoint: agentEndpoint || undefined,
      });
      setAgentSuccess(`Agent "${agent.name}" registered!`);
      setAgentName('');
      setAgentEndpoint('');
      await fetchData();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to register agent');
    } finally {
      setRegisteringAgent(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    background: 'rgba(255,255,255,0.07)',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '8px',
    padding: '8px 12px',
    color: '#fff',
    fontSize: '0.85rem',
    width: '100%',
    outline: 'none',
  };

  const btnPrimary: React.CSSProperties = {
    background: 'linear-gradient(135deg, #35654d, #1f4a37)',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '8px',
    color: '#fff',
    padding: '9px 20px',
    fontSize: '0.85rem',
    fontWeight: 700,
    cursor: 'pointer',
    transition: 'opacity 0.15s',
  };

  const btnSecondary: React.CSSProperties = {
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '8px',
    color: '#ccc',
    padding: '9px 20px',
    fontSize: '0.85rem',
    cursor: 'pointer',
  };

  const modalBg: React.CSSProperties = {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  };

  const modalBox: React.CSSProperties = {
    background: '#1e2340',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '14px',
    padding: '28px',
    minWidth: '360px',
    maxWidth: '90vw',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  };

  return (
    <div style={{ minHeight: '100vh', padding: '0 0 60px' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(180deg, #0f1628 0%, #1a1a2e 100%)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        padding: '20px 40px',
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <h1 style={{ fontSize: '1.9rem', fontWeight: 900, color: '#ffd700', letterSpacing: '-0.02em' }}>
                ♠ AI Poker
              </h1>
              <p style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)', marginTop: '2px' }}>
                Texas Hold'em Observer Platform
              </p>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              {stats && (
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <StatCard label="Total Games" value={stats.total_games} />
                  <StatCard label="Active Tables" value={stats.active_tables} color="#4caf50" />
                  <StatCard label="Agents" value={stats.total_agents} color="#2196f3" />
                  <StatCard label="Hands Played" value={stats.total_hands} color="#e91e63" />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 40px' }}>
        {error && (
          <div style={{
            background: 'rgba(244,67,54,0.12)',
            border: '1px solid rgba(244,67,54,0.35)',
            borderRadius: '8px',
            padding: '10px 16px',
            marginBottom: '20px',
            color: '#f44336',
            fontSize: '0.85rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span>⚠ {error}</span>
            <button onClick={() => setError(null)} style={{ background: 'none', border: 'none', color: '#f44336', cursor: 'pointer', fontSize: '1rem' }}>✕</button>
          </div>
        )}

        {/* Tables section */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'rgba(255,255,255,0.85)' }}>
            Tables
            {tables.length > 0 && (
              <span style={{ marginLeft: '10px', fontSize: '0.8rem', color: 'rgba(255,255,255,0.35)', fontWeight: 400 }}>
                {tables.length} available
              </span>
            )}
          </h2>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button style={btnSecondary} onClick={fetchData}>↻ Refresh</button>
            <button style={btnPrimary} onClick={() => setShowCreateTable(true)}>+ Create Table</button>
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'rgba(255,255,255,0.3)', fontSize: '0.9rem' }}>
            Loading tables…
          </div>
        ) : tables.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '60px',
            color: 'rgba(255,255,255,0.25)',
            border: '2px dashed rgba(255,255,255,0.08)',
            borderRadius: '12px',
          }}>
            <div style={{ fontSize: '2rem', marginBottom: '12px' }}>♠ ♥ ♣ ♦</div>
            <div style={{ fontSize: '0.95rem', marginBottom: '6px' }}>No tables yet</div>
            <div style={{ fontSize: '0.8rem' }}>Create a table to get started</div>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '16px',
            marginBottom: '40px',
          }}>
            {tables.map(table => (
              <div key={table.id} style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                transition: 'border-color 0.2s',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '1rem', color: '#fff' }}>{table.name}</div>
                    <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)', marginTop: '2px', fontFamily: 'monospace' }}>
                      {table.id.slice(0, 12)}…
                    </div>
                  </div>
                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    color: STATUS_COLOR[table.status] ?? '#888',
                    padding: '3px 9px',
                    borderRadius: '20px',
                    border: `1px solid ${STATUS_COLOR[table.status] ?? '#888'}`,
                    background: `${STATUS_COLOR[table.status] ?? '#888'}18`,
                  }}>
                    {STATUS_LABEL[table.status] ?? table.status}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '16px', fontSize: '0.8rem' }}>
                  <div>
                    <div style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Players</div>
                    <div style={{ color: '#fff', fontWeight: 700 }}>{table.player_count} / {table.max_players}</div>
                  </div>
                  <div>
                    <div style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Blinds</div>
                    <div style={{ color: '#ffd700', fontWeight: 700 }}>${table.small_blind} / ${table.big_blind}</div>
                  </div>
                </div>

                {/* Seat bar */}
                <div style={{ display: 'flex', gap: '4px' }}>
                  {Array.from({ length: table.max_players }).map((_, i) => (
                    <div key={i} style={{
                      flex: 1,
                      height: '6px',
                      borderRadius: '3px',
                      background: i < table.player_count ? '#35654d' : 'rgba(255,255,255,0.1)',
                    }} />
                  ))}
                </div>

                <button
                  style={{
                    ...btnPrimary,
                    opacity: table.status === 'finished' ? 0.5 : 1,
                    cursor: table.status === 'finished' ? 'not-allowed' : 'pointer',
                  }}
                  onClick={() => onWatchTable(table.id)}
                  disabled={table.status === 'finished'}
                >
                  👁 Watch Table
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Agents section */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'rgba(255,255,255,0.85)' }}>
            Agents
            {agents.length > 0 && (
              <span style={{ marginLeft: '10px', fontSize: '0.8rem', color: 'rgba(255,255,255,0.35)', fontWeight: 400 }}>
                {agents.length} registered
              </span>
            )}
          </h2>
          <button style={btnPrimary} onClick={() => { setShowCreateAgent(true); setAgentSuccess(null); }}>
            + Register Agent
          </button>
        </div>

        {agents.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: 'rgba(255,255,255,0.25)',
            border: '2px dashed rgba(255,255,255,0.08)',
            borderRadius: '12px',
          }}>
            <div style={{ fontSize: '0.9rem', marginBottom: '4px' }}>No agents registered</div>
            <div style={{ fontSize: '0.78rem' }}>Register an agent to play at tables</div>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: '12px',
          }}>
            {agents.map(agent => (
              <div key={agent.id} style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '10px',
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.2rem' }}>🤖</span>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{agent.name}</div>
                    <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)' }}>{agent.type}</div>
                  </div>
                </div>
                <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.25)', fontFamily: 'monospace' }}>
                  {agent.id.slice(0, 16)}…
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Table Modal */}
      {showCreateTable && (
        <div style={modalBg} onClick={() => setShowCreateTable(false)}>
          <div style={modalBox} onClick={e => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '4px' }}>Create New Table</h3>
            <form onSubmit={handleCreateTable} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: '5px' }}>Table Name</label>
                <input
                  style={inputStyle}
                  value={tableName}
                  onChange={e => setTableName(e.target.value)}
                  required
                  placeholder="e.g. High Stakes Table"
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: '5px' }}>Small Blind</label>
                  <input
                    style={inputStyle}
                    type="number"
                    min={1}
                    value={smallBlind}
                    onChange={e => setSmallBlind(Number(e.target.value))}
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: '5px' }}>Big Blind</label>
                  <input
                    style={inputStyle}
                    type="number"
                    min={2}
                    value={bigBlind}
                    onChange={e => setBigBlind(Number(e.target.value))}
                    required
                  />
                </div>
              </div>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: '5px' }}>Max Players (2–10)</label>
                <input
                  style={inputStyle}
                  type="number"
                  min={2}
                  max={10}
                  value={maxPlayers}
                  onChange={e => setMaxPlayers(Number(e.target.value))}
                  required
                />
              </div>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '4px' }}>
                <button type="button" style={btnSecondary} onClick={() => setShowCreateTable(false)}>
                  Cancel
                </button>
                <button type="submit" style={btnPrimary} disabled={creating}>
                  {creating ? 'Creating…' : 'Create Table'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Register Agent Modal */}
      {showCreateAgent && (
        <div style={modalBg} onClick={() => setShowCreateAgent(false)}>
          <div style={modalBox} onClick={e => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '4px' }}>Register Agent</h3>
            {agentSuccess && (
              <div style={{ background: 'rgba(76,175,80,0.15)', border: '1px solid rgba(76,175,80,0.4)', borderRadius: '8px', padding: '10px 14px', color: '#4caf50', fontSize: '0.85rem' }}>
                ✓ {agentSuccess}
              </div>
            )}
            <form onSubmit={handleRegisterAgent} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: '5px' }}>Agent Name</label>
                <input
                  style={inputStyle}
                  value={agentName}
                  onChange={e => setAgentName(e.target.value)}
                  required
                  placeholder="e.g. MyPokerBot"
                />
              </div>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: '5px' }}>Agent Type</label>
                <select
                  style={{ ...inputStyle, cursor: 'pointer' }}
                  value={agentType}
                  onChange={e => setAgentType(e.target.value)}
                >
                  <option value="random">Random</option>
                  <option value="call_station">Call Station</option>
                  <option value="tight_aggressive">Tight Aggressive</option>
                  <option value="loose_aggressive">Loose Aggressive</option>
                  <option value="http">HTTP (external agent)</option>
                </select>
              </div>
              {agentType === 'http' && (
                <div>
                  <label style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: '5px' }}>
                    Agent Endpoint URL
                  </label>
                  <input
                    style={inputStyle}
                    value={agentEndpoint}
                    onChange={e => setAgentEndpoint(e.target.value)}
                    placeholder="http://localhost:5001/action"
                  />
                </div>
              )}
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '4px' }}>
                <button type="button" style={btnSecondary} onClick={() => setShowCreateAgent(false)}>
                  Close
                </button>
                <button type="submit" style={btnPrimary} disabled={registeringAgent}>
                  {registeringAgent ? 'Registering…' : 'Register'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
