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
  meta_campaign_id text,
  meta_adset_id text,
  meta_platform text,
  meta_assets jsonb not null default '{}'::jsonb,
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

-- Migration: add Meta launch ID columns (safe to run multiple times)
alter table public.campaign_runs
  add column if not exists meta_campaign_id text,
  add column if not exists meta_adset_id text,
  add column if not exists meta_platform text,
  add column if not exists meta_assets jsonb not null default '{}'::jsonb;

-- ============================================================
-- mcp_campaign_state: de-duplicate launch actions across MCP modules
-- ============================================================
create table if not exists public.mcp_campaign_state (
  id                   UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  recommendation_key   TEXT UNIQUE NOT NULL,
  campaign_id          TEXT NOT NULL,
  platform             TEXT NOT NULL,  -- e.g. "Google Ads", "Instagram", "Facebook"
  ad_type              TEXT DEFAULT 'text',
  resource_name        TEXT,           -- Google Ads resource name or Meta campaign_id
  meta_campaign_id     TEXT,
  meta_adset_id        TEXT,
  launched_at          TIMESTAMPTZ,
  status               TEXT NOT NULL DEFAULT 'launched',
  recommendation       JSONB,          -- full recommendation object for reference
  launchable           BOOLEAN DEFAULT false,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

create index if not exists idx_mcp_state_platform on public.mcp_campaign_state (platform);
create index if not exists idx_mcp_state_campaign_id on public.mcp_campaign_state (campaign_id);

alter table public.mcp_campaign_state disable row level security;

-- ============================================================
-- campaign_ads: stores every ad launched inside a campaign
-- ============================================================
create table if not exists public.campaign_ads (
  id uuid primary key default gen_random_uuid(),
  campaign_run_id uuid not null references public.campaign_runs(id) on delete cascade,
  user_id uuid not null references public.app_users(id) on delete cascade,
  ad_name text,
  headline_1 text not null,
  headline_2 text not null,
  headline_3 text not null,
  description_1 text not null,
  description_2 text not null,
  final_url text not null,
  display_url_path_1 text,
  display_url_path_2 text,
  keywords text[] not null default '{}',
  status text not null default 'launched',
  platform text not null default 'Google Ads',
  google_ad_resource_name text,
  google_adgroup_resource_name text,
  dry_run boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists campaign_ads_run_created_idx
  on public.campaign_ads (campaign_run_id, created_at desc);

alter table public.campaign_ads disable row level security;

-- Migration: add media ad columns (image / video support)
alter table public.campaign_ads
  add column if not exists ad_type text not null default 'text',
  add column if not exists media_url text,
  add column if not exists media_file_name text,
  add column if not exists media_content_type text,
  add column if not exists media_size_bytes bigint,
  add column if not exists long_headline text,
  add column if not exists business_name text;

-- Make headline/description columns nullable for image/video ads
alter table public.campaign_ads alter column headline_1 drop not null;
alter table public.campaign_ads alter column headline_2 drop not null;
alter table public.campaign_ads alter column headline_3 drop not null;
alter table public.campaign_ads alter column description_1 drop not null;
alter table public.campaign_ads alter column description_2 drop not null;
