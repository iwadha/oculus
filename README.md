# Oculus ⚡

**Real-time copy trading intelligence** — maximize **alpha retention** with creator intelligence, execution analytics, and ops automations.

> Built with FastAPI + Next.js + Supabase + Workers.  
> Desktop-first (1440–2560px). UTC everywhere.

---

## Why Oculus

- **Keep the alpha you copy** — quantify where you lose performance vs the creator.
- **Rank creators** for _your_ outcome: sustained ROI, copyability, and risk.
- **Automate ops** — promote/demote, buy-only/paused, remove bad creators.

---

## Architecture (High Level)

```mermaid
flowchart LR
  subgraph Ingestion
    A[CSV: copy_trade.csv] --> W1[Worker: CSV Ingest]
    B[Sharp TUI Logs] --> W2[Worker: TUI Ingest]
  end
  W1 --> DB[(Supabase Postgres)]
  W2 --> DB
  DB --> P[Pairing Engine]
  P --> S[Execution Score v1.0.0]
  S --> DB
  DB --> API[FastAPI (service_role)]
  API --> WEB[Next.js (anon read via RLS)]
  API -- SSE --> WEB

 ## sequenceDiagram
  participant CSV as copy_trade.csv
  participant TUI as Sharp TUI Logs
  participant WCSV as Worker: CSV Ingest
  participant WTUI as Worker: TUI Ingest
  participant DB as Supabase (UTC)
  participant PE as Pairing Engine
  participant SE as Execution Score v1.0.0
  participant API as FastAPI
  participant UI as Next.js Web

  CSV->>WCSV: parse, validate, normalize
  WCSV->>DB: insert trades_ledger (copy wallet scoped)
  TUI->>WTUI: parse creator pubkeys, context
  WTUI->>DB: upsert creators, source_trades
  DB->>PE: fetch candidates
  PE->>DB: write trade_pairs
  DB->>SE: paired trades
  SE->>DB: write execution_score, diagnostics
  API->>UI: REST + SSE

Key Entities
Creator Wallet — the wallet you copy (ranked + scored)
Copy Wallet — your Sharp wallets (status only: Active/Buy-Only/Sell-Only/Paused/Removed)
Trade Pair — best match between source & copy trade
Execution Score — 0–100: Timing (40), Financial (35), Cost (15), Congestion (10)

Monorepo
apps/
  api/        # FastAPI (Supabase HTTP client)
  web/        # Next.js (SSR, fetches API)
packages/
  workers/    # ingestion, pairing, scoring (coming next)
supabase/
  migrations/ # versioned schema (RLS on, policies applied)

Local Dev (WSL)

API
uv run --directory apps/api uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
# http://localhost:8000/health
# http://localhost:8000/v1/wallets

Web
pnpm --filter @oculus/web dev
# http://localhost:3000

Security & RLS
Anon can read app-facing tables via PostgREST
Writes only via API/workers using service_role
Actions (state changes, removals, tips) must be auditable + reversible

Roadmap (MVP → v1)
CSV ingestion v1 → trades_ledger
TUI ingestion v1 → creators, source_trades
Pairing engine v1
Execution score v1.0.0
Creator league table
Ops panel (copy wallets)
Realtime SSE (live trades + diagnostics)

Contributing (Internal)
Branch from feature/<scope>
Small PRs, atomic commits
Tests for workers + pairing logic
Keep SQL in migrations only
```

## ✅ Module 2 — Real-Time Trade Feed + Dashboard KPIs (Completed)

Oculus now supports a fully reliable real-time stream of copy trades via SSE,
with automated recovery and burst control.

### Key Features
- Live streaming from database (`oculus_trades_view`)
- Cursor-based replay on restart (no gaps, no duplicates)
- Configurable polling + burst limiting for stability
- Backend KPI cache updates in real time
- Works locally with mock mode and in production with DB mode

### Environment Flags (Required)
```env
OCULUS_STREAM_SOURCE=db            # mock | db
OCULUS_DB_POLL_MS=500
OCULUS_DB_POLL_MAX_PER_TICK=250

OCULUS_DB_CURSOR_ENABLED=true
OCULUS_DB_CURSOR_STORAGE=supabase
OCULUS_DB_CURSOR_TABLE=oculus_cursor
OCULUS_DB_CURSOR_STREAM_KEY=trades_view
