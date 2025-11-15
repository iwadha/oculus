# backend/app/api/v1/routes/wallet_ops.py
from typing import Optional, Literal, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from asyncpg import Pool

from app.api.v1.deps import get_db

AllowedState = Literal["ACTIVE", "BUY_ONLY", "SELL_ONLY", "PAUSED", "REMOVED"]

# Add a prefix so final paths are /v1/wallets/...
router = APIRouter(prefix="/v1/wallets", tags=["wallet_ops"])

class UpdateWalletStateBody(BaseModel):
    state: AllowedState
    reason: Optional[str] = "Manual update"


@router.get("/ops")
async def get_wallet_ops(db: Pool = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns health rows from the view vw_copy_wallet_health
    """
    async with db.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM vw_copy_wallet_health ORDER BY label;"
        )
        return [dict(r) for r in rows]


@router.post("/{wallet_id}/state")
async def update_wallet_state(
    wallet_id: str,
    body: UpdateWalletStateBody = Body(...),
    db: Pool = Depends(get_db),
):
    """
    Update copy_wallets.status and write an audit row to wallet_action_log.
    Accepts JSON body: {"state": "<AllowedState>", "reason": "Manual update"}.
    """
    new_state = body.state
    reason = body.reason

    async with db.acquire() as conn:
        cur = await conn.fetchrow(
            "SELECT status FROM copy_wallets WHERE id = $1;",
            wallet_id,
        )
        if not cur:
            raise HTTPException(status_code=404, detail="Wallet not found")

        old_state = cur["status"]

        # No-op short-circuit
        if old_state == new_state:
            return {"old_state": old_state, "new_state": new_state, "note": "no change"}

        # Update state
        await conn.execute(
            "UPDATE copy_wallets SET status = $1 WHERE id = $2;",
            new_state,
            wallet_id,
        )

        # Audit log
        await conn.execute(
            """
            INSERT INTO wallet_action_log (wallet_id, old_state, new_state, reason)
            VALUES ($1, $2, $3, $4);
            """,
            wallet_id, old_state, new_state, reason,
        )

    return {"old_state": old_state, "new_state": new_state}
