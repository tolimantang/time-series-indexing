-- Astrological Insights Table
-- Stores pre-computed planetary aspect backtesting results
-- Similar to lunar_patterns but for planetary combinations (Jupiter/Mars, etc.)

CREATE TABLE IF NOT EXISTS astrological_insights (
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

    -- Performance metrics
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

    -- Pattern strength indicators
    accuracy_rate DECIMAL(5,4),          -- Overall pattern accuracy
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

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_astrological_insights_market_lookup
    ON astrological_insights(market_symbol, planet1, planet2, aspect_type);

CREATE INDEX IF NOT EXISTS idx_astrological_insights_performance
    ON astrological_insights(accuracy_rate DESC, avg_return_pct DESC);

CREATE INDEX IF NOT EXISTS idx_astrological_insights_phase
    ON astrological_insights(phase, win_rate DESC);

CREATE INDEX IF NOT EXISTS idx_astrological_insights_created
    ON astrological_insights(created_at DESC);

-- Comments
COMMENT ON TABLE astrological_insights IS 'Pre-computed planetary aspect backtesting results for trading recommendations';
COMMENT ON COLUMN astrological_insights.phase IS 'Trading phase: approaching (orb entry -> exact) or separating (exact -> orb exit)';
COMMENT ON COLUMN astrological_insights.pattern_name IS 'Descriptive name like "Jupiter-Mars Trine Approaching Phase"';
COMMENT ON COLUMN astrological_insights.accuracy_rate IS 'Percentage of profitable trades (0.0 to 1.0)';
COMMENT ON COLUMN astrological_insights.win_rate IS 'Same as accuracy_rate, kept for consistency with lunar_patterns';

-- Example usage query
/*
-- Get best performing Jupiter-Mars patterns for Platinum
SELECT
    pattern_name,
    phase,
    accuracy_rate,
    avg_return_pct,
    total_trades,
    avg_holding_days
FROM astrological_insights
WHERE market_symbol = 'PLATINUM_DAILY'
    AND planet1 = 'jupiter'
    AND planet2 = 'mars'
    AND accuracy_rate >= 0.65
ORDER BY avg_return_pct DESC, accuracy_rate DESC;
*/