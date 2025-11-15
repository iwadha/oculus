from fastapi import APIRouter, Depends, Query
from asyncpg import Pool
from app.api.v1.deps import get_db

router = APIRouter(prefix="/v1/trades", tags=["trades"])

@router.get("")
async def list_trades(
    db: Pool = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    offset = (page - 1) * page_size
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
              id,
              wallet_owned_id  AS wallet_id,
              wallet_target_id AS creator_id,
              invested_sol     AS amount,
              received_qty     AS price,
              token_mint       AS mint,
              created_at       AS timestamp
            FROM trades_ledger
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            page_size, offset,
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM trades_ledger")
    return {
        "items": [dict(r) for r in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }

