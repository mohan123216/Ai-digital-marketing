-- Supabase Schema for AI Digital Marketing Platform
-- Execute this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. CAMPAIGNS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS campaigns (
  id BIGSERIAL PRIMARY KEY,
  product_name VARCHAR(255) NOT NULL,
  product_type VARCHAR(100) NOT NULL,
  goal VARCHAR(100) NOT NULL,
  budget NUMERIC(15, 2) NOT NULL,
  duration INTEGER NOT NULL,
  status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  launched_at TIMESTAMP NULL
);

-- ============================================
-- 2. CAMPAIGN AUDIENCE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS campaign_audience (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  age_min INTEGER,
  age_max INTEGER,
  genders TEXT[],
  interests TEXT[],
  location VARCHAR(255),
  income_level VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 3. CAMPAIGN PLATFORMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS campaign_platforms (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  platform VARCHAR(100) NOT NULL,
  allocated_budget NUMERIC(15, 2),
  status VARCHAR(50) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. AI RECOMMENDATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS ai_recommendations (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  recommendation_type VARCHAR(100),
  content TEXT,
  score NUMERIC(5, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 5. CAMPAIGN PREDICTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS campaign_predictions (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  predicted_reach BIGINT,
  predicted_engagement NUMERIC(5, 2),
  predicted_conversions BIGINT,
  predicted_roi NUMERIC(5, 2),
  confidence_score NUMERIC(5, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. CAMPAIGN PERFORMANCE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS campaign_performance (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  impressions BIGINT DEFAULT 0,
  clicks BIGINT DEFAULT 0,
  conversions BIGINT DEFAULT 0,
  spend NUMERIC(15, 2) DEFAULT 0,
  revenue NUMERIC(15, 2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(campaign_id, date)
);

-- ============================================
-- 7. CAMPAIGN BENCHMARK COMPARISON TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS campaign_benchmark_comparison (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  benchmark_id BIGINT,
  metric_name VARCHAR(100),
  your_performance NUMERIC(15, 2),
  benchmark_value NUMERIC(15, 2),
  percentile NUMERIC(5, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 8. AD BENCHMARKS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS ad_benchmarks (
  id BIGSERIAL PRIMARY KEY,
  platform VARCHAR(100),
  industry VARCHAR(100),
  metric_name VARCHAR(100),
  average_value NUMERIC(15, 2),
  top_value NUMERIC(15, 2),
  bottom_value NUMERIC(15, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_campaign_audience_campaign_id ON campaign_audience(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_platforms_campaign_id ON campaign_platforms(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_campaign_id ON ai_recommendations(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_predictions_campaign_id ON campaign_predictions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_performance_campaign_id ON campaign_performance(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_performance_date ON campaign_performance(campaign_id, date);
CREATE INDEX IF NOT EXISTS idx_ad_benchmarks_platform_industry ON ad_benchmarks(platform, industry);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_audience ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_platforms ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_benchmark_comparison ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_benchmarks ENABLE ROW LEVEL SECURITY;

-- Create policies for campaigns table (allow public read/write for now)
CREATE POLICY "Allow public read campaigns" ON campaigns
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert campaigns" ON campaigns
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update campaigns" ON campaigns
  FOR UPDATE USING (true);

CREATE POLICY "Allow public delete campaigns" ON campaigns
  FOR DELETE USING (true);

-- Create policies for campaign_audience
CREATE POLICY "Allow public read audience" ON campaign_audience
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert audience" ON campaign_audience
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update audience" ON campaign_audience
  FOR UPDATE USING (true);

CREATE POLICY "Allow public delete audience" ON campaign_audience
  FOR DELETE USING (true);

-- Create policies for campaign_platforms
CREATE POLICY "Allow public read platforms" ON campaign_platforms
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert platforms" ON campaign_platforms
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update platforms" ON campaign_platforms
  FOR UPDATE USING (true);

CREATE POLICY "Allow public delete platforms" ON campaign_platforms
  FOR DELETE USING (true);

-- Create policies for ai_recommendations
CREATE POLICY "Allow public read recommendations" ON ai_recommendations
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert recommendations" ON ai_recommendations
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update recommendations" ON ai_recommendations
  FOR UPDATE USING (true);

CREATE POLICY "Allow public delete recommendations" ON ai_recommendations
  FOR DELETE USING (true);

-- Create policies for campaign_predictions
CREATE POLICY "Allow public read predictions" ON campaign_predictions
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert predictions" ON campaign_predictions
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update predictions" ON campaign_predictions
  FOR UPDATE USING (true);

CREATE POLICY "Allow public delete predictions" ON campaign_predictions
  FOR DELETE USING (true);

-- Create policies for campaign_performance
CREATE POLICY "Allow public read performance" ON campaign_performance
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert performance" ON campaign_performance
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update performance" ON campaign_performance
  FOR UPDATE USING (true);

CREATE POLICY "Allow public delete performance" ON campaign_performance
  FOR DELETE USING (true);

-- Create policies for campaign_benchmark_comparison
CREATE POLICY "Allow public read benchmark_comparison" ON campaign_benchmark_comparison
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert benchmark_comparison" ON campaign_benchmark_comparison
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update benchmark_comparison" ON campaign_benchmark_comparison
  FOR UPDATE USING (true);

CREATE POLICY "Allow public delete benchmark_comparison" ON campaign_benchmark_comparison
  FOR DELETE USING (true);

-- Create policies for ad_benchmarks
CREATE POLICY "Allow public read ad_benchmarks" ON ad_benchmarks
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert ad_benchmarks" ON ad_benchmarks
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update ad_benchmarks" ON ad_benchmarks
  FOR UPDATE USING (true);

CREATE POLICY "Allow public delete ad_benchmarks" ON ad_benchmarks
  FOR DELETE USING (true);

-- ============================================
-- DONE!
-- ============================================
