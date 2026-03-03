import React from 'react';
import { GameState } from '../types/game';

interface GameInfoProps {
  gameState: GameState;
}

const PHASE_COLORS: Record<string, string> = {
  waiting: '#888',
  pre_flop: '#2196f3',
  flop: '#4caf50',
  turn: '#ff9800',
  river: '#e91e63',
  showdown: '#ffd700',
  finished: '#888',
};

export const GameInfo: React.FC<GameInfoProps> = ({ gameState }) => {
  const currentPlayer = gameState.current_player_id
    ? gameState.players[gameState.current_player_id]
    : null;

  const phaseColor = PHASE_COLORS[gameState.phase ?? 'waiting'] ?? '#888';
  const phaseLabel = (gameState.phase ?? 'waiting').replace(/_/g, ' ');

  return (
    <div style={{
      background: 'rgba(0,0,0,0.6)',
      borderRadius: '12px',
      border: '1px solid rgba(255,255,255,0.1)',
      padding: '14px 18px',
      display: 'flex',
      flexDirection: 'column',
      gap: '10px',
      minWidth: '200px',
    }}>
      <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', letterSpacing: '0.1em', textTransform: 'uppercase', fontWeight: 600 }}>
        Game Info
      </div>

      {/* Phase */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{
          display: 'inline-block',
          padding: '3px 10px',
          borderRadius: '20px',
          background: `${phaseColor}22`,
          border: `1px solid ${phaseColor}`,
          color: phaseColor,
          fontSize: '0.75rem',
          fontWeight: 700,
          letterSpacing: '0.05em',
        }}>
          {phaseLabel}
        </span>
        <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.7rem' }}>
          Hand #{gameState.hand_number}
        </span>
      </div>

      {/* Pot */}
      <div>
        <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', marginBottom: '2px' }}>POT</div>
        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ffd700', letterSpacing: '-0.02em' }}>
          ${gameState.pot.toLocaleString()}
        </div>
      </div>

      {/* Current bet */}
      {gameState.current_bet > 0 && (
        <div>
          <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', marginBottom: '2px' }}>CURRENT BET</div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>
            ${gameState.current_bet.toLocaleString()}
          </div>
        </div>
      )}

      {/* Current player */}
      {currentPlayer && gameState.phase !== 'waiting' && (
        <div style={{
          padding: '8px 10px',
          background: 'rgba(255,215,0,0.08)',
          border: '1px solid rgba(255,215,0,0.3)',
          borderRadius: '8px',
        }}>
          <div style={{ fontSize: '0.62rem', color: 'rgba(255,215,0,0.6)', marginBottom: '3px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Acting Now
          </div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ffd700' }}>
            {currentPlayer.name}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.5)' }}>
            ${currentPlayer.chips.toLocaleString()} chips
          </div>
        </div>
      )}

      {/* Player count */}
      <div style={{ display: 'flex', gap: '12px' }}>
        <div>
          <div style={{ fontSize: '0.62rem', color: 'rgba(255,255,255,0.4)' }}>PLAYERS</div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700 }}>
            {Object.keys(gameState.players).length}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.62rem', color: 'rgba(255,255,255,0.4)' }}>ACTIVE</div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#4caf50' }}>
            {Object.values(gameState.players).filter(p => p.status === 'active').length}
          </div>
        </div>
      </div>
    </div>
  );
};
