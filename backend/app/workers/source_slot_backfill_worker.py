# backend/app/workers/source_slot_backfill_worker.py

import os
import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Optional

import asyncpg
import httpx

from app.core.config import settings

log = logging.getLogger("source_slot_backfill")

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

DB_DSN = os.getenv("DATABASE_URL")
HELIUS_RPC_URL: str = settings.HELIUS_RPC_URL

BATCH_SIZE = int(os.getenv("SOURCE_BACKFILL_BATCH_SIZE", "50"))
IDLE_SLEEP_SECONDS = float(os.getenv("SOURCE_BACKFILL_SLEEP_SECONDS", "10.0"))


async def fetch_tx_via_rpc(sig: str, client: httpx.AsyncClient) -> Optional[dict]:
    """
    Same RPC helper as in copy_slot_backfill, shared logic.
    """
    if not HELIUS_RPC_URL:
        log.error("[SOURCE_SLOT] HELIUS_RPC_URL is not set; cannot fetch transactions.")
        return None

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            sig,
            {
                "encoding": "json",
                "maxSupportedTransactionVersion": 0,
            },
        ],
    }

    try:
        resp = await client.post(HELIUS_RPC_URL, json=payload, timeout=20.0)
        resp.raise_for_status()
    except Exception as e:
        log.warning("[SOURCE_SLOT] RPC HTTP error for sig=%s: %r", sig, e)
        return None

    data = resp.json()
    result = data.get("result")
    if not result:
        log.warning("[SOURCE_SLOT] getTransaction returned no result for sig=%s raw=%s", sig, data)
        return None

    return result


async def fetch_needing_backfill(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    """
    Find source_trades that:
      - are actually referenced by trade_pairs (so they're real "creators" we care about)
      - have a non-null tx_signature
      - have event_slot NULL or 0 (placeholder)
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            select
              st.id          as source_id,
              st.tx_signature as tx_signature
            from source_trades st
            join trade_pairs tp
              on tp.source_trade_id = st.id
            where st.tx_signature is not null
              and (st.event_slot is null or st.event_slot = 0)
            order by st.event_ts
            limit $1
            """,
            BATCH_SIZE,
        )
    return rows


async def process_batch(pool: asyncpg.Pool) -> int:
    rows = await fetch_needing_backfill(pool)
    if not rows:
        log.info("[SOURCE_SLOT] No more source trades needing backfill.")
        return 0

    async with httpx.AsyncClient() as client:
        updated = 0

        for row in rows:
            source_id = row["source_id"]
            sig = row["tx_signature"]

            if not sig:
                log.info("[SOURCE_SLOT] Skip source_id=%s: tx_signature is NULL.", source_id)
                continue

            tx = await fetch_tx_via_rpc(sig, client)
            if not tx:
                log.info("[SOURCE_SLOT] Skip source_id=%s: getTransaction returned no data.", source_id)
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
            raw_json = json.dumps(tx)

            async with pool.acquire() as conn:
                # 1) Update the source_trades event_slot / event_ts
                await conn.execute(
                    """
                    update source_trades
                    set event_slot = coalesce(nullif(event_slot, 0), $2),
                        event_ts   = coalesce(event_ts, $3)
                    where id = $1
                    """,
                    source_id,
                    slot,
                    block_ts,
                )

                # 2) Optionally, also mirror into trades_transactions for that signature
                await conn.execute(
                    """
                    insert into trades_transactions (
                        tx_signature,
                        slot,
                        block_time,
                        cu_used,
                        raw
                    )
                    values ($1, $2, $3, $4, $5)
                    on conflict (tx_signature) do update
                    set slot       = excluded.slot,
                        block_time = excluded.block_time,
                        cu_used    = coalesce(excluded.cu_used, trades_transactions.cu_used),
                        raw        = excluded.raw
                    """,
                    sig,
                    slot,
                    block_ts,
                    cu_used,
                    raw_json,
                )

            updated += 1
            log.info(
                "[SOURCE_SLOT] Updated source_id=%s sig=%s slot=%s",
                source_id,
                sig,
                slot,
            )

    log.info(
        "[SOURCE_SLOT] Batch complete. rows=%s updated=%s",
        len(rows),
        updated,
    )
    return len(rows)


async def main() -> None:
    if not DB_DSN:
        raise RuntimeError("DATABASE_URL not set in environment.")

    log.info("[SOURCE_SLOT] Connecting to database...")
    pool = await asyncpg.create_pool(
        DB_DSN,
        statement_cache_size=0,
        max_inactive_connection_lifetime=60.0,
    )
    log.info(
        "[SOURCE_SLOT] Pool created; starting backfill loop (batch_size=%s).",
        BATCH_SIZE,
    )

    try:
        while True:
            processed = await process_batch(pool)
            if processed == 0:
                await asyncio.sleep(IDLE_SLEEP_SECONDS)
            else:
                await asyncio.sleep(1.0)
    finally:
        await pool.close()
        log.info("[SOURCE_SLOT] Pool closed, shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
