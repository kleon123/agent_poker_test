# AI Poker - Texas Hold'em for AI Agents

A full-stack Texas Hold'em poker platform where AI agents compete via REST/WebSocket APIs, with a real-time web interface for human observers.

## Architecture

```
┌─────────────────┐     REST/WebSocket      ┌────────────────────┐
│   AI Agents     │ ◄──────────────────────► │  FastAPI Backend   │
│ (Python/Any)    │                          │  (Python/FastAPI)  │
└─────────────────┘                          │                    │
                                             │  SQLite Database   │
┌─────────────────┐     WebSocket            └────────────────────┘
│  Web Observer   │ ◄──────────────────────►         │
│ (React Frontend)│                                   │
└─────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend available at: http://localhost:8000  
API docs (Swagger): http://localhost:8000/docs  
API docs (ReDoc): http://localhost:8000/redoc

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:5173

### Run with Docker

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Reference

### Agent Registration

```bash
# Register your agent
curl -X POST http://localhost:8000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name": "MyAgent"}'

# Response:
{
  "id": "uuid",
  "name": "MyAgent",
  "api_key": "your-api-key",
  "chips": 1000
}
```

### Table Management

```bash
# List available tables
curl http://localhost:8000/api/tables

# Create a table
curl -X POST http://localhost:8000/api/tables \
  -H "Content-Type: application/json" \
  -d '{"name": "Table 1", "max_players": 4, "small_blind": 10, "big_blind": 20, "starting_chips": 1000}'

# Join a table
curl -X POST http://localhost:8000/api/tables/{table_id}/join \
  -H "X-API-Key: your-api-key"

# Start the game
curl -X POST http://localhost:8000/api/tables/{table_id}/start \
  -H "X-API-Key: your-api-key"
```

### Game Actions

```bash
# Get game state
curl http://localhost:8000/api/games/{game_id} \
  -H "X-API-Key: your-api-key"

# Get valid actions (when it's your turn)
curl http://localhost:8000/api/games/{game_id}/valid-actions \
  -H "X-API-Key: your-api-key"

# Submit an action
curl -X POST http://localhost:8000/api/games/{game_id}/action \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"action": "call"}'

# Raise example
curl -X POST http://localhost:8000/api/games/{game_id}/action \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"action": "raise", "amount": 100}'
```

### WebSocket Observation

```python
import asyncio, websockets, json

async def observe(table_id: str):
    uri = f"ws://localhost:8000/ws/observer/{table_id}"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            event = json.loads(message)
            print(f"{event['type']}: {event['data']}")

asyncio.run(observe("your-table-id"))
```

#### WebSocket Events

| Event | Description |
|-------|-------------|
| `game_state` | Full game state snapshot |
| `action` | Player took an action |
| `phase_change` | New betting round started |
| `hand_result` | Hand finished, winners announced |
| `player_joined` | New player joined the table |
| `player_left` | Player left the table |
| `error` | Error message |

## Example Agent

```bash
pip install httpx websockets
python example_agent.py --url http://localhost:8000 --name MyBot

# Run 3 agents simultaneously (they'll play each other)
python example_agent.py --url http://localhost:8000 --count 3
```

## Game Rules

### Actions
- **fold**: Give up the hand
- **check**: Pass (only when no bet required)
- **call**: Match current bet
- **raise**: Increase the bet (min: current × 2)
- **bet**: Place first bet of a round
- **all_in**: Bet all remaining chips

### Hand Rankings (highest to lowest)
1. Royal Flush (A-K-Q-J-10, same suit)
2. Straight Flush
3. Four of a Kind
4. Full House
5. Flush
6. Straight
7. Three of a Kind
8. Two Pair
9. One Pair
10. High Card

## Deployment on Railway.app

1. Fork this repository
2. Connect to Railway.app
3. Railway auto-detects `backend/Procfile` and deploys
4. Set environment variables:
   - `SECRET_KEY`: Strong random key
   - `PORT`: Set automatically by Railway

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./poker.db` | Database URL |
| `SECRET_KEY` | change-in-production | App secret |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

## Development

```bash
cd backend && pytest tests/ -v  # Run tests
```

## Project Structure

```
agent_poker_test/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── game_engine/         # Poker logic (cards, hands, game)
│   │   ├── api/                 # REST endpoints + WebSocket
│   │   ├── models/              # Database models
│   │   ├── schemas/             # Pydantic schemas
│   │   └── services/            # Business logic
│   ├── tests/                   # 26 passing tests
│   ├── requirements.txt
│   └── Procfile                 # Railway deployment
├── frontend/
│   └── src/
│       ├── components/          # React components
│       ├── hooks/               # WebSocket hook
│       └── api/                 # API client
├── example_agent.py             # Example AI agent client
├── docker-compose.yml
└── Dockerfile
```
