import { TableInfo, AgentInfo, PlatformStats, GameState } from '../types/game';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getTables: () => request<TableInfo[]>('/tables'),

  createTable: (data: { name: string; small_blind: number; big_blind: number; max_players: number }) =>
    request<TableInfo>('/tables', { method: 'POST', body: JSON.stringify(data) }),

  joinTable: (tableId: string, data: { agent_id: string }) =>
    request<{ success: boolean }>(`/tables/${tableId}/join`, { method: 'POST', body: JSON.stringify(data) }),

  startGame: (tableId: string) =>
    request<{ game_id: string }>(`/tables/${tableId}/start`, { method: 'POST' }),

  getGame: (gameId: string) => request<GameState>(`/games/${gameId}`),

  submitAction: (gameId: string, data: { action: string; amount?: number }) =>
    request<{ success: boolean }>(`/games/${gameId}/action`, { method: 'POST', body: JSON.stringify(data) }),

  registerAgent: (data: { name: string; type: string; endpoint?: string }) =>
    request<AgentInfo>('/agents/register', { method: 'POST', body: JSON.stringify(data) }),

  getAgents: () => request<AgentInfo[]>('/agents'),

  getStats: () => request<PlatformStats>('/stats'),
};
