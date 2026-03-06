-- SQL Schema for AI Digital Marketing Campaign Database
-- Created for Supabase

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing tables if they exist (for fresh setup)
DROP TABLE IF EXISTS launched_campaigns CASCADE;
DROP TABLE IF EXISTS campaign_performance CASCADE;
DROP TABLE IF EXISTS campaign_benchmark_comparison CASCADE;
DROP TABLE IF EXISTS campaign_predictions CASCADE;
DROP TABLE IF EXISTS ai_recommendations CASCADE;
DROP TABLE IF EXISTS campaign_platforms CASCADE;
DROP TABLE IF EXISTS campaign_audience CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS ad_benchmarks CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users Table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main Campaigns Table
CREATE TABLE campaigns (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_name VARCHAR(255) NOT NULL,
  product_type VARCHAR(100) NOT NULL,
  goal VARCHAR(100) NOT NULL,
  budget DECIMAL(10, 2) NOT NULL,
  duration BIGINT DEFAULT 30,
  status VARCHAR(50) DEFAULT 'draft',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  launched_at TIMESTAMP NULL
);

-- Campaign Audience Table
CREATE TABLE campaign_audience (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  age_min INTEGER DEFAULT 18,
  age_max INTEGER DEFAULT 65,
  genders TEXT[] DEFAULT ARRAY['male', 'female'],
  interests TEXT[] DEFAULT ARRAY[]::TEXT[],
  location VARCHAR(255) DEFAULT 'Global',
  income_level VARCHAR(50) DEFAULT 'all',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign Platforms Table
CREATE TABLE campaign_platforms (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  platform VARCHAR(100) NOT NULL,
  allocated_budget DECIMAL(10, 2),
  status VARCHAR(50) DEFAULT 'draft',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Recommendations Table
CREATE TABLE ai_recommendations (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(100),
  confidence_score DECIMAL(5, 2),
  impact_level VARCHAR(50),
  action_type VARCHAR(100),
  applied BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign Predictions Table
CREATE TABLE campaign_predictions (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  estimated_reach BIGINT,
  estimated_clicks BIGINT,
  estimated_conversions BIGINT,
  estimated_ctr DECIMAL(10, 4),
  estimated_cpc DECIMAL(10, 2),
  estimated_cpa DECIMAL(10, 2),
  estimated_roas DECIMAL(10, 2),
  audience_score INTEGER DEFAULT 50,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign Plans Table (AI-generated plans from Planning Agent)
CREATE TABLE campaign_plans (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  plan_data JSON NOT NULL,
  benchmarks JSON NOT NULL,
  raw_response TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign Performance Table
CREATE TABLE campaign_performance (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  platform VARCHAR(100),
  date DATE DEFAULT CURRENT_DATE,
  impressions BIGINT DEFAULT 0,
  clicks BIGINT DEFAULT 0,
  conversions BIGINT DEFAULT 0,
  spend DECIMAL(10, 2) DEFAULT 0,
  revenue DECIMAL(10, 2) DEFAULT 0,
  ctr DECIMAL(10, 4) DEFAULT 0,
  cpc DECIMAL(10, 2) DEFAULT 0,
  cpa DECIMAL(10, 2) DEFAULT 0,
  roas DECIMAL(10, 2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign Benchmark Comparison Table
CREATE TABLE campaign_benchmark_comparison (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  platform VARCHAR(100),
  metric VARCHAR(100),
  campaign_value DECIMAL(10, 2),
  benchmark_value DECIMAL(10, 2),
  difference_percentage DECIMAL(10, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ad Benchmarks Table (reference data)
CREATE TABLE ad_benchmarks (
  id BIGSERIAL PRIMARY KEY,
  platform VARCHAR(100) NOT NULL,
  industry VARCHAR(100) NOT NULL,
  metric VARCHAR(100) NOT NULL,
  value DECIMAL(10, 4),
  creative_insight TEXT,
  source VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Launched Campaigns Table (stores manually posted ads)
CREATE TABLE launched_campaigns (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  platform VARCHAR(100) NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  budget DECIMAL(10, 2) NOT NULL,
  duration BIGINT DEFAULT 30,
  target_audience VARCHAR(255),
  status VARCHAR(50) DEFAULT 'active',
CREATE INDEX idx_launched_campaigns_campaign_id ON launched_campaigns(campaign_id);
CREATE INDEX idx_launched_campaigns_platform ON launched_campaigns(platform);
CREATE INDEX idx_launched_campaigns_created_at ON launched_campaigns(created_at DESC);
  ctr DECIMAL(10, 4) DEFAULT 0,
  cpc DECIMAL(10, 2) DEFAULT 0,
  cpa DECIMAL(10, 2) DEFAULT 0,
  impressions BIGINT DEFAULT 0,
  clicks BIGINT DEFAULT 0,
  conversions BIGINT DEFAULT 0,
  media_urls TEXT[],
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  launched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaign_audience_campaign_id ON campaign_audience(campaign_id);
CREATE INDEX idx_campaign_platforms_campaign_id ON campaign_platforms(campaign_id);
CREATE INDEX idx_ai_recommendations_campaign_id ON ai_recommendations(campaign_id);
CREATE INDEX idx_campaign_predictions_campaign_id ON campaign_predictions(campaign_id);
CREATE INDEX idx_campaign_performance_campaign_id ON campaign_performance(campaign_id);
CREATE INDEX idx_campaign_performance_date ON campaign_performance(date);
CREATE INDEX idx_campaign_benchmark_campaign_id ON campaign_benchmark_comparison(campaign_id);
CREATE INDEX idx_ad_benchmarks_industry_platform ON ad_benchmarks(industry, platform);

-- Enable RLS (Row Level Security) if needed
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_audience ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_platforms ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE launched_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_benchmark_comparison ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_benchmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (if needed - modify based on your security requirements)
CREATE POLICY "campaigns_read" ON campaigns FOR SELECT USING (true);
CREATE POLICY "campaigns_create" ON campaigns FOR INSERT WITH CHECK (true);
CREATE POLICY "campaigns_update" ON campaigns FOR UPDATE USING (true);
CREATE POLICY "campaigns_delete" ON campaigns FOR DELETE USING (true);

-- Users policies (adjust for production)
CREATE POLICY "users_read" ON users FOR SELECT USING (true);
CREATE POLICY "users_insert" ON users FOR INSERT WITH CHECK (true);

-- Similar policies for other tables
CREATE POLICY "campaign_audience_read" ON campaign_audience FOR SELECT USING (true);
CREATE POLICY "campaign_audience_insert" ON campaign_audience FOR INSERT WITH CHECK (true);
CREATE POLICY "campaign_audience_update" ON campaign_audience FOR UPDATE USING (true);

CREATE POLICY "campaign_platforms_read" ON campaign_platforms FOR SELECT USING (true);
CREATE POLICY "campaign_platforms_insert" ON campaign_platforms FOR INSERT WITH CHECK (true);
CREATE POLICY "campaign_platforms_update" ON campaign_platforms FOR UPDATE USING (true);

CREATE POLICY "ai_recommendations_read" ON ai_recommendations FOR SELECT USING (true);
CREATE POLICY "ai_recommendations_insert" ON ai_recommendations FOR INSERT WITH CHECK (true);
CREATE POLICY "ai_recommendations_update" ON ai_recommendations FOR UPDATE USING (true);

CREATE POLICY "campaign_plans_read" ON campaign_plans FOR SELECT USING (true);
CREATE POLICY "campaign_plans_insert" ON campaign_plans FOR INSERT WITH CHECK (true);
CREATE POLICY "campaign_plans_update" ON campaign_plans FOR UPDATE USING (true);

CREATE POLICY "campaign_predictions_read" ON campaign_predictions FOR SELECT USING (true);
CREATE POLICY "campaign_predictions_insert" ON campaign_predictions FOR INSERT WITH CHECK (true);

CREATE POLICY "campaign_performance_read" ON campaign_performance FOR SELECT USING (true);
CREATE POLICY "campaign_performance_insert" ON campaign_performance FOR INSERT WITH CHECK (true);
CREATE POLICY "campaign_performance_update" ON campaign_performance FOR UPDATE USING (true);

CREATE POLICY "campaign_benchmark_read" ON campaign_benchmark_comparison FOR SELECT USING (true);
CREATE POLICY "campaign_benchmark_insert" ON campaign_benchmark_comparison FOR INSERT WITH CHECK (true);

CREATE POLICY "ad_benchmarks_read" ON ad_benchmarks FOR SELECT USING (true);

CREATE POLICY "launched_campaigns_read" ON launched_campaigns FOR SELECT USING (true);
CREATE POLICY "launched_campaigns_insert" ON launched_campaigns FOR INSERT WITH CHECK (true);
CREATE POLICY "launched_campaigns_update" ON launched_campaigns FOR UPDATE USING (true);
CREATE POLICY "launched_campaigns_delete" ON launched_campaigns FOR DELETE USING (true);
CREATE POLICY "ad_benchmarks_insert" ON ad_benchmarks FOR INSERT WITH CHECK (true);
