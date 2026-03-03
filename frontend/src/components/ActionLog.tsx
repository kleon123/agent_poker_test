import React, { useEffect, useRef } from 'react';
import { ActionLogEntry } from '../types/game';

interface ActionLogProps {
  entries: ActionLogEntry[];
}

const TYPE_STYLES: Record<string, { color: string; icon: string }> = {
  action:        { color: '#e0e0e0', icon: '▶' },
  phase_change:  { color: '#2196f3', icon: '⟳' },
  hand_result:   { color: '#ffd700', icon: '🏆' },
  player_joined: { color: '#4caf50', icon: '→' },
  error:         { color: '#f44336', icon: '✕' },
  info:          { color: '#888',    icon: 'ℹ' },
};

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export const ActionLog: React.FC<ActionLogProps> = ({ entries }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [entries]);

  return (
    <div style={{
      background: 'rgba(0,0,0,0.6)',
      borderRadius: '12px',
      border: '1px solid rgba(255,255,255,0.1)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      minWidth: '260px',
      maxWidth: '320px',
      height: '100%',
      maxHeight: '480px',
    }}>
      <div style={{
        padding: '10px 14px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        fontSize: '0.7rem',
        color: 'rgba(255,255,255,0.4)',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        fontWeight: 600,
        flexShrink: 0,
      }}>
        Action Log
        <span style={{ marginLeft: '8px', color: 'rgba(255,255,255,0.25)', fontSize: '0.65rem' }}>
          ({entries.length})
        </span>
      </div>

      <div style={{
        overflowY: 'auto',
        flex: 1,
        padding: '8px 0',
      }}>
        {entries.length === 0 ? (
          <div style={{ padding: '20px 14px', color: 'rgba(255,255,255,0.25)', fontSize: '0.8rem', textAlign: 'center' }}>
            Waiting for game actions…
          </div>
        ) : (
          entries.map(entry => {
            const style = TYPE_STYLES[entry.type] ?? TYPE_STYLES.info;
            return (
              <div key={entry.id} style={{
                padding: '5px 14px',
                borderBottom: '1px solid rgba(255,255,255,0.04)',
                animation: 'fadeIn 0.2s ease-out',
                display: 'flex',
                gap: '8px',
                alignItems: 'flex-start',
              }}>
                <span style={{ color: style.color, fontSize: '0.7rem', marginTop: '1px', flexShrink: 0 }}>
                  {style.icon}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: style.color, fontSize: '0.78rem', lineHeight: 1.4, wordBreak: 'break-word' }}>
                    {entry.message}
                  </div>
                  <div style={{ color: 'rgba(255,255,255,0.25)', fontSize: '0.62rem', marginTop: '1px' }}>
                    {formatTime(entry.timestamp)}
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
