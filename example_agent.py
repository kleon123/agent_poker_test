#!/usr/bin/env python3
"""
Example AI Agent Client for Texas Hold'em Poker Platform

This demonstrates how to connect an AI agent to the poker API.
The agent uses a simple strategy: call/check when possible, occasionally raise.

Usage:
    pip install httpx websockets
    python example_agent.py --url http://localhost:8000 --name MyAgent
"""

import argparse
import asyncio
import json
import random
import sys
import time

import httpx
import websockets


class PokerAgent:
    """Simple poker agent that connects to the poker API and plays."""

    def __init__(self, base_url: str, name: str):
        self.base_url = base_url.rstrip("/")
        self.name = name
        self.api_key: str | None = None
        self.agent_id: str | None = None
        self.table_id: str | None = None
        self.game_id: str | None = None
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10)

    async def register(self) -> None:
        """Register agent and get API key."""
        resp = await self.client.post("/api/agents/register", json={"name": self.name})
        resp.raise_for_status()
        data = resp.json()
        self.api_key = data["api_key"]
        self.agent_id = data["id"]
        print(f"[{self.name}] Registered with ID={self.agent_id}, API key={self.api_key}")

    async def find_or_create_table(self) -> None:
        """Find an available table or create one."""
        resp = await self.client.get("/api/tables")
        resp.raise_for_status()
        tables = resp.json()

        # Look for a waiting table
        for table in tables:
            if table["status"] == "waiting" and table["player_count"] < table["max_players"]:
                self.table_id = table["id"]
                print(f"[{self.name}] Found table: {table['name']} ({table['id']})")
                return

        # Create a new table
        resp = await self.client.post(
            "/api/tables",
            json={
                "name": f"{self.name}'s Table",
                "max_players": 4,
                "small_blind": 10,
                "big_blind": 20,
                "starting_chips": 1000,
            },
        )
        resp.raise_for_status()
        table = resp.json()
        self.table_id = table["id"]
        print(f"[{self.name}] Created table: {table['name']} ({table['id']})")

    async def join_table(self) -> None:
        """Join the selected table."""
        resp = await self.client.post(
            f"/api/tables/{self.table_id}/join",
            headers={"X-API-Key": self.api_key},
        )
        resp.raise_for_status()
        print(f"[{self.name}] Joined table {self.table_id}")

    async def start_game_if_ready(self) -> bool:
        """Start the game if there are enough players."""
        resp = await self.client.get(f"/api/tables/{self.table_id}")
        resp.raise_for_status()
        table = resp.json()

        if table["player_count"] >= table["min_players"] and table["status"] == "waiting":
            try:
                resp = await self.client.post(
                    f"/api/tables/{self.table_id}/start",
                    headers={"X-API-Key": self.api_key},
                )
                resp.raise_for_status()
                game_data = resp.json()
                self.game_id = game_data.get("game_id")
                print(f"[{self.name}] Started game {self.game_id}")
                return True
            except httpx.HTTPStatusError as e:
                print(f"[{self.name}] Could not start game: {e.response.text}")
        return False

    def decide_action(self, valid_actions: list) -> tuple[str, int | None]:
        """Simple decision strategy."""
        action_map = {a["action"]: a for a in valid_actions}

        # Priority: check > call > raise (sometimes) > fold
        if "check" in action_map:
            return "check", None

        if "call" in action_map:
            call_info = action_map["call"]
            # Always call if it's less than 20% of our chips
            if call_info["min_amount"] < 200:
                return "call", call_info["min_amount"]

        if "raise" in action_map and random.random() < 0.3:
            raise_info = action_map["raise"]
            amount = raise_info["min_amount"] * 2
            amount = min(amount, raise_info["max_amount"])
            return "raise", amount

        if "bet" in action_map and random.random() < 0.2:
            bet_info = action_map["bet"]
            amount = bet_info["min_amount"] * 2
            return "bet", amount

        if "call" in action_map:
            return "call", action_map["call"]["min_amount"]

        if "fold" in action_map:
            return "fold", None

        if "all_in" in action_map:
            return "all_in", None

        return valid_actions[0]["action"], valid_actions[0].get("min_amount")

    async def play_turn(self) -> None:
        """Check if it's our turn and take action."""
        if not self.game_id:
            return

        try:
            resp = await self.client.get(
                f"/api/games/{self.game_id}/valid-actions",
                headers={"X-API-Key": self.api_key},
            )
            if resp.status_code == 400:
                return  # Not our turn
            resp.raise_for_status()
            data = resp.json()

            if not data.get("is_your_turn"):
                return

            valid_actions = data.get("valid_actions", [])
            if not valid_actions:
                return

            action, amount = self.decide_action(valid_actions)
            print(f"[{self.name}] Taking action: {action}" + (f" {amount}" if amount else ""))

            action_data = {"action": action}
            if amount is not None:
                action_data["amount"] = amount

            resp = await self.client.post(
                f"/api/games/{self.game_id}/action",
                headers={"X-API-Key": self.api_key},
                json=action_data,
            )
            resp.raise_for_status()

        except httpx.HTTPStatusError as e:
            print(f"[{self.name}] Action error: {e.response.status_code} {e.response.text}")
        except Exception as e:
            print(f"[{self.name}] Error: {e}")

    async def watch_game(self) -> None:
        """Connect to WebSocket to watch game events."""
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/observer/{self.table_id}"

        print(f"[{self.name}] Connecting to WebSocket: {ws_url}")

        async with websockets.connect(ws_url) as ws:
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    event = json.loads(msg)
                    event_type = event.get("type")

                    if event_type == "game_state":
                        state = event["data"]
                        phase = state.get("phase", "?")
                        pot = state.get("pot", 0)
                        current_player = state.get("current_player_id")
                        if not self.game_id:
                            self.game_id = state.get("game_id")
                        print(f"[{self.name}] Phase={phase} Pot={pot} Current={current_player}")

                    elif event_type == "action":
                        data = event["data"]
                        player_name = data.get("player", {}).get("name", "?")
                        action = data.get("action", "?")
                        amount = data.get("amount", "")
                        print(f"[{self.name}] Action: {player_name} -> {action} {amount or ''}")

                    elif event_type == "hand_result":
                        data = event["data"]
                        winners = [w.get("name", "?") for w in data.get("winners", [])]
                        pot = data.get("pot", 0)
                        print(f"[{self.name}] Hand result: Winners={winners}, Pot={pot}")

                    elif event_type == "phase_change":
                        data = event["data"]
                        print(f"[{self.name}] Phase change: {data.get('phase')}")

                except asyncio.TimeoutError:
                    # Check if it's our turn
                    await self.play_turn()
                except websockets.ConnectionClosed:
                    print(f"[{self.name}] WebSocket disconnected")
                    break

    async def run(self) -> None:
        """Main agent loop."""
        await self.register()
        await self.find_or_create_table()
        await self.join_table()

        # Wait a moment for other agents to join, then try to start
        await asyncio.sleep(2)
        started = await self.start_game_if_ready()

        if not started:
            print(f"[{self.name}] Waiting for more players to join...")
            # Wait up to 30 seconds for game to start
            for _ in range(30):
                resp = await self.client.get(f"/api/tables/{self.table_id}")
                table = resp.json()
                if table["status"] == "playing":
                    # Get current game
                    resp = await self.client.get(f"/api/games/history")
                    break
                await self.start_game_if_ready()
                await asyncio.sleep(1)

        await self.watch_game()
        await self.client.aclose()


async def run_multiple_agents(base_url: str, count: int) -> None:
    """Run multiple agents simultaneously for testing."""
    agents = [PokerAgent(base_url, f"Agent_{i+1}") for i in range(count)]
    tasks = [asyncio.create_task(agent.run()) for agent in agents]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("Stopping agents...")
        for task in tasks:
            task.cancel()


def main():
    parser = argparse.ArgumentParser(description="Poker AI Agent")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--name", default="TestAgent", help="Agent name")
    parser.add_argument("--count", type=int, default=1, help="Number of agents to run")
    args = parser.parse_args()

    print(f"Starting {args.count} agent(s) against {args.url}")

    if args.count > 1:
        asyncio.run(run_multiple_agents(args.url, args.count))
    else:
        agent = PokerAgent(args.url, args.name)
        asyncio.run(agent.run())


if __name__ == "__main__":
    main()
