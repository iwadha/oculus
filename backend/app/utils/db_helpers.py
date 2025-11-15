# backend/app/utils/db_helpers.py

from typing import Any, Dict, Iterable, Optional, Tuple, List
import json

from asyncpg import Pool, Record


def _normalize_params(params: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """
    Ensure parameters are in a form asyncpg / Postgres are happy with.

    - dict / list  -> JSON string (Postgres will cast text -> jsonb if needed)
    - everything else is passed through as-is
    """
    normalized: List[Any] = []
    for v in params:
        if isinstance(v, (dict, list)):
            normalized.append(json.dumps(v))
        else:
            normalized.append(v)
    return tuple(normalized)


async def upsert_one(db: Pool, sql: str, params: Tuple[Any, ...]) -> Optional[Record]:
    """
    Convenience helper for a single-row INSERT/UPDATE/UPSERT pattern.

    - Normalizes params (e.g. dict/list -> JSON string)
    - Returns the row if the SQL uses `... returning *`, else None
    """
    params = _normalize_params(params)
    return await db.fetchrow(sql, *params)


async def fetch_all(db: Pool, sql: str, *args) -> List[Record]:
    """
    Run a SELECT and return all rows as a list.
    """
    rows = await db.fetch(sql, *args)
    return list(rows)


async def fetch_one(db: Pool, sql: str, *args) -> Optional[Record]:
    """
    Run a SELECT and return a single row (or None).
    """
    return await db.fetchrow(sql, *args)


async def update_heartbeat(db: Pool, worker_name: str, backlog: int) -> None:
    """
    Upsert a heartbeat entry for a worker into system_worker_heartbeats.

    - worker_name: identifier for the worker (e.g. 'pairing_worker')
    - backlog: how many items were seen in the last run (for monitoring)
    """
    await db.execute(
        """
        insert into system_worker_heartbeats (worker_name, last_ok_at, backlog_count)
        values ($1, now(), $2)
        on conflict (worker_name)
        do update set
          last_ok_at    = excluded.last_ok_at,
          backlog_count = excluded.backlog_count,
          updated_at    = now()
        """,
        worker_name,
        backlog,
    )
