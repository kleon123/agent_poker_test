import { useState } from 'react';
import { Lobby } from './components/Lobby';
import { PokerTable } from './components/PokerTable';
import { ActionLog } from './components/ActionLog';
import { GameInfo } from './components/GameInfo';
import { useWebSocket } from './hooks/useWebSocket';

type View = 'lobby' | 'table';

export default function App() {
  const [view, setView] = useState<View>('lobby');
  const [watchingTableId, setWatchingTableId] = useState<string | null>(null);

  const { gameState, actionLog, connected, error } = useWebSocket(
    view === 'table' ? watchingTableId : null
  );

  const handleWatchTable = (tableId: string) => {
    setWatchingTableId(tableId);
    setView('table');
  };

  const handleBackToLobby = () => {
    setView('lobby');
    setWatchingTableId(null);
  };

  if (view === 'lobby') {
    return <Lobby onWatchTable={handleWatchTable} />;
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#1a1a2e',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Top bar */}
      <div style={{
        background: 'rgba(0,0,0,0.6)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        padding: '10px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        flexShrink: 0,
      }}>
        <button
          onClick={handleBackToLobby}
          style={{
            background: 'rgba(255,255,255,0.07)',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: '8px',
            color: '#ccc',
            padding: '7px 14px',
            fontSize: '0.82rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          ← Back to Lobby
        </button>

        <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#ffd700' }}>
          ♠ AI Poker Observer
        </div>

        {watchingTableId && (
          <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)', fontFamily: 'monospace' }}>
            Table: {watchingTableId.slice(0, 16)}…
          </div>
        )}

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Connection status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.75rem',
            color: connected ? '#4caf50' : '#f44336',
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: connected ? '#4caf50' : '#f44336',
              boxShadow: connected ? '0 0 6px 1px rgba(76,175,80,0.5)' : 'none',
              animation: connected ? 'none' : 'pulse-glow 1s infinite',
              display: 'inline-block',
            }} />
            {connected ? 'Live' : 'Connecting…'}
          </div>

          {error && (
            <span style={{ fontSize: '0.72rem', color: '#f44336' }}>⚠ {error}</span>
          )}
        </div>
      </div>

      {/* Main content */}
      <div style={{
        flex: 1,
        display: 'flex',
        padding: '20px',
        gap: '16px',
        alignItems: 'flex-start',
        overflowX: 'auto',
      }}>
        {/* Left panel: Game info */}
        {gameState && (
          <div style={{ flexShrink: 0 }}>
            <GameInfo gameState={gameState} />
          </div>
        )}

        {/* Center: Poker table */}
        <div style={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minWidth: 0,
        }}>
          {!gameState ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '16px',
              color: 'rgba(255,255,255,0.3)',
            }}>
              <div style={{ fontSize: '3rem' }}>♠</div>
              <div style={{ fontSize: '1rem', fontWeight: 600 }}>
                {connected ? 'Waiting for game state…' : 'Connecting to table…'}
              </div>
              <div style={{ fontSize: '0.8rem' }}>
                {connected
                  ? 'The game will appear here when it starts'
                  : 'Establishing WebSocket connection'}
              </div>
              {/* Spinner */}
              <div style={{
                width: '32px',
                height: '32px',
                border: '3px solid rgba(255,255,255,0.1)',
                borderTop: '3px solid #35654d',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
              }} />
            </div>
          ) : (
            <PokerTable gameState={gameState} />
          )}
        </div>

        {/* Right panel: Action log */}
        <div style={{ flexShrink: 0, alignSelf: 'stretch' }}>
          <ActionLog entries={actionLog} />
        </div>
      </div>
    </div>
  );
}
