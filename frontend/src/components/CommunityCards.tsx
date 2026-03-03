import React from 'react';
import { Card as CardType } from '../types/game';
import { Card } from './Card';

interface CommunityCardsProps {
  cards: CardType[];
  phase: string;
}

export const CommunityCards: React.FC<CommunityCardsProps> = ({ cards, phase }) => {
  const phaseLabel = phase.replace('_', ' ');

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '8px',
    }}>
      <div style={{
        fontSize: '0.7rem',
        color: 'rgba(255,255,255,0.5)',
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        fontWeight: 600,
      }}>
        {phaseLabel}
      </div>
      <div style={{ display: 'flex', gap: '6px', alignItems: 'center', minHeight: '5rem' }}>
        {cards.length === 0 ? (
          <div style={{ color: 'rgba(255,255,255,0.2)', fontSize: '0.8rem', fontStyle: 'italic' }}>
            No community cards yet
          </div>
        ) : (
          cards.map((card, i) => (
            <Card key={`${card.rank}-${card.suit}-${i}`} card={card} size="medium" />
          ))
        )}
        {/* Placeholder slots */}
        {Array.from({ length: Math.max(0, 5 - cards.length) }).map((_, i) => (
          <div key={`placeholder-${i}`} style={{
            width: '3.6rem',
            height: '5rem',
            borderRadius: '6px',
            border: '2px dashed rgba(255,255,255,0.1)',
            flexShrink: 0,
          }} />
        ))}
      </div>
    </div>
  );
};
