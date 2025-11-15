"use client";
import { useEffect, useRef, useState } from "react";
import { SSE_URL } from "@/lib/constants";

export type SSEState = { connected: boolean; lastEventTs?: number; errors: number };

export function useEventSource(onMessage: (ev: MessageEvent) => void) {
  const [state, setState] = useState<SSEState>({ connected: false, errors: 0 });
  const esRef = useRef<EventSource | null>(null);
  const backoff = useRef(1000);

  useEffect(() => {
    let canceled = false;
    function connect() {
      const es = new EventSource(SSE_URL);
      esRef.current = es;

      es.onopen = () => {
        backoff.current = 1000;
        if (!canceled) setState((s) => ({ ...s, connected: true }));
      };
      es.onmessage = (e) => {
        onMessage(e);
        if (!canceled) setState((s) => ({ ...s, lastEventTs: Date.now() }));
      };
      es.onerror = () => {
        es.close();
        if (!canceled)
          setState((s) => ({ ...s, connected: false, errors: s.errors + 1 }));
        const wait = Math.min(8000, backoff.current * 2);
        backoff.current = wait;
        setTimeout(() => !canceled && connect(), wait);
      };
    }
    connect();
    return () => {
      canceled = true;
      esRef.current?.close();
    };
  }, [onMessage]);

  return state;
}

