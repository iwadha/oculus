-- ===== GRANTS (needed so PostgREST can see objects) =====
grant usage on schema public to anon, authenticated, service_role;
grant select on all tables in schema public to anon, authenticated;
grant select on all sequences in schema public to anon, authenticated;
alter default privileges in schema public grant select on tables to anon, authenticated;
alter default privileges in schema public grant select on sequences to anon, authenticated;

-- ===== RLS POLICIES =====
-- READ-ONLY to anon/authenticated (browser) for safe analytics.
-- FULL READ/WRITE to service_role (API/workers).

-- Helper: allow all with row filter true (read-only)
create policy "anon_select_tokens"           on public.tokens             for select to anon, authenticated using (true);
create policy "anon_select_creators"         on public.creators           for select to anon, authenticated using (true);
create policy "anon_select_copy_wallets"     on public.copy_wallets       for select to anon, authenticated using (true);
create policy "anon_select_trades_ledger"    on public.trades_ledger      for select to anon, authenticated using (true);
create policy "anon_select_trades_tx"        on public.trades_transactions for select to anon, authenticated using (true);
create policy "anon_select_source_trades"    on public.source_trades      for select to anon, authenticated using (true);
create policy "anon_select_trade_pairs"      on public.trade_pairs        for select to anon, authenticated using (true);
create policy "anon_select_failed_tx"        on public.failed_tx          for select to anon, authenticated using (true);
create policy "anon_select_skipped_tx"       on public.skipped_tx         for select to anon, authenticated using (true);

-- Service role: full access (bypass is automatic, but explicit policies help in SQL clients)
create policy "svc_all_tokens"        on public.tokens             for all to service_role using (true) with check (true);
create policy "svc_all_creators"      on public.creators           for all to service_role using (true) with check (true);
create policy "svc_all_copy_wallets"  on public.copy_wallets       for all to service_role using (true) with check (true);
create policy "svc_all_trades_ledger" on public.trades_ledger      for all to service_role using (true) with check (true);
create policy "svc_all_trades_tx"     on public.trades_transactions for all to service_role using (true) with check (true);
create policy "svc_all_source_trades" on public.source_trades      for all to service_role using (true) with check (true);
create policy "svc_all_trade_pairs"   on public.trade_pairs        for all to service_role using (true) with check (true);
create policy "svc_all_failed_tx"     on public.failed_tx          for all to service_role using (true) with check (true);
create policy "svc_all_skipped_tx"    on public.skipped_tx         for all to service_role using (true) with check (true);

-- NOTE:
-- RLS is already enabled on all tables from migration #0001.
-- With these policies:
--  - Browser (anon key) can SELECT from tables (read-only).
--  - Writes are only possible with service_role key from API/workers.

-- ===== SEED DATA (copy wallets Zeus/Athena) =====
insert into public.copy_wallets (label, pubkey, status, rank)
values
  ('Zeus',   null, 'ACTIVE', 'LIEUTENANT'),
  ('Athena', null, 'ACTIVE', 'LIEUTENANT')
on conflict (label) do nothing;
