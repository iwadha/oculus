# backend/app/workers/copy_slot_backfill_worker.py

import os
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import asyncpg
import httpx

from app.core.config import settings

log = logging.getLogger("copy_slot_backfill")

# Basic logging config (respects LOG_LEVEL from settings where possible)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

DB_DSN = os.getenv("DATABASE_URL")
HELIUS_RPC_URL: str = os.getenv("HELIUS_RPC_URL", "")

# Tunables
BATCH_SIZE = int(os.getenv("COPY_BACKFILL_BATCH_SIZE", "50"))
IDLE_SLEEP_SECONDS = float(os.getenv("COPY_BACKFILL_SLEEP_SECONDS", "10.0"))


async def fetch_needing_backfill(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    """
    Find copy trades that:
      - belong to an ACTIVE copy wallet
      - have a non-null tx_signature
      - do NOT yet have a row in trades_transactions
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            select
              tl.id          as copy_id,
              tl.tx_signature as tx_signature
            from trades_ledger tl
            join copy_wallets cw
              on cw.id = tl.wallet_owned_id
            where cw.status = 'ACTIVE'
              and tl.tx_signature is not null
              and not exists (
                select 1
                from trades_transactions tx
                where tx.tx_signature = tl.tx_signature
              )
            order by tl.id
            limit $1
            """,
            BATCH_SIZE,
        )
    return rows


async def fetch_tx_via_rpc(
    sig: str,
    client: httpx.AsyncClient,
) -> Optional[dict]:
    """
    Call Helius RPC getTransaction for a given signature.
    We only need slot + blockTime (and we keep the full JSON as raw).
    """
    if not HELIUS_RPC_URL:
        log.error("[COPY_SLOT] HELIUS_RPC_URL is not set; cannot fetch transactions.")
        return None

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            sig,
            {
                "encoding": "json",
                # This is safe even if you're on v0-only txs
                "maxSupportedTransactionVersion": 0,
            },
        ],
    }

    try:
        resp = await client.post(HELIUS_RPC_URL, json=payload, timeout=20.0)
        resp.raise_for_status()
    except Exception as e:
        log.warning("[COPY_SLOT] RPC HTTP error for sig=%s: %r", sig, e)
        return None

    data = resp.json()
    result = data.get("result")
    if not result:
        log.warning("[COPY_SLOT] getTransaction returned no result for sig=%s raw=%s", sig, data)
        return None

    return result


async def process_batch(pool: asyncpg.Pool) -> int:
    """
    Process one batch of copy trades that need chain enrichment.
    Returns number of rows scanned in this batch.
    """
    rows = await fetch_needing_backfill(pool)
    if not rows:
        log.info("[COPY_SLOT] No more copy trades needing backfill.")
        return 0

    async with httpx.AsyncClient() as client:
        enriched = 0

        for row in rows:
            copy_id: int = row["copy_id"]
            sig: str = row["tx_signature"]

            if not sig:
                log.info("[COPY_SLOT] Skip copy_id=%s: tx_signature is NULL.", copy_id)
                continue

            tx = await fetch_tx_via_rpc(sig, client)
            if not tx:
                log.info("[COPY_SLOT] Skip copy_id=%s: getTransaction returned no data.", copy_id)
                continue

            slot = tx.get("slot")
            block_time = tx.get("blockTime")
            block_ts = (
                datetime.fromtimestamp(block_time, tz=timezone.utc)
                if block_time
                else None
            )

            meta = tx.get("meta") or {}
            cu_used = meta.get("computeUnitsConsumed")
            # You can extend this later if you want to pull priority/tips.
            priority_fee_lamports = None
            tip_lamports = None

            raw_json = json.dumps(tx)

            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    insert into trades_transactions (
                        tx_signature,
                        slot,
                        block_time,
                        priority_fee_lamports,
                        cu_used,
                        tip_lamports,
                        raw
                    )
                    values ($1, $2, $3, $4, $5, $6, $7)
                    on conflict (tx_signature) do update
                    set slot                   = excluded.slot,
                        block_time             = excluded.block_time,
                        priority_fee_lamports  = coalesce(
                            excluded.priority_fee_lamports,
                            trades_transactions.priority_fee_lamports
                        ),
                        cu_used                = coalesce(
                            excluded.cu_used,
                            trades_transactions.cu_used
                        ),
                        tip_lamports           = coalesce(
                            excluded.tip_lamports,
                            trades_transactions.tip_lamports
                        ),
                        raw                    = excluded.raw
                    """,
                    sig,
                    slot,
                    block_ts,
                    priority_fee_lamports,
                    cu_used,
                    tip_lamports,
                    raw_json,
                )

            enriched += 1
            log.info(
                "[COPY_SLOT] Enriched copy_id=%s sig=%s slot=%s",
                copy_id,
                sig,
                slot,
            )

    log.info(
        "[COPY_SLOT] Batch complete. rows=%s enriched=%s",
        len(rows),
        enriched,
    )
    return len(rows)


async def main() -> None:
    if not DB_DSN:
        raise RuntimeError("DATABASE_URL not set in environment.")

    log.info("[COPY_SLOT] Connecting to database...")
    pool = await asyncpg.create_pool(
        DB_DSN,
        statement_cache_size=0,
        max_inactive_connection_lifetime=60.0,
    )
    log.info("[COPY_SLOT] Pool created; starting backfill loop (batch_size=%s).", BATCH_SIZE)

    try:
        while True:
            processed = await process_batch(pool)
            # If nothing to do, sleep a bit longer
            if processed == 0:
                await asyncio.sleep(IDLE_SLEEP_SECONDS)
            else:
                await asyncio.sleep(1.0)
    finally:
        await pool.close()
        log.info("[COPY_SLOT] Pool closed, shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
