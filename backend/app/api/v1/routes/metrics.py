"""
System Metrics Endpoint
-----------------------
Provides high-level operational metrics and data freshness indicators
for Oculus backend.
"""

from fastapi import APIRouter, Depends
from asyncpg import Pool
from datetime import datetime, timedelta
from app.api.v1.deps import get_db

router = APIRouter(prefix="/v1/system", tags=["system"])

@router.get("/metrics")
async def get_system_metrics(db: Pool = Depends(get_db)):
    """
    Returns system-wide stats:
      - trades_today
      - unique_wallets
      - unscored_pairs
      - active_creators
      - pending_alerts
      - token_count
      - last_trade_ts
    """
    now = datetime.utcnow()
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    async with db.acquire() as conn:
        # --- Trades ---
        trades_today = await conn.fetchval(
            "SELECT COUNT(*) FROM trades_ledger WHERE timestamp >= $1;", since_24h
        )
        unique_wallets = await conn.fetchval(
            "SELECT COUNT(DISTINCT wallet_owned_id) FROM trades_ledger WHERE timestamp >= $1;", since_24h
        )
        last_trade_ts = await conn.fetchval(
            "SELECT MAX(timestamp) FROM trades_ledger;"
        )

        # --- Pairing / Scoring ---
        unscored_pairs = await conn.fetchval(
            "SELECT COUNT(*) FROM trade_pairs WHERE execution_score IS NULL;"
        )

        # --- Creator activity ---
        active_creators = await conn.fetchval(
            "SELECT COUNT(DISTINCT wallet_target_id) FROM trades_ledger WHERE timestamp >= $1;",
            since_7d
        )

        # --- Alerts ---
        pending_alerts = await conn.fetchval(
            "SELECT COUNT(*) FROM alerts WHERE resolved IS FALSE OR resolved IS NULL;"
        )

        # --- Token metadata ---
        token_count = await conn.fetchval("SELECT COUNT(*) FROM tokens;")

    return {
        "timestamp": now.isoformat() + "Z",
        "trades_today": trades_today or 0,
        "unique_wallets": unique_wallets or 0,
        "unscored_pairs": unscored_pairs or 0,
        "active_creators": active_creators or 0,
        "pending_alerts": pending_alerts or 0,
        "token_count": token_count or 0,
        "last_trade_ts": last_trade_ts.isoformat() + "Z" if last_trade_ts else None,
    }
