import React from 'react';
import { Player as PlayerType } from '../types/game';
import { Card } from './Card';

interface PlayerSeatProps {
  player: PlayerType;
  isCurrentPlayer: boolean;
  position: { x: number; y: number };
  seatIndex: number;
}

const STATUS_COLORS: Record<string, string> = {
  active: '#4caf50',
  folded: '#666',
  all_in: '#ff9800',
  sitting_out: '#555',
};

export const PlayerSeat: React.FC<PlayerSeatProps> = ({ player, isCurrentPlayer, position }) => {
  const isFolded = player.status === 'folded';
  const isAllIn = player.status === 'all_in';
  const hasCards = player.cards && player.cards.length > 0;

  const seatStyle: React.CSSProperties = {
    position: 'absolute',
    left: `${position.x}px`,
    top: `${position.y}px`,
    transform: 'translate(-50%, -50%)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
    zIndex: 10,
    opacity: isFolded ? 0.45 : 1,
    transition: 'opacity 0.3s ease',
    minWidth: '100px',
  };

  const cardContainerStyle: React.CSSProperties = {
    display: 'flex',
    gap: '3px',
  };

  const nameBoxStyle: React.CSSProperties = {
    background: isCurrentPlayer
      ? 'linear-gradient(135deg, #2a2a0a, #1a1a00)'
      : 'rgba(0,0,0,0.75)',
    border: `2px solid ${isCurrentPlayer ? '#ffd700' : 'rgba(255,255,255,0.15)'}`,
    borderRadius: '10px',
    padding: '6px 10px',
    textAlign: 'center',
    minWidth: '90px',
    boxShadow: isCurrentPlayer
      ? '0 0 12px 3px rgba(255,215,0,0.5), 0 0 30px 6px rgba(255,215,0,0.25)'
      : '0 2px 8px rgba(0,0,0,0.5)',
    animation: isCurrentPlayer ? 'pulse-glow 1.5s ease-in-out infinite' : 'none',
  };

  const badges: React.ReactNode[] = [];
  if (player.is_dealer) badges.push(
    <span key="d" style={{ background: '#ffd700', color: '#000', borderRadius: '50%', width: '18px', height: '18px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.6rem', fontWeight: 900, marginLeft: '4px' }}>D</span>
  );
  if (player.is_small_blind) badges.push(
    <span key="sb" style={{ background: '#2196f3', color: '#fff', borderRadius: '50%', width: '18px', height: '18px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.55rem', fontWeight: 700, marginLeft: '4px' }}>SB</span>
  );
  if (player.is_big_blind) badges.push(
    <span key="bb" style={{ background: '#9c27b0', color: '#fff', borderRadius: '50%', width: '18px', height: '18px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.55rem', fontWeight: 700, marginLeft: '4px' }}>BB</span>
  );

  return (
    <div style={seatStyle}>
      {/* Cards above or below based on position */}
      {hasCards && (
        <div style={cardContainerStyle}>
          {player.cards.map((card, i) => (
            <Card key={i} card={card} size="small" />
          ))}
        </div>
      )}

      {/* Name / info box */}
      <div style={nameBoxStyle}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px', flexWrap: 'wrap' }}>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            color: isFolded ? '#888' : '#fff',
            whiteSpace: 'nowrap',
            maxWidth: '80px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}>
            {player.name}
          </span>
          {badges}
        </div>
        <div style={{
          fontSize: '0.7rem',
          color: '#ffd700',
          fontWeight: 600,
          marginTop: '2px',
        }}>
          ${player.chips.toLocaleString()}
        </div>

        {/* Status indicators */}
        <div style={{ display: 'flex', gap: '4px', justifyContent: 'center', marginTop: '2px', flexWrap: 'wrap' }}>
          {isAllIn && (
            <span style={{
              background: '#ff9800',
              color: '#000',
              fontSize: '0.55rem',
              fontWeight: 900,
              padding: '1px 5px',
              borderRadius: '4px',
            }}>
              ALL IN
            </span>
          )}
          {isFolded && (
            <span style={{
              background: '#555',
              color: '#aaa',
              fontSize: '0.55rem',
              fontWeight: 700,
              padding: '1px 5px',
              borderRadius: '4px',
            }}>
              FOLDED
            </span>
          )}
          {!isFolded && !isAllIn && (
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: STATUS_COLORS[player.status] ?? '#666',
              display: 'inline-block',
              boxShadow: player.status === 'active' ? '0 0 4px 1px rgba(76,175,80,0.6)' : 'none',
            }} />
          )}
        </div>

        {/* Current bet */}
        {player.current_bet > 0 && !isFolded && (
          <div style={{
            marginTop: '3px',
            fontSize: '0.65rem',
            color: 'rgba(255,255,255,0.7)',
          }}>
            Bet: <span style={{ color: '#ffd700' }}>${player.current_bet}</span>
          </div>
        )}
      </div>
    </div>
  );
};
