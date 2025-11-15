import os
from typing import Optional, List, Dict, Any
from asyncpg import Pool
from ..utils.helius_client import HeliusClient
from ..utils.db_helpers import fetch_all, upsert_one, update_heartbeat

PAIR_BATCH = int(os.getenv("NORMALIZER_COPY_BATCH", "300"))

COPY_RAW_QUERY = """
select id, tx_signature, copy_wallet_pubkey, source_wallet_pubkey, token_mint, side,
       received_qty, invested_sol, ts_iso, raw_json
from trades_ledger_raw
where processed_at is null
order by id
limit $1
"""

MARK_COPY_RAW_DONE = "update trades_ledger_raw set processed_at = now() where id = $1"

UPSERT_TRADES_TX = """
insert into trades_transactions (tx_signature, slot, block_time)
values ($1, $2, $3)
on conflict (tx_signature) do update set slot = excluded.slot, block_time = excluded.block_time
returning tx_signature
"""

UPSERT_TRADES_LEDGER = """
insert into trades_ledger (
  -- keep your existing column set; we avoid tx_signature because it's often empty
  wallet_target_id,                -- creator pubkey if known
  token_mint,
  side,
  received_qty,
  invested_sol,
  timestamp
)
values ($1, $2, $3, $4, $5, $6)
returning id
"""

class NormalizerCopy:
    def __init__(self, db: Pool, helius: Optional[HeliusClient] = None):
        self.db = db
        self.helius = helius or HeliusClient()

    async def _normalize_row(self, row) -> None:
        # tx_signature may be empty in your CSV; we still try to fetch Helius if present
        sig = row["tx_signature"]
        slot = None
        block_time = None
        if sig:
            tx = self.helius.tx_by_signature(sig)
            if tx:
                slot = tx.get("slot")
                block_time = tx.get("blockTime")

                # Persist tx linkage
                await upsert_one(self.db, UPSERT_TRADES_TX, (sig, slot, block_time))

        # Insert canonical copy trade (we do not depend on tx_signature here)
        # Using creator hint if present (source_wallet_pubkey) into wallet_target_id
        await upsert_one(
            self.db,
            UPSERT_TRADES_LEDGER,
            (
                row["source_wallet_pubkey"],        # wallet_target_id (creator pubkey)
                row["token_mint"],
                row["side"],
                row["received_qty"],
                row["invested_sol"],
                row["ts_iso"],
            ),
        )

        # Mark raw processed
        await self.db.execute(MARK_COPY_RAW_DONE, row["id"])

    async def run_once(self) -> int:
        rows = await fetch_all(self.db, COPY_RAW_QUERY, PAIR_BATCH)
        for r in rows:
            await self._normalize_row(r)
        await update_heartbeat(self.db, "normalizer_copy", len(rows))
        return len(rows)
