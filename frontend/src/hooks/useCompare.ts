import { useEffect, useMemo, useRef, useState } from "react";
import type { CompareResponse } from "../types/compare";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

type State = "idle" | "loading" | "ready" | "awaiting" | "error";

export function useCompare(tradeId?: number | string) {
  const [state, setState] = useState<State>("idle");
  const [data, setData] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const tries = useRef(0);

  useEffect(() => {
    if (!tradeId) return;
    let active = true;
    setState("loading");
    setError(null);

    const fetchOnce = async () => {
      try {
        const res = await fetch(`${API_BASE}/v1/trades/${tradeId}/compare`, { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = (await res.json()) as CompareResponse;
        if (!active) return;

        const isAwaiting = (json as any)?.status === "AWAITING_MATCH";
        setData(json);
        setState(isAwaiting ? "awaiting" : "ready");

        // simple retry if awaiting
        if (isAwaiting && tries.current < 3) {
          tries.current += 1;
          setTimeout(fetchOnce, 2500);
        }
      } catch (e: any) {
        if (!active) return;
        setError(e.message || "Fetch failed");
        setState("error");
      }
    };

    fetchOnce();
    return () => {
      active = false;
    };
  }, [tradeId]);

  return useMemo(() => ({ state, data, error }), [state, data, error]);
}
