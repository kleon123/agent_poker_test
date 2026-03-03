import React, { useMemo } from 'react';
import { GameState, Player } from '../types/game';
import { PlayerSeat } from './PlayerSeat';
import { CommunityCards } from './CommunityCards';

interface PokerTableProps {
  gameState: GameState;
}

// Returns {x, y} positions around an ellipse for N seats.
// centerX, centerY: center of ellipse
// rx, ry: horizontal/vertical radii
function getSeatPositions(
  n: number,
  centerX: number,
  centerY: number,
  rx: number,
  ry: number
): Array<{ x: number; y: number }> {
  if (n === 0) return [];
  const positions: Array<{ x: number; y: number }> = [];
  // Start from bottom-center and go clockwise
  for (let i = 0; i < n; i++) {
    const angle = (Math.PI / 2) + (2 * Math.PI * i) / n; // start at bottom
    const x = centerX + rx * Math.cos(angle);
    const y = centerY + ry * Math.sin(angle);
    positions.push({ x, y });
  }
  return positions;
}

export const PokerTable: React.FC<PokerTableProps> = ({ gameState }) => {
  const TABLE_W = 820;
  const TABLE_H = 480;
  const CENTER_X = TABLE_W / 2;
  const CENTER_Y = TABLE_H / 2;
  const RX = 330; // horizontal radius for seats
  const RY = 195; // vertical radius for seats

  const players: Player[] = useMemo(
    () => Object.values(gameState.players),
    [gameState.players]
  );

  const seatPositions = useMemo(
    () => getSeatPositions(players.length, CENTER_X, CENTER_Y, RX, RY),
    [players.length]
  );

  // Felt ellipse dimensions (slightly smaller than seat ellipse)
  const feltRX = RX - 60;
  const feltRY = RY - 45;

  return (
    <div style={{
      position: 'relative',
      width: `${TABLE_W}px`,
      height: `${TABLE_H}px`,
      flexShrink: 0,
    }}>
      {/* SVG Table surface */}
      <svg
        width={TABLE_W}
        height={TABLE_H}
        style={{ position: 'absolute', top: 0, left: 0 }}
      >
        <defs>
          <radialGradient id="felt" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#3d7a5a" />
            <stop offset="100%" stopColor="#28503c" />
          </radialGradient>
          <radialGradient id="feltShadow" cx="50%" cy="50%" r="50%">
            <stop offset="60%" stopColor="transparent" />
            <stop offset="100%" stopColor="rgba(0,0,0,0.35)" />
          </radialGradient>
          <filter id="tableShadow" x="-5%" y="-5%" width="110%" height="110%">
            <feDropShadow dx="0" dy="4" stdDeviation="12" floodColor="rgba(0,0,0,0.7)" />
          </filter>
        </defs>

        {/* Table border / rail */}
        <ellipse
          cx={CENTER_X}
          cy={CENTER_Y}
          rx={feltRX + 18}
          ry={feltRY + 18}
          fill="#1a3a2a"
          filter="url(#tableShadow)"
        />

        {/* Felt surface */}
        <ellipse
          cx={CENTER_X}
          cy={CENTER_Y}
          rx={feltRX}
          ry={feltRY}
          fill="url(#felt)"
        />

        {/* Inner shadow on felt */}
        <ellipse
          cx={CENTER_X}
          cy={CENTER_Y}
          rx={feltRX}
          ry={feltRY}
          fill="url(#feltShadow)"
        />

        {/* Center logo text */}
        <text
          x={CENTER_X}
          y={CENTER_Y + 68}
          textAnchor="middle"
          fill="rgba(255,255,255,0.06)"
          fontSize="18"
          fontWeight="800"
          letterSpacing="6"
          fontFamily="sans-serif"
        >
          AI POKER
        </text>
      </svg>

      {/* Community cards in center */}
      <div style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -58%)',
        zIndex: 5,
      }}>
        <CommunityCards cards={gameState.community_cards} phase={gameState.phase} />
      </div>

      {/* Pot display in center */}
      <div style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, 30%)',
        zIndex: 5,
        textAlign: 'center',
      }}>
        {gameState.pot > 0 && (
          <div style={{
            background: 'rgba(0,0,0,0.55)',
            border: '1px solid rgba(255,215,0,0.3)',
            borderRadius: '20px',
            padding: '4px 14px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
          }}>
            <span style={{ fontSize: '0.65rem', color: 'rgba(255,215,0,0.6)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Pot</span>
            <span style={{ fontSize: '0.95rem', fontWeight: 800, color: '#ffd700' }}>${gameState.pot.toLocaleString()}</span>
          </div>
        )}
      </div>

      {/* Player seats */}
      {players.map((player, i) => (
        <PlayerSeat
          key={player.id}
          player={player}
          isCurrentPlayer={player.id === gameState.current_player_id}
          position={seatPositions[i] ?? { x: 0, y: 0 }}
          seatIndex={i}
        />
      ))}

      {/* Waiting overlay */}
      {gameState.phase === 'waiting' && (
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 20,
        }}>
          <div style={{
            background: 'rgba(0,0,0,0.65)',
            borderRadius: '12px',
            padding: '16px 28px',
            border: '1px solid rgba(255,255,255,0.1)',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffd700' }}>Waiting for game to start…</div>
            <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)', marginTop: '6px' }}>
              {players.length} player{players.length !== 1 ? 's' : ''} at table
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
