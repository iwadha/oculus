# backend/app/workers/pairing_worker.py
import os
import json
from typing import Optional, Dict, Any

from asyncpg import Pool
from ..utils.db_helpers import fetch_all, fetch_one, upsert_one, update_heartbeat

BATCH = int(os.getenv("PAIRING_BATCH_SIZE", "300"))
RPC_FALLBACK = os.getenv("PAIRING_USE_DB_RPC_FALLBACK", "true").lower() == "true"

# 1) Find copy trades that do NOT yet have a row in trade_pairs
UNPAIRED = """
select
  t.id          as copy_id,
  t.token_mint  as token_mint,
  t.side        as side,
  tr.slot       as copy_slot,
  tr.block_time as copy_block_time
from trades_ledger t
left join trade_pairs p
  on p.copy_trade_id = t.id
left join trades_transactions tr
  on tr.tx_signature = t.tx_signature
where p.copy_trade_id is null
order by t.id
limit $1
"""

# 2) Find the closest source_trade by mint + side + slot distance
FIND_SOURCE_FOR_COPY = """
select
  st.id   as source_id,
  st.event_ts,
  tr.slot as source_slot
from source_trades st
left join trades_transactions tr
  on tr.tx_signature = st.tx_signature
where st.token_mint = $1
  and st.side       = $2
order by abs(tr.slot - $3) asc nulls last
limit 1
"""

# 3) Insert / update the pairing record
UPSERT_PAIR = """
insert into trade_pairs (
  copy_trade_id,
  source_trade_id,
  token_mint,
  side,
  delta_slots_event,
  delta_ms_event,
  price_drift,
  confidence,
  diagnostics
)
values ($1,$2,$3,$4,$5,$6,$7,$8,$9)
on conflict (copy_trade_id) do update set
  source_trade_id   = excluded.source_trade_id,
  token_mint        = excluded.token_mint,
  side              = excluded.side,
  delta_slots_event = excluded.delta_slots_event,
  delta_ms_event    = excluded.delta_ms_event,
  price_drift       = excluded.price_drift,
  confidence        = excluded.confidence,
  diagnostics       = excluded.diagnostics,
  paired_at         = now()
"""

class PairingWorker:
    def __init__(self, db: Pool):
        self.db = db

    async def _fallback_db_rpc(self, copy_id: int) -> Optional[int]:
        """
        Optional: if you keep your old DB RPC (fn_nearest_source_for_copy),
        you can call it here. For now we just noop.
        """
        if not RPC_FALLBACK:
            return None
        return None

    async def run_once(self) -> int:
        rows = await fetch_all(self.db, UNPAIRED, BATCH)
        paired = 0

        for r in rows:
            token_mint = r["token_mint"]
            side = r["side"]
            copy_slot = r["copy_slot"]

            # 1) Slot-nearest match in source_trades
            src = await fetch_one(
                self.db,
                FIND_SOURCE_FOR_COPY,
                token_mint,
                side,
                copy_slot,
            )
            source_id: Optional[int] = src["source_id"] if src else None
            source_slot: Optional[int] = src["source_slot"] if src else None

            # 2) Optional RPC / DB function fallback
            if not source_id:
                source_id = await self._fallback_db_rpc(r["copy_id"])

            # 3) Compute simple deltas / confidence
            delta_slots = None
            delta_ms = None
            price_drift = None

            confidence = "LOW"
            if source_id is not None and source_slot is not None and copy_slot is not None:
                delta_slots = copy_slot - source_slot
                confidence = "MED"

            diagnostics: Dict[str, Any] = {
                "note": "pairing_worker",
                "has_source": bool(source_id),
            }
            diagnostics_str = json.dumps(diagnostics)  # TEXT column expects str

            await upsert_one(
                self.db,
                UPSERT_PAIR,
                (
                    r["copy_id"],      # $1 copy_trade_id
                    source_id,         # $2 source_trade_id
                    token_mint,        # $3 token_mint
                    side,              # $4 side
                    delta_slots,       # $5 delta_slots_event
                    delta_ms,          # $6 delta_ms_event
                    price_drift,       # $7 price_drift
                    confidence,        # $8 confidence
                    diagnostics_str,   # $9 diagnostics (TEXT)
                ),
            )
            paired += 1

        await update_heartbeat(self.db, "pairing_worker", len(rows))
        return paired
