# README

## Overview
This project is designed to simulate a poker game environment where various agents can compete against each other. The framework allows for both local and live game settings and provides an API for interacting with agents and game mechanics.

## How It Works
Agents are programmed to make decisions based on game state and their own strategies. They interact with the game environment to place bets, call, and fold based on their evaluation of the situation. The game engine facilitates the turn-based gameplay and enforces the rules of poker.

## Quick Start
### Local
1. Clone the repository: `git clone https://github.com/kleon123/agent_poker_test.git`
2. Navigate into the project folder: `cd agent_poker_test`
3. Install the dependencies: `pip install -r requirements.txt`
4. Run the local game: `python run_game.py`

### Live
To set up a live game, configure your server settings in `config.json`, then deploy it to your cloud provider of choice and run `python live_game.py`.

## API Reference
- **GET /api/games**: Retrieve the current state of all games.
- **POST /api/agents**: Register a new agent for the next game.
- **PATCH /api/games/{id}/action**: Submit an action (bet, call, fold) for a specific game.

## Running Agents
To run your own agent, implement the `Agent` class and define your strategy in `agent.py`. Ensure your new agent is registered with the game engine before the game starts.

## Game Rules
- Each game follows standard Texas Hold'em rules.
- Players are dealt two private cards and share five community cards.
- The objective is to make the best five-card poker hand.
- Betting rounds take place after the deal and after community cards are revealed.

## Deployment Instructions
1. Set your environment variables for game settings and agent behavior.
2. Use CI/CD pipelines for automated deployment strategies. 
3. Monitor performance and adapt agent strategies as needed.