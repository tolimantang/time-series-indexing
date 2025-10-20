-- Migration 002: Add market data tables for financial analysis
-- This adds structured market data storage for P&L calculations

-- Market data table for OHLCV data
CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(12,4) NOT NULL,
    high_price DECIMAL(12,4) NOT NULL,
    low_price DECIMAL(12,4) NOT NULL,
    close_price DECIMAL(12,4) NOT NULL,
    adjusted_close DECIMAL(12,4),
    volume BIGINT NOT NULL DEFAULT 0,
    daily_return DECIMAL(8,6), -- Pre-calculated for performance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, trade_date)
);

-- Market data performance indexes
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_date ON market_data(trade_date DESC);
CREATE INDEX idx_market_data_symbol_date ON market_data(symbol, trade_date DESC);

-- Trigger to update market_data updated_at
CREATE TRIGGER update_market_data_updated_at BEFORE UPDATE ON market_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate daily returns (if not pre-calculated)
CREATE OR REPLACE FUNCTION calculate_daily_return(
    p_symbol VARCHAR(10),
    p_date DATE
) RETURNS DECIMAL(8,6) AS $$
DECLARE
    current_price DECIMAL(12,4);
    previous_price DECIMAL(12,4);
    daily_return DECIMAL(8,6);
BEGIN
    -- Get current day's close price
    SELECT close_price INTO current_price
    FROM market_data
    WHERE symbol = p_symbol AND trade_date = p_date;

    -- Get previous trading day's close price
    SELECT close_price INTO previous_price
    FROM market_data
    WHERE symbol = p_symbol
      AND trade_date < p_date
    ORDER BY trade_date DESC
    LIMIT 1;

    -- Calculate return
    IF previous_price IS NOT NULL AND previous_price > 0 THEN
        daily_return := (current_price - previous_price) / previous_price;
    ELSE
        daily_return := NULL;
    END IF;

    RETURN daily_return;
END;
$$ LANGUAGE plpgsql;

-- View for market data with calculated returns
CREATE VIEW market_data_with_returns AS
SELECT
    md.*,
    LAG(close_price) OVER (PARTITION BY symbol ORDER BY trade_date) as prev_close,
    CASE
        WHEN LAG(close_price) OVER (PARTITION BY symbol ORDER BY trade_date) IS NOT NULL
        THEN (close_price - LAG(close_price) OVER (PARTITION BY symbol ORDER BY trade_date)) /
             LAG(close_price) OVER (PARTITION BY symbol ORDER BY trade_date)
        ELSE NULL
    END as calculated_daily_return
FROM market_data md;