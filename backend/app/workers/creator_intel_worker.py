# backend/app/workers/creator_intel_worker.py
import os
from asyncpg import Pool
from ..utils.db_helpers import fetch_all, upsert_one, update_heartbeat

BATCH = int(os.getenv("CREATOR_INTEL_BATCH_SIZE", "200"))

AGG_ROWS = """
-- Aggregate execution_score per creator over the last 7 days
select
  c.source_wallet_pubkey           as creator_pubkey,
  avg(p.execution_score)           as exec_score_avg,
  count(*)                         as trade_count
from creators c
join source_trades st
  on st.source_wallet_pubkey = c.source_wallet_pubkey
join trade_pairs p
  on p.source_trade_id = st.id
where p.paired_at >= now() - interval '7 days'
group by c.source_wallet_pubkey
order by c.source_wallet_pubkey
limit $1
"""

UPSERT_INTEL_DAILY = """
insert into creator_intel_daily (
  creator_pubkey,
  day,
  exec_score_avg,
  trade_count
)
values ($1, current_date, $2, $3)
on conflict (creator_pubkey, day) do update set
  exec_score_avg = excluded.exec_score_avg,
  trade_count    = excluded.trade_count
"""

class CreatorIntelWorker:
    def __init__(self, db: Pool):
        self.db = db

    async def run_once(self) -> int:
        rows = await fetch_all(self.db, AGG_ROWS, BATCH)
        done = 0
        for r in rows:
            await upsert_one(
                self.db,
                UPSERT_INTEL_DAILY,
                (
                    r["creator_pubkey"],
                    r["exec_score_avg"],
                    r["trade_count"],
                ),
            )
            done += 1

        await update_heartbeat(self.db, "creator_intel_worker", len(rows))
        return done
