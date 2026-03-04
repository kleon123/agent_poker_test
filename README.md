# Agent Poker Test

## Overview
The Agent Poker Test is an experimental project designed to test various AI agents in a poker environment. This project aims to provide insights into agent behavior, performance metrics, and strategies utilized during poker games.

## How Agents Work
Agents in this project are implemented using reinforcement learning techniques. Each agent learns from its environment by making decisions based on the current state of the game, updating its strategy based on the rewards received from previous actions.

## Running Locally
To run the project locally, follow these steps:
1. **Clone the repository:**
   ```bash
   git clone https://github.com/kleon123/agent_poker_test.git
   cd agent_poker_test
   ```
2. **Install dependencies:**
   Make sure you have Python 3.8 or above. Then install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   Execute the following command to start the game:
   ```bash
   python main.py
   ```

## Running Live
To run the project live:
1. **Deploy:** Use a cloud service provider to deploy the application. 
2. **Configure settings:** Ensure that you configure the server environment properly, including any environment variables required for API access and agent settings.
3. **Start the server:** Make sure your server is running and accessible over the internet.

## API Documentation
### Endpoints
#### GET /api/agents
- **Description:** Retrieve a list of all agents.
- **Response:** A JSON array of agent objects.

#### POST /api/agents
- **Description:** Add a new agent to the system.
- **Payload:** Include agent configuration details in JSON format.
- **Response:** Confirmation of the agent creation including its ID.

#### GET /api/games
- **Description:** Fetch the current game state.
- **Response:** A JSON object representing the state of the ongoing game.

#### POST /api/games
- **Description:** Start a new poker game.
- **Payload:** Include parameters for the game setup in JSON format.
- **Response:** Details of the newly created game session.

### Error Handling
All API responses will include a status code and a message, along with additional error details for any failures.