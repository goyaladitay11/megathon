-- Optional sample schema. Run only if your hackathon idea needs this table.
create table if not exists public.project_events (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  event_type text not null,
  payload jsonb not null default '{}'::jsonb
);
-- No anonymous access by default. Configure narrowly scoped policies after auth is designed.
alter table public.project_events enable row level security;
