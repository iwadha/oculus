from fastapi import APIRouter, HTTPException, Query, Depends
from asyncpg import Pool

from app.schemas.ladder import (
    LadderResponse, CopyTx, SourceTx, Crowding,
    NeighborFeeStats, FeePercentiles,
    NeighborDistributions, NeighborSamples, SlotAgg, NeighborExample, NeighborSampleGroup
)
from app.services import ladder as svc
from app.api.v1.deps import get_db 

router = APIRouter(prefix="/v1/trades", tags=["ladder"])


@router.get("/{pair_id}/ladder", response_model=LadderResponse)
async def get_ladder(
    pair_id: int,
    window_slots: int = Query(svc.DEFAULT_WINDOW, ge=svc.MIN_WINDOW, le=svc.MAX_WINDOW),
    db: Pool = Depends(get_db),
):
    async with db.acquire() as conn:
        core = await svc.fetch_core(conn, pair_id)
        if not core:
            raise HTTPException(status_code=404, detail="pair_id not found")

        source = await svc.fetch_source_side(conn, pair_id)

        neighbors_rows = []
        if core["event_slot"] is not None:
            neighbors_rows = await svc.fetch_neighbors(conn, pair_id, window_slots)

        # Build crowding + copies_per_slot
        crowd_counts = svc.build_crowd(neighbors_rows, core["event_slot"])
        copies_per_slot = [
            SlotAgg(
                slot=int(r["slot"]),
                relative=int(r["relative"]),
                copies=int(r["copies"]),
                sources=int(r["sources"]),
                tip_avg=(float(r["tip_avg"]) if r["tip_avg"] is not None else None),
                cu_price_avg=(float(r["cu_price_avg"]) if r["cu_price_avg"] is not None else None),
            )
            for r in neighbors_rows
        ]

        # Percentiles for grading
        pct = await svc.fetch_fee_percentiles(conn, pair_id, window_slots)
        tip_grade, cu_grade, notes = svc.grade_efficiency(
            core.get("tip_lamports"),
            (float(core["cu_price_micro_lamports"]) if core.get("cu_price_micro_lamports") is not None else None),
            pct,
        )

        # Histograms + samples
        hist_json = await svc.fetch_hist_and_samples(conn, pair_id, window_slots)

        # Assemble response
        resp = LadderResponse(
            pair_id=int(core["pair_id"]),
            token_mint=core["token_mint"],
            side=core["side"],
            window=window_slots,
            event_slot=(int(core["event_slot"]) if core["event_slot"] is not None else None),
            landed_slot=(int(core["landed_slot"]) if core["landed_slot"] is not None else None),
            delta_slots=(int(core["delta_slots"]) if core["delta_slots"] is not None else None),

            copy_tx=CopyTx(
                tx_signature=core.get("copy_tx_signature"),
                tip_lamports=(int(core["tip_lamports"]) if core["tip_lamports"] is not None else None),
                cu_used=(int(core["cu_used"]) if core["cu_used"] is not None else None),
                priority_fee_lamports=(int(core["priority_fee_lamports"]) if core["priority_fee_lamports"] is not None else None),
                cu_price_micro_lamports=(float(core["cu_price_micro_lamports"]) if core["cu_price_micro_lamports"] is not None else None),
                status=core.get("copy_tx_status"),
            ),

            source_tx=SourceTx(
                creator_pubkey=(source and source.get("creator_pubkey")),
                event_slot=(int(source["event_slot"]) if source and source["event_slot"] is not None else None),
                landed_slot=(int(source["landed_slot"]) if source and source["landed_slot"] is not None else None),
                tip_lamports=(int(source["source_tip_lamports"]) if source and source["source_tip_lamports"] is not None else None),
                cu_used=(int(source["source_cu_used"]) if source and source["source_cu_used"] is not None else None),
                cu_price_micro_lamports=(float(source["source_cu_price_micro_lamports"]) if source and source["source_cu_price_micro_lamports"] is not None else None),
            ),

            crowding=Crowding(
                ahead=crowd_counts["ahead"],
                at_event=crowd_counts["at_event"],
                behind=crowd_counts["behind"],
                total=crowd_counts["total"],
                copies_per_slot=copies_per_slot,
            ),

            neighbor_fee_stats=NeighborFeeStats(
                n=int(pct.get("n") or 0),
                tip_lamports=FeePercentiles(
                    p50=(float(pct["tip_p50"]) if pct.get("tip_p50") is not None else None),
                    p66=(float(pct["tip_p66"]) if pct.get("tip_p66") is not None else None),
                    p90=(float(pct["tip_p90"]) if pct.get("tip_p90") is not None else None),
                ),
                cu_price_micro_lamports=FeePercentiles(
                    p50=(float(pct["cu_p50"]) if pct.get("cu_p50") is not None else None),
                    p66=(float(pct["cu_p66"]) if pct.get("cu_p66") is not None else None),
                    p90=(float(pct["cu_p90"]) if pct.get("cu_p90") is not None else None),
                ),
            ),

            neighbor_distributions=NeighborDistributions(
                tip_lamports_hist=[
                    # json: {'bin_min', 'bin_max', 'count'}
                    # Be tolerant of nulls
                    dict(
                        bin_min=(float(x["bin_min"]) if x.get("bin_min") is not None else None),
                        bin_max=(float(x["bin_max"]) if x.get("bin_max") is not None else None),
                        count=int(x["count"]),
                    )
                    for x in hist_json.get("tip_hist", [])
                ],
                cu_price_micro_lamports_hist=[
                    dict(
                        bin_min=(float(x["bin_min"]) if x.get("bin_min") is not None else None),
                        bin_max=(float(x["bin_max"]) if x.get("bin_max") is not None else None),
                        count=int(x["count"]),
                    )
                    for x in hist_json.get("cu_price_hist", [])
                ],
            ),

            neighbor_samples=NeighborSamples(
                top_ahead=[
                    NeighborSampleGroup(
                        slot=int(g["slot"]),
                        relative=int(g["relative"]),
                        copies=int(g["copies"]),
                        examples=[
                            NeighborExample(
                                copy_wallet_label=e.get("copy_wallet_label"),
                                tx_signature=e.get("tx_signature"),
                                tip_lamports=(int(e["tip_lamports"]) if e.get("tip_lamports") is not None else None),
                                cu_used=(int(e["cu_used"]) if e.get("cu_used") is not None else None),
                                cu_price_micro_lamports=(float(e["cu_price_micro_lamports"]) if e.get("cu_price_micro_lamports") is not None else None),
                            )
                            for e in (g.get("examples") or [])
                        ],
                    )
                    for g in (hist_json.get("top_ahead") or [])
                ],
                top_behind=[
                    NeighborSampleGroup(
                        slot=int(g["slot"]),
                        relative=int(g["relative"]),
                        copies=int(g["copies"]),
                        examples=[
                            NeighborExample(
                                copy_wallet_label=e.get("copy_wallet_label"),
                                tx_signature=e.get("tx_signature"),
                                tip_lamports=(int(e["tip_lamports"]) if e.get("tip_lamports") is not None else None),
                                cu_used=(int(e["cu_used"]) if e.get("cu_used") is not None else None),
                                cu_price_micro_lamports=(float(e["cu_price_micro_lamports"]) if e.get("cu_price_micro_lamports") is not None else None),
                            )
                            for e in (g.get("examples") or [])
                        ],
                    )
                    for g in (hist_json.get("top_behind") or [])
                ],
            ),

            efficiency=dict(
                tip_grade=tip_grade,
                cu_price_grade=cu_grade,
                notes=notes,
            ),

            badges=svc.derive_badges(
                core.get("event_slot"),
                core.get("delta_slots"),
                crowd_counts["total"],
                tip_grade,
            ),

            confidence=core.get("confidence"),
        )
        return resp
