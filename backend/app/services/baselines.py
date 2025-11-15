# backend/app/services/baselines.py
from __future__ import annotations
import asyncio, time
from typing import Any, Dict, Optional
from supabase import create_client
from ..core.config import settings

REFRESH_SECONDS = 10
MIN_SAMPLE_CREATOR = 100
MIN_SAMPLE_TOKEN = 100

class BaselineCache:
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ts: float = 0.0
        self._lock = asyncio.Lock()
        url, key = settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY
        self.sb = create_client(url, key)

    async def _fetch_scope(self, where: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # One SQL to compute percentiles for recent 500 pairs with known landed/tip/cu
        sql = f"""
        with recent as (
          select tp.*, 
                 vcl.tip_lamports, vcl.cu_used, vcl.cu_price_micro_lamports, 
                 (abs(vtc.copy_price - vtc.source_price) / nullif(vtc.source_price,0)) as price_drift_pct,
                 vtc.delta_slots_landed, vtc.delta_ms_event
          from trade_pairs tp
          left join v_copy_tx_landed vcl on vcl.copy_trade_id = tp.copy_trade_id
          left join v_trade_compare  vtc on vtc.copy_id = tp.copy_trade_id
          {where}
          order by tp.paired_at desc
          limit 500
        )
        select
          percentile_disc(0.50) within group (order by (tip_lamports / greatest(cu_used,1))) as tip_per_cu_p50,
          percentile_disc(0.50) within group (order by cu_price_micro_lamports) as cu_price_p50,
          percentile_disc(0.95) within group (order by delta_slots_landed) as delta_slots_landed_p95,
          percentile_disc(0.50) within group (order by delta_ms_event) as delta_ms_event_p50,
          percentile_disc(0.95) within group (order by delta_ms_event) as delta_ms_event_p95,
          percentile_disc(0.50) within group (order by price_drift_pct) as price_drift_p50
        from recent;
        """
        res = self.sb.rpc("exec_sql", {"sql": sql, "params": params}).execute()  # If you don’t have exec_sql RPC, see note below
        if not res.data or not isinstance(res.data, list):
            return {}
        row = res.data[0] or {}
        return {k: (row.get(k) if row.get(k) is not None else None) for k in [
            "tip_per_cu_p50","cu_price_p50","delta_slots_landed_p95","delta_ms_event_p50","delta_ms_event_p95","price_drift_p50"
        ]}

    async def _refresh_locked(self) -> None:
        # global
        global_scope = await self._fetch_scope("where tp.execution_score is not null", {})
        self._cache["global"] = global_scope

        # token-level (only if enough samples)
        # You can expand this on-demand. For now, just keep global. Token/creator scopes can be added later.

        self._ts = time.time()

    async def get(self) -> Dict[str, Any]:
        async with self._lock:
            if time.time() - self._ts > REFRESH_SECONDS:
                await self._refresh_locked()
            return self._cache.get("global", {})

baseline_cache = BaselineCache()
