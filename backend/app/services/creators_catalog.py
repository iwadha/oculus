# app/services/creators_catalog.py
from typing import Optional, Tuple, Any, List
from asyncpg import Pool, Record

VALID_SORTS = {
    "last_activity": "last_activity",
    "roi_me_30d": "roi_me_30d",
    "avg_execution_score_7d": "avg_execution_score_7d",
    "trades_copied_7d": "trades_copied_7d",
    "creator_rank": "creator_rank",
}
VALID_ORDER = {"asc", "desc"}

def _interval(window: Optional[str]) -> str:
    if not window:
        return "30 days"
    if window.endswith("d"):
        return f"{int(window[:-1])} days"
    if window.endswith("h"):
        return f"{int(window[:-1])} hours"
    return "30 days"

def _add(params: List[Any], value: Any) -> str:
    params.append(value)
    return f"${len(params)}"

async def fetch_catalog(
    *,
    pool: Pool,                               # injected via get_db
    query: Optional[str],
    tier: Optional[str],
    risk_max: Optional[float],
    roi_min: Optional[float],
    active_within: Optional[str],
    badges: Optional[List[str]],
    sort: str,
    order: str,
    page: int,
    page_size: int,
) -> Tuple[List[Record], int]:
    where: List[str] = ["1=1"]
    params: List[Any] = []

    if query:
        ph = _add(params, f"%{query}%")
        where.append(f"(alias ILIKE {ph} OR creator_pubkey ILIKE {ph})")

    if tier:
        ph = _add(params, tier)
        where.append(f"copyability_tier = {ph}")

    if risk_max is not None:
        ph = _add(params, risk_max)
        where.append(f"risk_score <= {ph}")

    if roi_min is not None:
        ph = _add(params, roi_min)
        where.append(f"roi_me_30d >= {ph}")

    if active_within:
        where.append(f"last_activity >= now() - interval '{_interval(active_within)}'")

    join_badges = ""
    if badges:
        join_badges = "JOIN vw_creator_badges b ON b.creator_pubkey = c.creator_pubkey"
        phs = [ _add(params, b) for b in badges ]
        # your badges table uses column name `badge`
        where.append(f"b.badge IN ({', '.join(phs)})")

    sort_col = VALID_SORTS.get(sort, "last_activity")
    order_kw = "DESC" if order not in VALID_ORDER or order == "desc" else "ASC"
    offset = max(0, (page - 1) * page_size)

    base = f"""
      FROM vw_creator_catalog c
      {join_badges}
      WHERE {" AND ".join(where)}
    """

    sql_items = f"""
      SELECT c.*
      {base}
      ORDER BY {sort_col} {order_kw} NULLS LAST
      LIMIT {page_size} OFFSET {offset}
    """

    sql_count = f"SELECT COUNT(*) {base}"

    async with pool.acquire() as con:
        rows = await con.fetch(sql_items, *params)
        total = await con.fetchval(sql_count, *params)

    return rows, int(total or 0)
