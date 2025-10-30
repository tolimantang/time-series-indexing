-- Market Data Table for Asset Price Storage
-- Supports daily OHLCV data for causal analysis

CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(15,6),
    high_price DECIMAL(15,6),
    low_price DECIMAL(15,6),
    close_price DECIMAL(15,6),
    volume BIGINT,
    adjusted_close DECIMAL(15,6),
    source VARCHAR(50) DEFAULT 'unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(symbol, date)
);

-- Indexes for fast lookups
CREATE INDEX idx_market_data_symbol_date ON market_data(symbol, date);
CREATE INDEX idx_market_data_date_range ON market_data(date);
CREATE INDEX idx_market_data_symbol ON market_data(symbol);

-- Common asset symbols we'll support
-- Gold: GLD, GOLD, XAU
-- Silver: SLV, SILVER, XAG
-- Oil: USO, OIL, CL
-- SPX: SPY, SPX
-- etc.

COMMENT ON TABLE market_data IS 'Daily market data for asset price analysis';
COMMENT ON COLUMN market_data.symbol IS 'Asset symbol (e.g., GLD, SPY, BTC)';
COMMENT ON COLUMN market_data.date IS 'Trading date';
COMMENT ON COLUMN market_data.source IS 'Data provider (e.g., alpha_vantage, yahoo, polygon)';