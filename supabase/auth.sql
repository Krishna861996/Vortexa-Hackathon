-- Run after schema.sql. Browser keys may only access public challenge fields
-- and the authenticated user's own practice records. Hidden tests and hints
-- remain inaccessible through the Data API.
begin;
grant select (id, title, description, difficulty, function_name, starter_code,
              visible_tests, concept_tags, sort_order)
    on public.challenges to anon, authenticated;
drop policy if exists "Read public challenge fields" on public.challenges;
create policy "Read public challenge fields" on public.challenges
    for select to anon, authenticated using (true);

grant select, insert on public.learners to authenticated;
grant update (hint_positions) on public.learners to authenticated;
drop policy if exists "Read own learner" on public.learners;
create policy "Read own learner" on public.learners
    for select to authenticated using (id = (select auth.uid())::text);
drop policy if exists "Create own learner" on public.learners;
create policy "Create own learner" on public.learners
    for insert to authenticated with check (id = (select auth.uid())::text);
drop policy if exists "Update own hints" on public.learners;
create policy "Update own hints" on public.learners
    for update to authenticated using (id = (select auth.uid())::text)
    with check (id = (select auth.uid())::text);

grant select, insert on public.attempts to authenticated;
grant usage, select on sequence public.attempts_id_seq to authenticated;
drop policy if exists "Read own attempts" on public.attempts;
create policy "Read own attempts" on public.attempts
    for select to authenticated using (learner_id = (select auth.uid())::text);
drop policy if exists "Save own practice" on public.attempts;
create policy "Save own practice" on public.attempts
    for insert to authenticated with check (learner_id = (select auth.uid())::text);
commit;
