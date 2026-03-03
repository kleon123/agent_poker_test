export type Suit = 'HEARTS' | 'DIAMONDS' | 'CLUBS' | 'SPADES';
export type Rank = '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | '10' | 'J' | 'Q' | 'K' | 'A';

export interface Card {
  rank: Rank;
  suit: Suit;
}

export type PlayerStatus = 'active' | 'folded' | 'all_in' | 'sitting_out';
export type GamePhase = 'PRE_FLOP' | 'FLOP' | 'TURN' | 'RIVER' | 'SHOWDOWN' | 'WAITING';

export interface Player {
  id: string;
  name: string;
  chips: number;
  cards: Card[];
  status: PlayerStatus;
  current_bet: number;
  is_dealer: boolean;
  is_small_blind: boolean;
  is_big_blind: boolean;
}

export interface GameState {
  game_id: string;
  table_id: string;
  phase: GamePhase;
  players: Record<string, Player>;
  community_cards: Card[];
  pot: number;
  current_bet: number;
  current_player_id: string | null;
  hand_number: number;
}

export interface TableInfo {
  id: string;
  name: string;
  player_count: number;
  max_players: number;
  small_blind: number;
  big_blind: number;
  status: 'waiting' | 'playing' | 'finished';
  game_id?: string;
}

export interface AgentInfo {
  id: string;
  name: string;
  type: string;
  created_at?: string;
}

export interface PlatformStats {
  total_games: number;
  active_tables: number;
  total_agents: number;
  total_hands: number;
}

export interface ActionEvent {
  player: Player;
  action: string;
  amount: number | null;
  pot: number;
}

export interface PhaseChangeEvent {
  phase: GamePhase;
  community_cards: Card[];
}

export interface HandResultEvent {
  winners: Array<{ player: Player; amount: number; hand_description?: string }>;
  pot: number;
}

export interface ActionLogEntry {
  id: string;
  timestamp: Date;
  type: 'action' | 'phase_change' | 'hand_result' | 'player_joined' | 'error' | 'info';
  message: string;
  data?: unknown;
}
