-- 1) Drop rank from copy wallets (status-only)
alter table public.copy_wallets
  drop column if exists rank;

-- 2) Add ranking to creators
do $$
begin
  if not exists (select 1 from pg_type where typname = 'creator_rank') then
    create type public.creator_rank as enum (
      'GENERAL','COLONEL','MAJOR','CAPTAIN','LIEUTENANT','SERGEANT','PRIVATE'
    );
  end if;
end$$;

alter table public.creators
  add column if not exists rank public.creator_rank,
  add column if not exists score numeric;  -- 0–100 (nullable until we compute)

-- (Optional) seed defaults for future inserts (no automatic value)
-- update public.creators set rank = 'PRIVATE' where rank is null;
