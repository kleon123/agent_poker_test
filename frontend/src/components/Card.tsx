import React from 'react';
import { Card as CardType } from '../types/game';

const SUIT_SYMBOLS: Record<string, string> = {
  hearts: '♥',
  diamonds: '♦',
  clubs: '♣',
  spades: '♠',
};

const RED_SUITS = new Set(['hearts', 'diamonds']);

const RANK_LABELS: Record<number, string> = {
  2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8',
  9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K', 14: 'A',
};

const DIMENSIONS = {
  small:  { width: '2.8rem', height: '3.8rem', fontSize: '0.85rem', suitSize: '1rem' },
  medium: { width: '3.6rem', height: '5rem',   fontSize: '1.05rem', suitSize: '1.3rem' },
  large:  { width: '4.5rem', height: '6.2rem', fontSize: '1.3rem',  suitSize: '1.6rem' },
} as const;

interface CardProps {
  card: CardType;
  size?: 'small' | 'medium' | 'large';
  faceDown?: boolean;
}

export const Card: React.FC<CardProps> = ({ card, size = 'small', faceDown = false }) => {
  const d = DIMENSIONS[size];
  const isRed = RED_SUITS.has(card.suit);
  const symbol = SUIT_SYMBOLS[card.suit] ?? '?';
  const rankLabel = RANK_LABELS[card.rank] ?? String(card.rank);

  if (faceDown) {
    return (
      <div style={{
        width: d.width,
        height: d.height,
        borderRadius: '6px',
        background: 'linear-gradient(135deg, #1a3a6e 0%, #0d1f3c 100%)',
        border: '2px solid rgba(255,255,255,0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: d.suitSize,
        color: 'rgba(255,255,255,0.15)',
        boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
        flexShrink: 0,
      }}>
        ♠
      </div>
    );
  }

  return (
    <div style={{
      width: d.width,
      height: d.height,
      borderRadius: '6px',
      background: '#fff',
      border: '1px solid #ccc',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '2px 3px',
      color: isRed ? '#cc0000' : '#111',
      boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
      flexShrink: 0,
      animation: 'dealCard 0.3s ease-out',
      userSelect: 'none',
    }}>
      <span style={{ fontSize: d.fontSize, fontWeight: 700, lineHeight: 1, alignSelf: 'flex-start' }}>
        {rankLabel}
      </span>
      <span style={{ fontSize: d.suitSize, lineHeight: 1 }}>
        {symbol}
      </span>
      <span style={{ fontSize: d.fontSize, fontWeight: 700, lineHeight: 1, alignSelf: 'flex-end', transform: 'rotate(180deg)' }}>
        {rankLabel}
      </span>
    </div>
  );
};
