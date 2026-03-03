import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.models.database import create_tables
from backend.api.routes import router
from backend.api.websocket_manager import manager
from backend.game.game_engine import get_table


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="Texas Hold'em Poker Platform",
    description="A complete Texas Hold'em poker platform with REST API and WebSocket support.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "poker-platform"}


@app.websocket("/ws/{table_id}")
async def websocket_endpoint(websocket: WebSocket, table_id: str):
    await manager.connect(table_id, websocket)
    table = get_table(table_id)
    if table:
        await manager.send_personal(websocket, {
            "type": "connected",
            "table_id": table_id,
            "game_state": table.to_dict(),
        })
    else:
        await manager.send_personal(websocket, {
            "type": "connected",
            "table_id": table_id,
            "game_state": None,
        })
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back any pings
            if data == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(table_id, websocket)


# Serve frontend build if available
frontend_build = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
if os.path.isdir(frontend_build):
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="frontend")
