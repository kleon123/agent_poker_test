#!/usr/bin/env python3
"""
Example poker agent that connects to the Texas Hold'em Poker Platform.
This agent registers, joins a table, and plays using a simple strategy.

Usage:
    # Start the server first:
    uvicorn backend.main:app --reload

    # Then run this agent:
    python example_agent.py --server http://localhost:8000 --name "MyBot"
"""

import asyncio
import json
import random
import argparse
import httpx
import websockets


class PokerAgent:
    def __init__(self, server_url: str, name: str):
        self.server_url = server_url.rstrip("/")
        self.name = name
        self.api_key: str = ""
        self.agent_id: int = 0
        self.table_id: str = ""

    # ── Registration & Auth ────────────────────────────────────────────────────

    async def register(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(f"{self.server_url}/api/agents/register", json={"name": self.name})
        if resp.status_code == 201:
            data = resp.json()
            self.api_key = data["api_key"]
            self.agent_id = data["id"]
            print(f"[{self.name}] Registered! Agent ID: {self.agent_id}, API Key: {self.api_key[:8]}...")
        elif resp.status_code == 400 and "already taken" in resp.text:
            print(f"[{self.name}] Name taken. Try a different name.")
            raise SystemExit(1)
        else:
            print(f"[{self.name}] Registration failed: {resp.text}")
            raise SystemExit(1)

    def headers(self) -> dict:
        return {"X-API-Key": self.api_key}

    # ── Table management ───────────────────────────────────────────────────────

    async def find_or_create_table(self, client: httpx.AsyncClient) -> str:
        # Look for an existing table
        resp = await client.get(f"{self.server_url}/api/tables")
        tables = resp.json()
        for table in tables:
            if table["player_count"] < table["max_players"] and table["status"] in ("waiting", "finished"):
                self.table_id = table["id"]
                print(f"[{self.name}] Joining existing table: {table['name']}")
                return self.table_id

        # Create a new table
        resp = await client.post(
            f"{self.server_url}/api/tables",
            json={"name": f"{self.name}'s Table", "max_players": 4, "small_blind": 10, "big_blind": 20},
            headers=self.headers(),
        )
        data = resp.json()
        self.table_id = data["id"]
        print(f"[{self.name}] Created table: {data['name']}")
        return self.table_id

    async def join_table(self, client: httpx.AsyncClient) -> int:
        resp = await client.post(
            f"{self.server_url}/api/tables/{self.table_id}/join",
            json={"chips": 1000},
            headers=self.headers(),
        )
        data = resp.json()
        print(f"[{self.name}] Joined at seat {data['seat']}")
        return data["seat"]

    # ── Strategy ───────────────────────────────────────────────────────────────

    def decide_action(self, game_state: dict) -> tuple[str, int]:
        """
        Simple strategy:
        - 70% chance to call/check
        - 20% chance to raise (by min raise)
        - 10% chance to fold (unless checking is free)
        """
        my_id = str(self.agent_id)
        players = game_state.get("players", {})
        me = players.get(my_id)
        if not me:
            return "fold", 0

        call_amount = 0
        for action in game_state.get("valid_actions", []):
            if action["action"] == "call":
                call_amount = action["amount"]

        roll = random.random()
        if call_amount == 0:
            # Free check or raise
            if roll < 0.3:
                return "raise", game_state.get("min_raise", 20)
            return "check", 0
        else:
            if roll < 0.1:
                return "fold", 0
            elif roll < 0.8:
                return "call", call_amount
            else:
                return "raise", game_state.get("min_raise", 20)

    # ── WebSocket game loop ────────────────────────────────────────────────────

    async def play(self, client: httpx.AsyncClient):
        ws_url = self.server_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/{self.table_id}"

        print(f"[{self.name}] Connecting to WebSocket: {ws_url}")
        async with websockets.connect(ws_url) as ws:
            # Try to start a game
            start_resp = await client.post(
                f"{self.server_url}/api/tables/{self.table_id}/start",
                headers=self.headers(),
            )
            if start_resp.status_code == 200:
                print(f"[{self.name}] Started game!")

            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(message)
                    event_type = data.get("type", "")

                    if event_type == "pong":
                        continue

                    game_state = data.get("game_state", {})
                    if not game_state:
                        continue

                    state = game_state.get("state", "")
                    current_player = game_state.get("current_player_id")

                    print(f"[{self.name}] Event: {event_type}, State: {state}, Current: {current_player}")

                    if state == "finished":
                        winners = game_state.get("winners", [])
                        for w in winners:
                            print(f"[{self.name}] Winner: {w['name']} wins {w['amount']} with {w['hand']}")
                        # Wait and try to start next hand
                        await asyncio.sleep(2)
                        start_resp = await client.post(
                            f"{self.server_url}/api/tables/{self.table_id}/start",
                            headers=self.headers(),
                        )
                        if start_resp.status_code != 200:
                            print(f"[{self.name}] Could not start next hand: {start_resp.text}")

                    elif current_player == str(self.agent_id) and state not in ("waiting", "finished", "showdown"):
                        # Get valid actions
                        valid_resp = await client.get(
                            f"{self.server_url}/api/tables/{self.table_id}/valid_actions",
                            headers=self.headers(),
                        )
                        valid_data = valid_resp.json()
                        game_state["valid_actions"] = valid_data.get("valid_actions", [])

                        action, amount = self.decide_action(game_state)
                        print(f"[{self.name}] Acting: {action} {amount}")

                        act_resp = await client.post(
                            f"{self.server_url}/api/tables/{self.table_id}/action",
                            json={"action": action, "amount": amount},
                            headers=self.headers(),
                        )
                        if act_resp.status_code != 200:
                            print(f"[{self.name}] Action failed: {act_resp.text}")

                except asyncio.TimeoutError:
                    # Send ping to keep alive
                    await ws.send("ping")
                except websockets.ConnectionClosed:
                    print(f"[{self.name}] WebSocket closed")
                    break

    # ── Main entry ─────────────────────────────────────────────────────────────

    async def run(self):
        async with httpx.AsyncClient(timeout=10) as client:
            # Health check
            try:
                resp = await client.get(f"{self.server_url}/health")
                print(f"[{self.name}] Server health: {resp.json()}")
            except Exception as e:
                print(f"[{self.name}] Cannot reach server: {e}")
                return

            await self.register(client)
            await self.find_or_create_table(client)
            await self.join_table(client)
            await self.play(client)


async def main():
    parser = argparse.ArgumentParser(description="Example Poker Agent")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--name", default=f"Agent_{random.randint(1000, 9999)}", help="Agent name")
    args = parser.parse_args()

    agent = PokerAgent(server_url=args.server, name=args.name)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
