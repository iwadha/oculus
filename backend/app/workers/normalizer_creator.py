import os
from typing import Optional
from asyncpg import Pool
from ..utils.helius_client import HeliusClient
from ..utils.db_helpers import fetch_all, fetch_one, upsert_one, update_heartbeat

BATCH = int(os.getenv("NORMALIZER_CREATOR_BATCH", "300"))
PAIR_WINDOW_SLOTS = int(os.getenv("PAIRING_SEARCH_SLOTS", "50"))

UNPAIRED_COPIES = """
select t.id as copy_id, t.token_mint, t.side, tr.tx_signature, tr.slot, tr.block_time,
       t.wallet_target_id as source_wallet_pubkey
from trades_ledger t
left join trade_pairs p on p.copy_trade_id = t.id
left join trades_transactions tr on tr.tx_signature = (select tx_signature from trades_transactions tt where tt.tx_signature = tr.tx_signature)
where p.copy_trade_id is null
  and t.wallet_target_id is not null                          -- we need creator pubkey hint
order by t.id
limit $1
"""

UPSERT_SOURCE_TRADE = """
insert into source_trades (
  tx_signature, source_wallet_pubkey, token_mint, side, event_ts, tip_lamports,
  cu_price_micro_lamports, route
)
values ($1, $2, $3, $4, $5, $6, $7, $8)
on conflict (tx_signature) do update set
  source_wallet_pubkey = excluded.source_wallet_pubkey,
  token_mint = excluded.token_mint,
  side = excluded.side,
  event_ts = excluded.event_ts,
  tip_lamports = excluded.tip_lamports,
  cu_price_micro_lamports = excluded.cu_price_micro_lamports,
  route = excluded.route
returning tx_signature
"""

class NormalizerCreator:
    def __init__(self, db: Pool, helius: Optional[HeliusClient] = None):
        self.db = db
        self.helius = helius or HeliusClient()

    def _closest_match(self, creator_txs, copy_slot: Optional[int], mint: str, side: str):
        best = None
        best_delta = None
        for tx in creator_txs:
            # Filter: token_mint/side if present in meta (best effort; adjust to your parsing)
            slot = tx.get("slot")
            if copy_slot is not None and slot is not None:
                delta = abs(slot - copy_slot)
                if best_delta is None or delta < best_delta:
                    best = tx; best_delta = delta
        return best

    async def _create_source_row_from_helius(self, creator_pubkey: str, mint: str, side: str, copy_slot: Optional[int]):
        before = copy_slot + PAIR_WINDOW_SLOTS if copy_slot else None
        after  = copy_slot - PAIR_WINDOW_SLOTS if copy_slot else None
        window = self.helius.address_txs_window(creator_pubkey, limit=50, before_slot=before, after_slot=after)
        match = self._closest_match(window, copy_slot, mint, side)
        if not match:
            return None

        # Extract fields defensively
        sig = match.get("signature")
        slot = match.get("slot")
        block_time = match.get("blockTime")
        meta = match.get("meta") or {}
        # Tip/CU extraction are service/provider dependent; store what we can safely
        tip = meta.get("fee")                    # placeholder if tip split not exposed
        cu_price = None                          # optional if not directly available
        route = None

        # Persist source trade
        await upsert_one(
            self.db, UPSERT_SOURCE_TRADE,
            (sig, creator_pubkey, mint, side, block_time, tip, cu_price, route)
        )
        return sig

    async def run_once(self) -> int:
        rows = await fetch_all(self.db, UNPAIRED_COPIES, BATCH)
        created = 0
        for r in rows:
            creator = r["source_wallet_pubkey"]
            if not creator:
                continue
            sig = await self._create_source_row_from_helius(
                creator, r["token_mint"], r["side"], r["slot"]
            )
            if sig:
                created += 1
        await update_heartbeat(self.db, "normalizer_creator", len(rows))
        return created
