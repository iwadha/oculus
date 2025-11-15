# backend/app/workers/alerts_worker.py

import asyncio
import asyncpg
from typing import Any, Dict

from ..core.config import settings
from ..utils.db_helpers import update_heartbeat


# ======================================================================
# SQL — Select candidates for alerts
# ======================================================================

ALERT_CANDIDATES = """
select
    p.copy_trade_id,
    tl.wallet_owned_id as wallet_id,
    st.source_wallet_pubkey as creator_pubkey,
    p.execution_score
from trade_pairs p
join trades_ledger tl
  on tl.id = p.copy_trade_id
join source_trades st
  on st.id = p.source_trade_id
where p.execution_score is not null
  and p.execution_score < $1
  and not exists (
        select 1
        from alerts a
        where a.wallet_id = tl.wallet_owned_id
          and a.category = 'EXECUTION_SCORE'
          and a.created_at > now() - interval '1 day'
  )
order by p.paired_at desc
limit $2;
"""


# ======================================================================
# Alerts Worker
# ======================================================================

class AlertsWorker:
    """
    Creates alerts for poor execution scores.
    Severity bands:
      - CRITICAL < 20
      - HIGH     < 40
      - MEDIUM   < 60
      - LOW      < threshold (e.g. 60)
    """

    def __init__(self, db_pool: asyncpg.pool.Pool):
        self.db_pool = db_pool
        self.threshold = settings.EXEC_SCORE_ALERT_THRESHOLD or 60
        self.batch = settings.ALERTS_BATCH_SIZE

    # ------------------------------------------------------------------
    async def run_once(self):
        """
        Run one alert batch:
        1. Fetch candidates
        2. Insert alerts
        3. Update heartbeat
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(ALERT_CANDIDATES, self.threshold, self.batch)

            backlog = len(rows)
            backlog = len(rows)
            await update_heartbeat(self.db_pool, "alerts_worker", backlog)


            if backlog == 0:
                return

            for row in rows:
                await self._insert_alert(row)

        except Exception as e:
            print(f"[ALERTS] Worker error: {repr(e)}")

    # ------------------------------------------------------------------
    async def _insert_alert(self, row: Dict[str, Any]):
        """
        Insert one alert row.
        """
        score = float(row["execution_score"])

        if score < 20:
            severity = "CRITICAL"
        elif score < 40:
            severity = "HIGH"
        elif score < 60:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        reason = f"Execution score {score:.1f} below threshold {self.threshold}"
        resolution = "Review creator; consider reducing allocation or pausing copying."

        snapshot = {
            "copy_trade_id": row["copy_trade_id"],
            "creator_pubkey": row["creator_pubkey"],
            "raw_score": score,
        }

        sql_insert = """
        insert into alerts (
            wallet_id,
            creator_pubkey,
            category,
            severity,
            reason,
            resolution_action,
            eval_snapshot
        )
        values ($1, $2, 'EXECUTION_SCORE', $3, $4, $5, $6::jsonb);
        """

        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    sql_insert,
                    row["wallet_id"],
                    row["creator_pubkey"],
                    severity,
                    reason,
                    resolution,
                    snapshot,
                )
            print(
                f"[ALERTS] Alert for wallet={row['wallet_id']} "
                f"creator={row['creator_pubkey']} severity={severity}"
            )
        except Exception as e:
            print(f"[ALERTS] Insert failed: {repr(e)}")

    # ------------------------------------------------------------------
    async def loop(self):
        """
        Loop forever with configured interval.
        """
        interval = settings.ALERTS_INTERVAL_MS / 1000
        while True:
            await self.run_once()
            await asyncio.sleep(interval)
