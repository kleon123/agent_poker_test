import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import useWebSocket from '../hooks/useWebSocket';
import PlayerSeat from './PlayerSeat';
import CommunityCards from './CommunityCards';
import GameLog from './GameLog';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const MAX_SEATS = 6;

function PokerTable() {
  const { tableId } = useParams();
  const { gameState, setGameState, connected } = useWebSocket(tableId);
  const [raiseAmount, setRaiseAmount] = useState(20);
  const [actionError, setActionError] = useState('');
  const [loading, setLoading] = useState(false);

  const apiKey = localStorage.getItem('poker_api_key') || '';
  const myAgentId = localStorage.getItem('poker_agent_id') || '';

  const state = gameState?.state || 'waiting';
  const players = gameState?.players || {};
  const communityCards = gameState?.community_cards || [];
  const totalPot = gameState?.total_pot || 0;
  const currentPlayerId = gameState?.current_player_id;
  const dealerSeat = gameState?.dealer_seat;
  const logs = gameState?.game_log || [];
  const winners = gameState?.winners || [];
  const isMyTurn = currentPlayerId === myAgentId;
  const maxPlayers = gameState?.max_players || MAX_SEATS;

  const sendAction = async (action, amount = 0) => {
    setActionError('');
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/tables/${tableId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
        body: JSON.stringify({ action, amount: Number(amount) }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setActionError(data.detail || 'Action failed');
      } else if (data.game_state) {
        setGameState(data.game_state);
      }
    } catch (e) {
      setActionError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const startGame = async () => {
    setActionError('');
    try {
      const resp = await fetch(`${API_BASE}/tables/${tableId}/start`, {
        method: 'POST',
        headers: { 'X-API-Key': apiKey },
      });
      const data = await resp.json();
      if (!resp.ok) setActionError(data.detail || 'Cannot start game');
    } catch (e) {
      setActionError('Network error');
    }
  };

  // Build seat list
  const seatPlayers = Array.from({ length: maxPlayers }, (_, i) => {
    const player = Object.values(players).find(p => p.seat === i);
    return player || null;
  });

  const myPlayer = players[myAgentId];
  const callAmount = myPlayer
    ? Math.max(0, Math.max(...Object.values(players).map(p => p.current_bet || 0)) - (myPlayer.current_bet || 0))
    : 0;

  return (
    <div className="poker-table-container">
      <div className="table-controls">
        <span style={{ color: connected ? '#4dff4d' : '#ff4d4d', fontSize: '0.85rem' }}>
          {connected ? '● Connected' : '○ Disconnected'}
        </span>
        <span style={{ color: '#889988', fontSize: '0.85rem' }}>
          Table: {gameState?.name || tableId?.slice(0, 8)}
        </span>
        {(state === 'waiting' || state === 'finished') && (
          <button onClick={startGame} className="btn-primary">Start Game</button>
        )}
      </div>

      {actionError && <div className="error-msg">{actionError}</div>}

      {winners.length > 0 && state === 'finished' && (
        <div className="winners-display">
          <h3>🏆 Winner{winners.length > 1 ? 's' : ''}!</h3>
          {winners.map((w, i) => (
            <div key={i} className="winner-entry">
              {w.name} wins {w.amount} chips with {w.hand}
            </div>
          ))}
        </div>
      )}

      <div className="poker-table-wrapper">
        <div className="poker-felt">
          <div className="table-center">
            {totalPot > 0 && (
              <div className="pot-display">💰 Pot: {totalPot}</div>
            )}
            <div className="game-status-display">{state.replace('_', ' ')}</div>
          </div>
        </div>

        <div className="player-seats">
          {seatPlayers.map((player, i) => (
            <PlayerSeat
              key={i}
              player={player}
              seatIndex={i}
              dealerSeat={dealerSeat}
              isCurrentPlayer={player && player.player_id === currentPlayerId}
              myPlayerId={myAgentId}
            />
          ))}
        </div>
      </div>

      <CommunityCards cards={communityCards} />

      {isMyTurn && state !== 'waiting' && state !== 'finished' && state !== 'showdown' && (
        <div className="action-panel">
          <h3>Your Turn{loading ? ' (processing...)' : ''}</h3>
          <div className="action-buttons">
            <button className="action-btn btn-fold" onClick={() => sendAction('fold')} disabled={loading}>
              Fold
            </button>
            {callAmount === 0 ? (
              <button className="action-btn btn-check" onClick={() => sendAction('check')} disabled={loading}>
                Check
              </button>
            ) : (
              <button className="action-btn btn-call" onClick={() => sendAction('call', callAmount)} disabled={loading}>
                Call {callAmount}
              </button>
            )}
            <button className="action-btn btn-allin" onClick={() => sendAction('all_in')} disabled={loading}>
              All-In
            </button>
          </div>
          <div className="raise-input">
            <input
              type="number"
              value={raiseAmount}
              min={gameState?.min_raise || 20}
              onChange={e => setRaiseAmount(e.target.value)}
            />
            <button className="action-btn btn-raise" onClick={() => sendAction('raise', raiseAmount)} disabled={loading}>
              Raise {raiseAmount}
            </button>
          </div>
        </div>
      )}

      <GameLog logs={logs} />
    </div>
  );
}

export default PokerTable;
