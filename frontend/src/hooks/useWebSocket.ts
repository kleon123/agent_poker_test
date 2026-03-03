import { useState, useEffect, useRef, useCallback } from 'react';
import { GameState, ActionLogEntry, ActionEvent, PhaseChangeEvent, HandResultEvent, Player } from '../types/game';

interface WSMessage {
  type: string;
  data: unknown;
}

interface UseWebSocketResult {
  gameState: GameState | null;
  lastAction: ActionEvent | null;
  actionLog: ActionLogEntry[];
  connected: boolean;
  error: string | null;
}

function formatAction(action: ActionEvent): string {
  const name = action.player?.name ?? 'Unknown';
  const act = action.action?.toLowerCase() ?? '';
  switch (act) {
    case 'fold': return `${name} folds`;
    case 'check': return `${name} checks`;
    case 'call': return `${name} calls ${action.amount != null ? `$${action.amount}` : ''}`;
    case 'raise': return `${name} raises to $${action.amount ?? 0}`;
    case 'bet': return `${name} bets $${action.amount ?? 0}`;
    case 'all_in': return `${name} goes ALL IN with $${action.amount ?? 0}`;
    default: return `${name} ${act}${action.amount != null ? ` $${action.amount}` : ''}`;
  }
}

function phaseLabel(phase: string): string {
  return phase.replace('_', ' ');
}

let logIdCounter = 0;
function makeEntry(type: ActionLogEntry['type'], message: string, data?: unknown): ActionLogEntry {
  return { id: `log-${++logIdCounter}`, timestamp: new Date(), type, message, data };
}

export function useWebSocket(tableId: string | null): UseWebSocketResult {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [lastAction, setLastAction] = useState<ActionEvent | null>(null);
  const [actionLog, setActionLog] = useState<ActionLogEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmounted = useRef(false);

  const addLog = useCallback((entry: ActionLogEntry) => {
    setActionLog(prev => [...prev.slice(-99), entry]);
  }, []);

  const connect = useCallback(() => {
    if (!tableId || unmounted.current) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/observer/${tableId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (unmounted.current) return;
      setConnected(true);
      setError(null);
      addLog(makeEntry('info', 'Connected to table observer'));
    };

    ws.onmessage = (event) => {
      if (unmounted.current) return;
      try {
        const msg: WSMessage = JSON.parse(event.data as string);
        switch (msg.type) {
          case 'game_state': {
            setGameState(msg.data as GameState);
            break;
          }
          case 'action': {
            const actionData = msg.data as ActionEvent;
            setLastAction(actionData);
            addLog(makeEntry('action', formatAction(actionData), actionData));
            break;
          }
          case 'phase_change': {
            const phaseData = msg.data as PhaseChangeEvent;
            addLog(makeEntry('phase_change', `Phase changed to ${phaseLabel(phaseData.phase)}`, phaseData));
            setGameState(prev => prev ? { ...prev, phase: phaseData.phase, community_cards: phaseData.community_cards } : prev);
            break;
          }
          case 'hand_result': {
            const result = msg.data as HandResultEvent;
            const winnerNames = result.winners.map((w: { player?: Player; player_name?: string; amount: number; hand_description?: string; hand?: string }) =>
              `${w.player?.name ?? w.player_name ?? 'Unknown'} wins $${w.amount}${(w.hand_description ?? w.hand) ? ` (${w.hand_description ?? w.hand})` : ''}`
            ).join(', ');
            addLog(makeEntry('hand_result', `Hand over — ${winnerNames}`, result));
            break;
          }
          case 'player_joined': {
            const pData = msg.data as Player;
            addLog(makeEntry('player_joined', `${pData?.name ?? 'A player'} joined the table`, pData));
            break;
          }
          case 'error': {
            const errData = msg.data as { message: string };
            addLog(makeEntry('error', `Error: ${errData?.message ?? 'Unknown error'}`, errData));
            break;
          }
          default:
            break;
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      if (unmounted.current) return;
      setConnected(false);
      addLog(makeEntry('info', 'Disconnected — reconnecting in 3s…'));
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      if (unmounted.current) return;
      setError('WebSocket connection failed');
    };
  }, [tableId, addLog]);

  useEffect(() => {
    unmounted.current = false;
    setGameState(null);
    setLastAction(null);
    setActionLog([]);
    setConnected(false);

    if (tableId) connect();

    return () => {
      unmounted.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [tableId, connect]);

  return { gameState, lastAction, actionLog, connected, error };
}
