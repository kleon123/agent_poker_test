import React from 'react';
import Card from './Card';

function CommunityCards({ cards = [] }) {
  const placeholders = 5 - cards.length;

  return (
    <div className="community-cards-area">
      <div className="community-cards-label">Community Cards</div>
      <div className="community-cards">
        {cards.map((card, i) => (
          <Card key={i} card={card} />
        ))}
        {Array.from({ length: placeholders }).map((_, i) => (
          <div key={`ph-${i}`} className="card face-down" style={{ opacity: 0.3 }} />
        ))}
      </div>
    </div>
  );
}

export default CommunityCards;
