import React from 'react';
import Card from './Card';

// Seat positions around the table (percentage of container)
const SEAT_POSITIONS = [
  { top: '50%', left: '5%' },   // 0 - left
  { top: '10%', left: '20%' },  // 1 - upper left
  { top: '5%',  left: '50%' },  // 2 - top center
  { top: '10%', left: '80%' },  // 3 - upper right
  { top: '50%', left: '95%' },  // 4 - right
  { top: '90%', left: '80%' },  // 5 - lower right
  { top: '90%', left: '50%' },  // 6 - bottom center
  { top: '90%', left: '20%' },  // 7 - lower left
  { top: '10%', left: '5%' },   // 8 - far upper left
  { top: '10%', left: '95%' },  // 9 - far upper right
];

function PlayerSeat({ player, seatIndex, dealerSeat, isCurrentPlayer, myPlayerId }) {
  const pos = SEAT_POSITIONS[seatIndex] || { top: '50%', left: '50%' };
  const isDealer = player && player.seat === dealerSeat;
  const isMe = player && player.player_id === myPlayerId;

  if (!player) {
    return (
      <div
        className="player-seat empty-seat"
        style={{ top: pos.top, left: pos.left }}
      >
        <div className="empty-seat-label">Empty</div>
      </div>
    );
  }

  const classes = [
    'player-seat',
    isCurrentPlayer ? 'is-current' : '',
    player.is_folded ? 'is-folded' : '',
    player.is_all_in ? 'is-all-in' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} style={{ top: pos.top, left: pos.left }}>
      <div className="seat-name">
        {isDealer && <span className="dealer-btn">D</span>}
        {player.name}
        {isMe && ' (You)'}
      </div>
      <div className="seat-chips">💰 {player.chips}</div>
      {player.current_bet > 0 && (
        <div className="seat-bet">Bet: {player.current_bet}</div>
      )}
      <div className="seat-status">
        {player.is_folded && '(Folded)'}
        {player.is_all_in && '(All-In)'}
        {isCurrentPlayer && !player.is_folded && !player.is_all_in && '⚡ Acting'}
      </div>
      <div className="seat-cards">
        {player.hole_cards_count > 0 && player.hole_cards.map((card, i) => (
          card ? <Card key={i} card={card} size="small" /> :
            <div key={i} className="seat-card-placeholder" />
        ))}
      </div>
    </div>
  );
}

export default PlayerSeat;
