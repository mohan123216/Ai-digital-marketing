create extension if not exists "pgcrypto";

create table if not exists public.app_users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.campaign_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.app_users(id) on delete cascade,
  product_name text not null,
  campaign_goal text not null,
  budget_min numeric not null,
  budget_max numeric not null,
  top_platform text,
  predicted_roi numeric,
  input jsonb not null,
  output jsonb not null,
  launched_platforms jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists app_users_email_idx
  on public.app_users (email);

create index if not exists campaign_runs_user_created_idx
  on public.campaign_runs (user_id, created_at desc);

alter table public.campaign_runs disable row level security;

alter table public.campaign_runs drop constraint if exists campaign_runs_user_id_fkey;
alter table public.campaign_runs
  add constraint campaign_runs_user_id_fkey
  foreign key (user_id) references public.app_users(id) on delete cascade;

-- Migration: add launched_platforms column if it does not exist yet
alter table public.campaign_runs
  add column if not exists launched_platforms jsonb not null default '[]'::jsonb;
