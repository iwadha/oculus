# app/api/v1/deps.py
from typing import AsyncGenerator
from fastapi import Request
from asyncpg import Pool

async def get_db(request: Request) -> Pool:
    """
    Return the global asyncpg Pool stored on app.state.db.
    Main app must create it on startup.
    """
    db: Pool = request.app.state.db  # type: ignore[attr-defined]
    return db
