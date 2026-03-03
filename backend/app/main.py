from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import tables, games, players, websocket
from app.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="Poker API",
    description="Texas Hold'em for AI Agents",
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

app.include_router(players.router, prefix="/api")
app.include_router(tables.router, prefix="/api")
app.include_router(games.router, prefix="/api")
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {"message": "Poker API is running", "docs": "/docs"}
