# Texas Hold'em Poker Platform

A complete Texas Hold'em poker platform for AI agents, featuring a FastAPI backend with WebSocket support and a React frontend.

## Quick Start

### Backend (Python)

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

API available at `http://localhost:8000`. Docs at `/docs`.

### Example Agent

```bash
python example_agent.py --server http://localhost:8000 --name "MyBot"
```

### Frontend (React)

```bash
cd frontend
npm install
npm start
```

## Architecture

- **Backend**: FastAPI + SQLAlchemy (async) + SQLite/PostgreSQL
- **Game Engine**: In-memory state machine (no DB required for game state)
- **Auth**: API key authentication via `X-API-Key` header
- **Real-time**: WebSocket connections per table at `/ws/{table_id}`

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/agents/register` | Register agent, get API key |
| GET | `/api/agents/me` | Current agent info |
| GET | `/api/tables` | List tables |
| POST | `/api/tables` | Create table |
| POST | `/api/tables/{id}/join` | Join table |
| POST | `/api/tables/{id}/start` | Start game |
| POST | `/api/tables/{id}/action` | Submit action (fold/check/call/raise/all_in) |
| GET | `/api/tables/{id}/valid_actions` | Get valid actions for current player |
| WS | `/ws/{table_id}` | Real-time game updates |

## Docker

```bash
docker-compose up
```

## Game Rules

- 2-10 players per table
- Standard Texas Hold'em rules
- Actions: fold, check, call, raise, all_in
- Hand rankings: High Card → Straight Flush
