-- ============================================================
-- NexusAds: MCP Campaign State Migration
-- Run this in your Supabase SQL Editor ONCE
-- ============================================================
-- This replaces the JSON file state storage used by the
-- Google Ads and Meta Ads MCP modules with a Supabase table.
-- ============================================================

CREATE TABLE IF NOT EXISTS mcp_campaign_state (
  id                   UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  recommendation_key   TEXT UNIQUE NOT NULL,
  campaign_id          TEXT NOT NULL,
  platform             TEXT NOT NULL,  -- e.g. "Google Ads", "Instagram", "Facebook"
  ad_type              TEXT DEFAULT 'text',
  resource_name        TEXT,           -- Google Ads resource name or Meta campaign_id
  meta_campaign_id     TEXT,           -- Explicit Meta campaign ID (for Meta Ads)
  meta_adset_id        TEXT,           -- Explicit Meta AdSet ID (for Meta Ads)
  launched_at          TIMESTAMPTZ,
  status               TEXT NOT NULL DEFAULT 'launched',
  recommendation       JSONB,          -- full recommendation object for reference
  launchable           BOOLEAN DEFAULT false,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookup by platform
CREATE INDEX IF NOT EXISTS idx_mcp_state_platform ON mcp_campaign_state (platform);

-- Index for fast lookup by campaign_id
CREATE INDEX IF NOT EXISTS idx_mcp_state_campaign_id ON mcp_campaign_state (campaign_id);

-- Enable Row Level Security (service role bypasses this, so it's fine)
ALTER TABLE mcp_campaign_state ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (used by the backend)
CREATE POLICY IF NOT EXISTS "Service role full access" ON mcp_campaign_state
  USING (true) WITH CHECK (true);

-- ============================================================
-- Campaign Optimization Logs
-- ============================================================
CREATE TABLE IF NOT EXISTS campaign_optimizations (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  campaign_run_id TEXT NOT NULL,
  user_id         UUID NOT NULL,
  platform        TEXT NOT NULL,
  dry_run         BOOLEAN DEFAULT false,
  status          TEXT,
  analysis        JSONB,
  actions         JSONB,
  old_values      JSONB,   -- snapshot of values BEFORE optimization (for undo)
  undone          BOOLEAN DEFAULT false,  -- true if this optimization has been reverted
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_optimizations_run_id ON campaign_optimizations (campaign_run_id);

-- Add columns if table already exists (safe to run multiple times)
ALTER TABLE campaign_optimizations ADD COLUMN IF NOT EXISTS old_values JSONB;
ALTER TABLE campaign_optimizations ADD COLUMN IF NOT EXISTS undone BOOLEAN DEFAULT false;

-- ============================================================
-- campaign_runs: store Meta launch IDs (optional convenience)
-- ============================================================
ALTER TABLE public.campaign_runs
  ADD COLUMN IF NOT EXISTS meta_campaign_id text,
  ADD COLUMN IF NOT EXISTS meta_adset_id text,
  ADD COLUMN IF NOT EXISTS meta_platform text,
  ADD COLUMN IF NOT EXISTS meta_assets jsonb not null default '{}'::jsonb;
