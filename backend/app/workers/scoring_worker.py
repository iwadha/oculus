# backend/app/workers/scoring_worker.py
import os
from asyncpg import Pool
from ..utils.db_helpers import fetch_all, upsert_one, update_heartbeat

BATCH = int(os.getenv("SCORING_BATCH_SIZE", "300"))

# We assume your existing compare view already exposes needed fields.
# If your actual view name differs, adjust 'v_trade_compare' accordingly.
COMPARE_ROWS = """
select
  p.copy_trade_id,
  p.source_trade_id,
  p.delta_slots_event,
  p.delta_ms_event,
  p.price_drift,
  -- Placeholder; if your compare view has a real congestion metric, select it instead
  0 as congestion_proxy
from trade_pairs p
left join v_trade_compare c
  on c.copy_id = p.copy_trade_id
where p.execution_score is null
order by p.copy_trade_id
limit $1
"""

UPSERT_SCORE = """
update trade_pairs
set execution_score = $2::numeric,
    exec_status = 'READY',
    exec_subscores = jsonb_build_object(
        'timing',    $3::numeric,
        'financial', $4::numeric,
        'cost',      $5::numeric,
        'congestion',$6::numeric
    ),
    exec_inputs = jsonb_build_object(
       'delta_slots', $7::integer,
        'delta_ms',    $8::bigint,
        'price_drift', $9::numeric
    ),
    exec_version = 'v1',
    exec_ready_at = now(),
    exec_latency_ms = 0
where copy_trade_id = $1
"""


def _score(delta_slots, delta_ms, price_drift, congestion_proxy):
    """
    Very light placeholder score function following your weighting plan.
    You can refine this later with real heuristics or ML-based scoring.
    Returns:
      total_score, timing_score, financial_score, cost_score, congestion_score
    """
    # For now we ignore the inputs and just apply fixed weights
    timing = 40.0
    financial = 35.0
    cost = 15.0
    congestion = 10.0
    total = timing + financial + cost + congestion
    return total, timing, financial, cost, congestion


class ScoringWorker:
    def __init__(self, db: Pool):
        self.db = db

    async def run_once(self) -> int:
        """
        Pull a batch of unscored pairs from trade_pairs,
        compute an execution score, and update each row.
        """
        rows = await fetch_all(self.db, COMPARE_ROWS, BATCH)
        scored = 0

        for r in rows:
            total, t, f, c, cg = _score(
                r["delta_slots_event"],
                r["delta_ms_event"],
                r["price_drift"],
                r["congestion_proxy"],
            )

            await upsert_one(
                self.db,
                UPSERT_SCORE,
                (
                    r["copy_trade_id"],
                    total,
                    t,
                    f,
                    c,
                    cg,
                    r["delta_slots_event"],
                    r["delta_ms_event"],
                    r["price_drift"],
                ),
            )
            scored += 1

        await update_heartbeat(self.db, "scoring_worker", len(rows))
        return scored
