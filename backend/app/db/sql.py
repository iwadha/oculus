# backend/app/db/sql.py
from typing import Optional, Dict, Any, List, Tuple, Sequence
import os

from supabase import create_client, Client


# ---------------------------------------------------------------------------
# Supabase client bootstrap (direct from environment)
# ---------------------------------------------------------------------------

def sb() -> Client:
    """
    Return a Supabase client using environment variables.

    Required:
      - SUPABASE_URL
      - SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError("Supabase credentials missing: SUPABASE_URL or key env vars not set")

    return create_client(url, key)


# ---------------------------------------------------------------------------
# READ HELPERS
# ---------------------------------------------------------------------------

def fetch_copy_trade(copy_trade_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a trades_ledger row plus the latest trades_transactions row
    for a given copy trade.

    Expected columns:
      - trades_ledger:
          id, timestamp, token_mint, side, invested_sol, received_qty, pnl_percent
      - trades_transactions:
          slot, block_time (joined via trades_fk = trades_ledger.id)
    """
    client = sb()

    # trades_ledger
    tl_rows = (
        client.table("trades_ledger")
        .select(
            "id, timestamp, token_mint, side, invested_sol, received_qty, pnl_percent"
        )
        .eq("id", copy_trade_id)
        .limit(1)
        .execute()
        .data
    )
    if not tl_rows:
        return None
    tl = tl_rows[0]

    # latest transaction for this trade (slot + block_time; optional)
    tx_rows = (
        client.table("trades_transactions")
        .select("slot, block_time")
        .eq("trades_fk", copy_trade_id)
        .order("slot", desc=True)
        .limit(1)
        .execute()
        .data
    )
    tx = tx_rows[0] if tx_rows else {}

    tl["tx_slot"] = tx.get("slot")
    tl["tx_block_time"] = tx.get("block_time")
    return tl


def fetch_source_trade(source_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a source_trades row by id.

    Expected columns:
      id, event_ts, event_slot, price, route,
      tip_lamports, cu_used, cu_price_micro_lamports
    """
    client = sb()
    rows = (
        client.table("source_trades")
        .select(
            "id, event_ts, event_slot, price, route, "
            "tip_lamports, cu_used, cu_price_micro_lamports"
        )
        .eq("id", source_id)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def fetch_compare_row(copy_trade_id: int) -> Optional[Dict[str, Any]]:
    """
    Read one row from the v_trade_compare view for the given copy trade id.

    This is used by:
      - app/services/pairing_service.compare_for_trade
    """
    client = sb()
    res = (
        client.table("v_trade_compare")
        .select("*")
        .eq("copy_id", copy_trade_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    return rows[0] if rows else None


# ---------------------------------------------------------------------------
# RPC / NEAREST SOURCE HELPERS
# ---------------------------------------------------------------------------

def nearest_source_for_copy(copy_trade_id: int, window_s: int) -> Optional[str]:
    """
    RPC bridge to public.fn_nearest_source_for_copy(copy_id bigint).

    NOTE:
    - The DB function expects EXACTLY one argument named `copy_id`.
    - It returns a rowset (list) with columns including `source_id`.
    - This helper normalizes to a single UUID string (source_id) or None.

    The `window_s` parameter is kept only for backwards compatibility with
    callers; the RPC itself doesn't currently use it.
    """
    client = sb()
    try:
        res = client.rpc(
            "fn_nearest_source_for_copy",
            {"copy_id": copy_trade_id},
        ).execute()

        data: Any = getattr(res, "data", None)

        # supabase-py returns a list of rows; be defensive:
        if isinstance(data, Sequence) and not isinstance(data, (str, bytes)) and len(data) > 0:
            row = data[0]
            if isinstance(row, dict):
                return row.get("source_id")
            return None
        if isinstance(data, dict):
            return data.get("source_id")
        return None

    except Exception:
        # On any RPC failure (404, arg mismatch, etc.), just return None so the
        # caller can fall back to "AWAITING_MATCH" without crashing.
        return None


def call_nearest_source(copy_trade_id: int, window_s: int) -> Optional[str]:
    """
    Backwards-compatible alias used by some older code.

    Delegates to nearest_source_for_copy().
    """
    return nearest_source_for_copy(copy_trade_id, window_s)


# ---------------------------------------------------------------------------
# JOB SELECTION HELPERS (for rebuilds / tooling)
# ---------------------------------------------------------------------------

def select_recent_copy_ids(
    limit: int = 200,
    since_iso: Optional[str] = None,
    until_iso: Optional[str] = None,
) -> List[int]:
    """
    Get recent trades_ledger ids for batch pairing / rebuild.

    Filters by timestamp if since_iso / until_iso are provided.
    """
    client = sb()
    q = (
        client.table("trades_ledger")
        .select("id,timestamp")
        .order("timestamp", desc=True)
    )
    if since_iso:
        q = q.gte("timestamp", since_iso)
    if until_iso:
        q = q.lte("timestamp", until_iso)
    if limit:
        q = q.limit(limit)

    rows = q.execute().data or []
    return [r["id"] for r in rows]


# ---------------------------------------------------------------------------
# WRITE / UPSERT HELPERS
# ---------------------------------------------------------------------------

def upsert_trade_pair(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Upsert into trade_pairs by copy_trade_id (PK).

    Typical payload keys:
      copy_trade_id, source_trade_id, token_mint, side,
      delta_ms_event, delta_slots_event,
      delta_ms_landed, delta_slots_landed,
      price_drift, size_similarity, route_similarity, confidence,
      execution_score, exec_subscores, exec_inputs, exec_status,
      paired_at, diagnostics, etc.

    Returns (ok, error_message).
    """
    client = sb()
    try:
        client.table("trade_pairs").upsert(
            payload,
            on_conflict="copy_trade_id",
        ).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def upsert_source_trade(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Insert or update a row in source_trades by id.

    The exact columns in `payload` should match your source_trades schema.
    """
    client = sb()
    try:
        client.table("source_trades").upsert(
            payload,
            on_conflict="id",
        ).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def upsert_ladder_snapshot(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Upsert a ladder_snapshots row keyed by pair_id.

    Expected columns (as per your schema):
      pair_id, event_slot, copy_landed_slot, delta_slots,
      crowd_ahead, crowd_at_event, crowd_behind,
      tip_p50, tip_p66, tip_p90,
      cu_p50, cu_p66, cu_p90,
      tip_grade, cu_grade, hist, status, computed_at
    """
    client = sb()
    try:
        client.table("ladder_snapshots").upsert(
            payload,
            on_conflict="pair_id",
        ).execute()
        return True, None
    except Exception as e:
        return False, str(e)
