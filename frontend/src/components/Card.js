import React from 'react';

function Card({ card, faceDown = false, size = 'normal' }) {
  if (faceDown || !card) {
    return (
      <div className={`card face-down ${size === 'small' ? 'card-small' : ''}`} />
    );
  }

  const isRed = card.suit === 'hearts' || card.suit === 'diamonds';
  const suitSymbols = { spades: '♠', hearts: '♥', diamonds: '♦', clubs: '♣' };
  const rankNames = { 11: 'J', 12: 'Q', 13: 'K', 14: 'A' };
  const rank = rankNames[card.rank] || String(card.rank);
  const suit = suitSymbols[card.suit] || card.suit_symbol || card.suit;

  return (
    <div className={`card ${isRed ? 'red' : 'black'} ${size === 'small' ? 'card-small' : ''}`}>
      <span className="card-rank">{rank}</span>
      <span className="card-suit">{suit}</span>
    </div>
  );
}

export default Card;
