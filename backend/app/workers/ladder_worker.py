# backend/app/workers/ladder_worker.py
import os
import logging
from typing import Optional

from asyncpg import Pool

from ..utils.db_helpers import update_heartbeat

log = logging.getLogger("ladder_worker")

# How many pairs to process per run_once
BATCH = int(os.getenv("LADDER_BATCH_SIZE", "200"))

# ---------------------------------------------------------------------------
# SQL: find pairs that need ladder snapshots
# ---------------------------------------------------------------------------

PAIRS_NEEDING_LADDER = """
select
    tp.copy_trade_id                         as pair_id,
    st.id                                    as source_trade_id,
    st.event_slot                            as source_event_slot,
    coalesce(st.landed_slot, st.event_slot)  as source_landed_slot,
    cp_tx.slot                               as copy_slot
from trade_pairs tp
join trades_ledger cp
  on cp.id = tp.copy_trade_id
left join source_trades st
  on st.id = tp.source_trade_id
left join trades_transactions cp_tx
  on cp_tx.tx_signature = cp.tx_signature
left join ladder_snapshots ls
  on ls.pair_id = tp.copy_trade_id
where tp.source_trade_id is not null
  and ls.pair_id is null
  -- only consider pairs where we actually have a copy signature + slot
  and cp.tx_signature is not null
  and cp_tx.slot is not null
  -- and we have at least some source slot info
  and coalesce(st.landed_slot, st.event_slot) is not null
order by tp.copy_trade_id
limit $1;
"""


# ---------------------------------------------------------------------------
# SQL: upsert into ladder_snapshots
# ---------------------------------------------------------------------------

UPSERT_LADDER = """
insert into ladder_snapshots (
    pair_id,
    event_slot,
    copy_landed_slot,
    delta_slots,
    crowd_ahead,
    crowd_at_event,
    crowd_behind,
    tip_p50,
    tip_p66,
    tip_p90,
    cu_p50,
    cu_p66,
    cu_p90,
    tip_grade,
    cu_grade,
    hist,
    status,
    computed_at
)
values (
    $1, $2, $3, $4,
    $5, $6, $7,
    $8, $9, $10,
    $11, $12, $13,
    $14, $15,
    $16,
    $17,
    now()
)
on conflict (pair_id) do update
set event_slot        = excluded.event_slot,
    copy_landed_slot  = excluded.copy_landed_slot,
    delta_slots       = excluded.delta_slots,
    crowd_ahead       = excluded.crowd_ahead,
    crowd_at_event    = excluded.crowd_at_event,
    crowd_behind      = excluded.crowd_behind,
    tip_p50           = excluded.tip_p50,
    tip_p66           = excluded.tip_p66,
    tip_p90           = excluded.tip_p90,
    cu_p50            = excluded.cu_p50,
    cu_p66            = excluded.cu_p66,
    cu_p90            = excluded.cu_p90,
    tip_grade         = excluded.tip_grade,
    cu_grade          = excluded.cu_grade,
    hist              = excluded.hist,
    status            = excluded.status,
    computed_at       = excluded.computed_at;
"""

class LadderWorker:
    """Worker that ensures every paired trade has a ladder snapshot.

    For now we compute a _minimal_ snapshot:
      * event_slot        = source_landed_slot (or event_slot)
      * copy_landed_slot  = copy_slot
      * delta_slots       = copy_slot - event_slot

    All of the crowding / fee percentile fields are left NULL for now.
    Once this is stable we can enrich the hist JSON and percentile fields
    using additional Helius / baseline data.
    """

    def __init__(self, db: Pool):
        self.db: Pool = db

    async def run_once(self) -> int:
        """Process up to BATCH pairs needing ladder snapshots.

        Returns the number of snapshots written/updated.
        """
        rows = await self.db.fetch(PAIRS_NEEDING_LADDER, BATCH)
        if not rows:
            await update_heartbeat(self.db, "ladder_worker", 0)
            return 0

        written = 0

        for r in rows:
            pair_id: int = r["pair_id"]
            source_slot: Optional[int] = r["source_landed_slot"] or r["source_event_slot"]
            copy_slot: Optional[int] = r["copy_slot"]

            if source_slot is None or copy_slot is None:
                log.info(
                    "[LADDER] Skip pair_id=%s: insufficient slot data "
                    "(source_slot=%s copy_slot=%s)",
                    pair_id,
                    source_slot,
                    copy_slot,
                )
                continue

            delta_slots = copy_slot - source_slot

            # Minimal snapshot: only set core fields; everything else NULL for now.
            await self.db.execute(
                UPSERT_LADDER,
                pair_id,          # $1 pair_id
                source_slot,      # $2 event_slot
                copy_slot,        # $3 copy_landed_slot
                delta_slots,      # $4 delta_slots
                None,             # $5 crowd_ahead
                None,             # $6 crowd_at_event
                None,             # $7 crowd_behind
                None,             # $8 tip_p50
                None,             # $9 tip_p66
                None,             # $10 tip_p90
                None,             # $11 cu_p50
                None,             # $12 cu_p66
                None,             # $13 cu_p90
                None,             # $14 tip_grade
                None,             # $15 cu_grade
                None,             # $16 hist
                "OK",             # $17 status
            )
            written += 1

        # Backlog ≈ "how many still need ladder" → we don't know total here,
        # but len(rows) is a useful approximation for monitoring.
        await update_heartbeat(self.db, "ladder_worker", len(rows))
        log.info("[LADDER] run_once: wrote %s snapshots (batch=%s)", written, len(rows))
        return written
