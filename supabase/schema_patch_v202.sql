-- Kore Athletic — schema patch for v202 features (announcements + student goals)
-- Run once in Supabase → SQL Editor if student/coach pages crash with PostgREST
-- "Could not find the table" / PGRST205 for ka_announcements or ka_student_goals.
-- Safe to re-run (IF NOT EXISTS).

create table if not exists public.ka_announcements (
  row_id bigserial primary key,
  id text,
  title text,
  body text,
  published_at text,
  published text,
  author text
);

create table if not exists public.ka_student_goals (
  row_id bigserial primary key,
  id text,
  username text,
  athlete_name text,
  event text,
  target_score text,
  updated_at text,
  active text
);

-- Optional indexes for common lookups
create index if not exists ka_announcements_id_idx on public.ka_announcements (id);
create index if not exists ka_student_goals_username_idx on public.ka_student_goals (username);

-- Ensure PostgREST can see the tables (service_role already bypasses RLS)
grant select, insert, update, delete on public.ka_announcements to service_role;
grant select, insert, update, delete on public.ka_student_goals to service_role;
grant usage, select on sequence public.ka_announcements_row_id_seq to service_role;
grant usage, select on sequence public.ka_student_goals_row_id_seq to service_role;

-- Reload schema cache so new tables appear immediately
notify pgrst, 'reload schema';
