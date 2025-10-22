-- Enhanced database schema for comprehensive astrological trading system
-- This migration adds tables for storing Claude AI insights and daily recommendations

-- Store Claude AI insights about astrological patterns
CREATE TABLE IF NOT EXISTS astrological_insights (
    id SERIAL PRIMARY KEY,
    insight_type VARCHAR(50) NOT NULL, -- 'pattern', 'rule', 'correlation'
    category VARCHAR(50) NOT NULL,     -- 'lunar_phase', 'planetary_aspect', 'seasonal'
    pattern_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    confidence_score DOUBLE PRECISION, -- 0-100
    success_rate DOUBLE PRECISION,     -- percentage
    avg_profit DOUBLE PRECISION,
    trade_count INTEGER,
    evidence JSONB,                    -- supporting data
    claude_analysis TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient querying
CREATE INDEX IF NOT EXISTS idx_astrological_insights_category ON astrological_insights(category);
CREATE INDEX IF NOT EXISTS idx_astrological_insights_confidence ON astrological_insights(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_astrological_insights_success_rate ON astrological_insights(success_rate DESC);

-- Store daily astrological conditions
CREATE TABLE IF NOT EXISTS daily_astrological_conditions (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,
    planetary_positions JSONB NOT NULL,
    major_aspects JSONB,
    lunar_phase_name VARCHAR(50),
    lunar_phase_angle DOUBLE PRECISION,
    significant_events TEXT[],
    daily_score DOUBLE PRECISION,      -- overall favorability 0-100
    market_outlook TEXT,               -- 'bullish', 'bearish', 'neutral', 'volatile'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient date-based queries
CREATE INDEX IF NOT EXISTS idx_daily_astro_conditions_date ON daily_astrological_conditions(trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_astro_conditions_score ON daily_astrological_conditions(daily_score DESC);

-- Store daily trading recommendations
CREATE TABLE IF NOT EXISTS daily_trading_recommendations (
    id SERIAL PRIMARY KEY,
    recommendation_date DATE NOT NULL,
    symbol VARCHAR(25) NOT NULL,
    recommendation_type VARCHAR(20) NOT NULL, -- 'enter_long', 'enter_short', 'exit', 'hold', 'avoid'
    confidence DOUBLE PRECISION NOT NULL,     -- 0-100
    astrological_reasoning TEXT,
    supporting_insights INTEGER[],            -- references to astrological_insights.id
    target_price DOUBLE PRECISION,
    stop_loss DOUBLE PRECISION,
    holding_period_days INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(recommendation_date, symbol, recommendation_type)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_daily_recommendations_date ON daily_trading_recommendations(recommendation_date);
CREATE INDEX IF NOT EXISTS idx_daily_recommendations_symbol ON daily_trading_recommendations(symbol);
CREATE INDEX IF NOT EXISTS idx_daily_recommendations_confidence ON daily_trading_recommendations(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_daily_recommendations_type ON daily_trading_recommendations(recommendation_type);

-- Add foreign key constraint for supporting insights
-- Note: Using array of integers instead of proper FK for flexibility

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger for astrological_insights
DROP TRIGGER IF EXISTS update_astrological_insights_updated_at ON astrological_insights;
CREATE TRIGGER update_astrological_insights_updated_at
    BEFORE UPDATE ON astrological_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your user)
-- GRANT ALL PRIVILEGES ON astrological_insights TO your_db_user;
-- GRANT ALL PRIVILEGES ON daily_astrological_conditions TO your_db_user;
-- GRANT ALL PRIVILEGES ON daily_trading_recommendations TO your_db_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_db_user;

-- Useful queries for monitoring:
--
-- SELECT COUNT(*) FROM astrological_insights;
-- SELECT category, COUNT(*) FROM astrological_insights GROUP BY category ORDER BY COUNT(*) DESC;
-- SELECT AVG(confidence_score), AVG(success_rate) FROM astrological_insights;
--
-- SELECT COUNT(*) FROM daily_astrological_conditions;
-- SELECT trade_date, daily_score, market_outlook FROM daily_astrological_conditions ORDER BY trade_date DESC LIMIT 10;
--
-- SELECT COUNT(*) FROM daily_trading_recommendations;
-- SELECT recommendation_date, symbol, recommendation_type, confidence FROM daily_trading_recommendations ORDER BY recommendation_date DESC, confidence DESC LIMIT 10;