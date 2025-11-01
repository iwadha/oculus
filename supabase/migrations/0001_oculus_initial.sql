-- Oculus DB — Initial schema (public), PostgreSQL 15+ / Supabase
-- Extensions
create extension if not exists pgcrypto;
create extension if not exists "uuid-ossp";

-- ===== ENUMS (public schema) =====
do $$ begin
  if not exists (select 1 from pg_type where typname = 'trade_side') then
    create type trade_side as enum ('BUY','SELL');
  end if;
  if not exists (select 1 from pg_type where typname = 'confidence_level') then
    create type confidence_level as enum ('HIGH','MED','LOW','NONE');
  end if;
  if not exists (select 1 from pg_type where typname = 'copy_wallet_status') then
    create type copy_wallet_status as enum ('ACTIVE','BUY_ONLY','SELL_ONLY','PAUSED','REMOVED');
  end if;
  if not exists (select 1 from pg_type where typname = 'copy_wallet_rank') then
    create type copy_wallet_rank as enum ('GENERAL','COLONEL','CAPTAIN','LIEUTENANT','SERGEANT');
  end if;
  if not exists (select 1 from pg_type where typname = 'tx_status') then
    create type tx_status as enum ('PENDING','SUCCESS','FAILED');
  end if;
end $$;

-- ===== REFERENCE TABLES =====
create table if not exists public.tokens (
  token_mint text primary key,
  symbol text,
  decimals int2,
  image_url text,
  first_seen_at timestamptz default now(),
  last_refreshed_at timestamptz
);

create table if not exists public.creators (
  source_wallet_pubkey text primary key,
  label text,
  is_active boolean default true,
  first_seen_at timestamptz default now(),
  last_seen_at timestamptz
);

create table if not exists public.copy_wallets (
  id uuid primary key default gen_random_uuid(),
  label text not null unique,
  pubkey text unique,
  status copy_wallet_status not null default 'ACTIVE',
  rank copy_wallet_rank not null default 'LIEUTENANT',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- updated_at trigger
create or replace function public.tg_set_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;

drop trigger if exists trg_copy_wallets_updated on public.copy_wallets;
create trigger trg_copy_wallets_updated
before update on public.copy_wallets
for each row execute function public.tg_set_updated_at();

-- ===== CORE TRADE TABLES =====
create table if not exists public.trades_ledger (
  id bigserial primary key,
  timestamp timestamptz not null,
  wallet_owned_id uuid references public.copy_wallets(id) on delete set null,
  wallet_target_id text references public.creators(source_wallet_pubkey) on delete set null,
  token_mint text references public.tokens(token_mint) on delete set null,
  side trade_side not null,
  invested_sol numeric(38,9),
  received_qty numeric(38,18),
  pnl_value_sol numeric(38,9),
  pnl_percent numeric(9,4),
  percent_sold numeric(9,4),
  reason text,
  source_identifier text,
  tx_signature text,
  created_at timestamptz default now(),
  constraint chk_percent_sold check (percent_sold is null or (percent_sold >= 0 and percent_sold <= 100))
);

create table if not exists public.trades_transactions (
  id bigserial primary key,
  trades_fk bigint references public.trades_ledger(id) on delete cascade,
  tx_signature text unique,
  slot int8,
  block_time timestamptz,
  priority_fee_lamports int8,
  cu_used int8,
  tip_lamports int8,
  status tx_status,
  raw jsonb
);

create table if not exists public.source_trades (
  id uuid primary key default gen_random_uuid(),
  source_wallet_pubkey text not null references public.creators(source_wallet_pubkey) on delete cascade,
  token_mint text not null references public.tokens(token_mint) on delete cascade,
  side trade_side not null,
  route text,
  price numeric(38,18),
  size numeric(38,18),
  tip_lamports int8,
  cu_used int8,
  cu_price_micro_lamports int8,
  tx_signature text unique,
  event_slot int8 not null,
  event_ts timestamptz not null,
  landed_slot int8,
  landed_ts timestamptz,
  copy_wallet_label text,
  raw jsonb,
  created_at timestamptz default now()
);

create table if not exists public.trade_pairs (
  copy_trade_id bigint primary key references public.trades_ledger(id) on delete cascade,
  source_trade_id uuid references public.source_trades(id) on delete set null,
  confidence confidence_level not null default 'NONE',
  delta_slots_event int,
  delta_ms_event int,
  delta_slots_landed int,
  delta_ms_landed int,
  price_drift numeric(38,18),
  route_similarity numeric(5,2),
  size_similarity numeric(5,2),
  execution_score numeric(5,2),
  diagnostics jsonb,
  paired_at timestamptz default now()
);

create table if not exists public.failed_tx (
  id bigserial primary key,
  ts timestamptz not null,
  slot int8,
  copy_wallet_label text,
  wallet_owned_id uuid references public.copy_wallets(id) on delete set null,
  creator_pubkey text references public.creators(source_wallet_pubkey) on delete set null,
  token_mint text references public.tokens(token_mint) on delete set null,
  side trade_side,
  route text,
  rpc_host text,
  error_class text,
  error_code text,
  raw_msg text,
  cu_req int8,
  cu_used int8,
  tip_lamports int8,
  retry_index int,
  tx_signature text,
  context jsonb,
  created_at timestamptz default now()
);

create table if not exists public.skipped_tx (
  id bigserial primary key,
  ts timestamptz not null,
  copy_wallet_label text,
  wallet_owned_id uuid references public.copy_wallets(id) on delete set null,
  creator_pubkey text references public.creators(source_wallet_pubkey) on delete set null,
  token_mint text references public.tokens(token_mint) on delete set null,
  side trade_side,
  skip_reason text,
  est_missed_pnl_sol numeric(38,9),
  policy_snapshot jsonb,
  created_at timestamptz default now()
);

-- ===== INDEXES =====
create index if not exists idx_trades_ledger_time on public.trades_ledger (timestamp desc);
create index if not exists idx_trades_ledger_target_time on public.trades_ledger (wallet_target_id, timestamp desc);
create index if not exists idx_trades_ledger_owned_time on public.trades_ledger (wallet_owned_id, timestamp desc);
create index if not exists idx_trades_ledger_token_time on public.trades_ledger (token_mint, timestamp desc);

create index if not exists idx_trades_tx_sig on public.trades_transactions (tx_signature);
create index if not exists idx_source_trades_token_side_time on public.source_trades (token_mint, side, event_ts desc);
create index if not exists idx_source_trades_creator_time on public.source_trades (source_wallet_pubkey, event_ts desc);
create index if not exists idx_trade_pairs_source on public.trade_pairs (source_trade_id);
create index if not exists idx_failed_tx_time on public.failed_tx (ts desc);
create index if not exists idx_failed_tx_creator on public.failed_tx (creator_pubkey, ts desc);
create index if not exists idx_skipped_tx_time on public.skipped_tx (ts desc);
create index if not exists idx_skipped_tx_creator on public.skipped_tx (creator_pubkey, ts desc);

-- ===== VIEWS (stubs) =====
create or replace view public.v_kpis_global as
select
  coalesce(sum(pnl_value_sol),0) as realized_pnl_sol,
  coalesce(avg(tp.execution_score),0) as avg_execution_score,
  now() as generated_at
from public.trades_ledger tl
left join public.trade_pairs tp on tp.copy_trade_id = tl.id;

create or replace view public.v_execution_score_by_wallet as
select tl.wallet_owned_id,
       avg(tp.execution_score) as avg_exec_score,
       count(*) as trade_count
from public.trades_ledger tl
left join public.trade_pairs tp on tp.copy_trade_id = tl.id
group by 1;

-- ===== RLS (enable now; policies added later) =====
alter table public.tokens enable row level security;
alter table public.creators enable row level security;
alter table public.copy_wallets enable row level security;
alter table public.trades_ledger enable row level security;
alter table public.trades_transactions enable row level security;
alter table public.source_trades enable row level security;
alter table public.trade_pairs enable row level security;
alter table public.failed_tx enable row level security;
alter table public.skipped_tx enable row level security;

-- Note: With RLS enabled and no policies, anon cannot read/write.
-- The service role key bypasses RLS for ingestion/workers.
