from asyncpg import Pool
from typing import Any, Dict, List, Optional, Tuple

PROFILE_SQL = """
select * from public.vw_creator_profile
where creator_pubkey = $1
limit 1;
"""

BADGES_SQL = """
select badges from public.vw_creator_badges
where creator_pubkey = $1
limit 1;
"""

ACTIVITY_SQL = """
select *
from public.vw_creator_activity
where creator_pubkey = $1
  and ($2::timestamptz is null or paired_at >= $2)
  and ($3::timestamptz is null or paired_at <= $3)
  and ($4::text is null or side = $4)
  and ($5::float8 is null or execution_score >= $5)
  and ($6::text is null or status = $6)
order by paired_at desc
offset $7
limit  $8;
"""

COUNT_EST_SQL = """
select count(*)::bigint as n
from public.vw_creator_activity
where creator_pubkey = $1
  and ($2::timestamptz is null or paired_at >= $2)
  and ($3::timestamptz is null or paired_at <= $3)
  and ($4::text is null or side = $4)
  and ($5::float8 is null or execution_score >= $5)
  and ($6::text is null or status = $6);
"""

CHARTS_SQL = """
-- keep it tiny: daily buckets over window for four series.
with days as (
  select generate_series(date_trunc('day', now()) - $2::interval + interval '1 day',
                         date_trunc('day', now()),
                         interval '1 day')::date as d
),
roi as (
  select date_trunc('day', day)::date as d, avg(avg_roi_pct) as v
  from public.creator_intel_daily
  where creator_pubkey = $1
    and day >= (current_date - $2::interval)
  group by 1
),
execs as (
  select date_trunc('day', day)::date as d, avg(exec_score_avg) as v
  from public.creator_intel_daily
  where creator_pubkey = $1
    and day >= (current_date - $2::interval)
  group by 1
),
dslots as (
  select date_trunc('day', tp.paired_at)::date as d, avg(tp.delta_slots_landed)::float as v
  from public.trade_pairs tp
  join public.source_trades st on st.id = tp.source_trade_id
  where st.source_wallet_pubkey = $1
    and tp.paired_at >= (now() - $2::interval)
  group by 1
),
crowd as (
  select date_trunc('day', day)::date as d, avg(crowd_pressure) as v
  from public.creator_intel_daily
  where creator_pubkey = $1
    and day >= (current_date - $2::interval)
  group by 1
)
select
  array_agg( (to_char(days.d, 'YYYY-MM-DD'), coalesce(roi.v,0))  order by days.d ) as roi,
  array_agg( (to_char(days.d, 'YYYY-MM-DD'), coalesce(execs.v,0)) order by days.d ) as exec,
  array_agg( (to_char(days.d, 'YYYY-MM-DD'), coalesce(dslots.v,0)) order by days.d ) as dsl,
  array_agg( (to_char(days.d, 'YYYY-MM-DD'), coalesce(crowd.v,0)) order by days.d ) as crd
from days
left join roi    on roi.d = days.d
left join execs  on execs.d = days.d
left join dslots on dslots.d = days.d
left join crowd  on crowd.d = days.d;
"""

async def fetch_profile(pool: Pool, creator_pubkey: str) -> Dict[str, Any]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(PROFILE_SQL, creator_pubkey)
        if not row:
            return {}
        data = dict(row)
        b = await conn.fetchrow(BADGES_SQL, creator_pubkey)
        data["badges"] = (b and b["badges"]) or []
        return data

async def fetch_activity(pool: Pool, creator_pubkey: str, *, since: Optional[str], until: Optional[str],
                         side: Optional[str], min_score: Optional[float], status: Optional[str],
                         page: int, page_size: int):
    offset = (page - 1) * page_size
    async with pool.acquire() as conn:
        rows = await conn.fetch(ACTIVITY_SQL, creator_pubkey, since, until, side, min_score, status, offset, page_size)
        cnt  = await conn.fetchval(COUNT_EST_SQL, creator_pubkey, since, until, side, min_score, status)
    return [dict(r) for r in rows], int(cnt)

async def fetch_charts(pool: Pool, creator_pubkey: str, window: str):
    win = "7 days" if window == "7d" else "30 days"
    async with pool.acquire() as conn:
        r = await conn.fetchrow(CHARTS_SQL, creator_pubkey, win)
    arr = lambda a: [(d, float(v)) for (d, v) in (a or [])]
    return {
        "window": "7d" if window == "7d" else "30d",
        "roi_for_me": arr(r["roi"]),
        "execution_score": arr(r["exec"]),
        "delta_slots": arr(r["dsl"]),
        "crowding": arr(r["crd"]),
    }
