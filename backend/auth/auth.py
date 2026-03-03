import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.models import Agent

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    return secrets.token_hex(32)


def hash_api_key(key: str) -> str:
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()


async def get_current_agent(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    db: Optional[AsyncSession] = None,
) -> Agent:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header.",
        )
    hashed = hash_api_key(api_key)
    result = await db.execute(select(Agent).where(Agent.api_key == hashed))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    return agent


def make_get_current_agent(db: AsyncSession):
    """Factory that returns a get_current_agent coroutine bound to a db session."""
    async def _get(api_key: Optional[str] = Security(API_KEY_HEADER)) -> Agent:
        return await get_current_agent(api_key=api_key, db=db)
    return _get
