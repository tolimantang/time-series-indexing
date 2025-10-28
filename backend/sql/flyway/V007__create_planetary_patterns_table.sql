-- Create planetary_patterns table for planetary aspect backtesting results
-- Migration: V007
-- Date: 2024-10-28
-- Description: Create properly named planetary_patterns table, handle existing astrological_insights table

-- Note: V006 was removed, so no astrological_insights table to drop

-- Create planetary_patterns table with correct name and structure
CREATE TABLE IF NOT EXISTS planetary_patterns (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Market identification
    market_symbol VARCHAR(50) NOT NULL,  -- e.g., 'PLATINUM_DAILY', 'GOLD_DAILY'
    symbol VARCHAR(20) NOT NULL,         -- e.g., 'PL=F', 'GC=F'

    -- Planetary aspect identification
    planet1 VARCHAR(20) NOT NULL,        -- e.g., 'jupiter'
    planet2 VARCHAR(20) NOT NULL,        -- e.g., 'mars'
    aspect_type VARCHAR(20) NOT NULL,    -- e.g., 'trine', 'conjunction', 'square'

    -- Backtest configuration
    orb_size DECIMAL(4,2) NOT NULL,      -- e.g., 8.00 degrees
    start_date DATE NOT NULL,            -- Backtest period start
    end_date DATE NOT NULL,              -- Backtest period end

    -- Phase-specific results
    phase VARCHAR(20) NOT NULL,          -- 'approaching' or 'separating'

    -- Performance metrics (consistent with lunar_patterns structure)
    total_trades INTEGER NOT NULL,
    avg_return_pct DECIMAL(8,4),         -- Average return percentage
    win_rate DECIMAL(5,4),               -- Win rate (0.0 to 1.0)
    avg_holding_days DECIMAL(6,2),       -- Average holding period
    best_return_pct DECIMAL(8,4),        -- Best single trade return
    worst_return_pct DECIMAL(8,4),       -- Worst single trade return

    -- Statistical significance
    sharpe_ratio DECIMAL(6,4),           -- Risk-adjusted return
    max_drawdown_pct DECIMAL(8,4),       -- Maximum drawdown
    volatility_pct DECIMAL(8,4),         -- Return volatility

    -- Pattern strength indicators (consistent with lunar_patterns)
    accuracy_rate DECIMAL(5,4),          -- Overall pattern accuracy (same as win_rate)
    confidence_score DECIMAL(5,4),       -- Statistical confidence

    -- Metadata
    pattern_name VARCHAR(100),           -- Human-readable pattern description
    total_aspects_found INTEGER,         -- Number of aspect periods found
    execution_time_seconds DECIMAL(8,2), -- Backtest execution time

    -- Analysis metadata
    backtest_version VARCHAR(20) DEFAULT 'v1.0',
    notes TEXT,

    UNIQUE(market_symbol, planet1, planet2, aspect_type, phase, orb_size, start_date, end_date)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_planetary_patterns_market_lookup
    ON planetary_patterns(market_symbol, planet1, planet2, aspect_type);

CREATE INDEX IF NOT EXISTS idx_planetary_patterns_performance
    ON planetary_patterns(accuracy_rate DESC, avg_return_pct DESC);

CREATE INDEX IF NOT EXISTS idx_planetary_patterns_phase
    ON planetary_patterns(phase, win_rate DESC);

CREATE INDEX IF NOT EXISTS idx_planetary_patterns_created
    ON planetary_patterns(created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE planetary_patterns IS 'Pre-computed planetary aspect backtesting results for trading recommendations';
COMMENT ON COLUMN planetary_patterns.phase IS 'Trading phase: approaching (orb entry -> exact) or separating (exact -> orb exit)';
COMMENT ON COLUMN planetary_patterns.pattern_name IS 'Descriptive name like "Jupiter-Mars Trine Approaching Phase"';
COMMENT ON COLUMN planetary_patterns.accuracy_rate IS 'Percentage of profitable trades (0.0 to 1.0)';
COMMENT ON COLUMN planetary_patterns.win_rate IS 'Same as accuracy_rate, kept for consistency with lunar_patterns';
COMMENT ON COLUMN planetary_patterns.market_symbol IS 'Market identifier matching lunar_patterns format';
COMMENT ON COLUMN planetary_patterns.backtest_version IS 'Version of backtesting algorithm used';

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_planetary_patterns_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_planetary_patterns_updated_at
    BEFORE UPDATE ON planetary_patterns
    FOR EACH ROW EXECUTE FUNCTION update_planetary_patterns_updated_at();