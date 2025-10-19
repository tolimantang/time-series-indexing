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

-- Portfolio positions for tracking user investments
CREATE TABLE portfolio_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    entry_date DATE NOT NULL,
    exit_date DATE,
    entry_price DECIMAL(12,4) NOT NULL,
    exit_price DECIMAL(12,4),
    quantity DECIMAL(12,4) NOT NULL,
    position_type VARCHAR(10) NOT NULL CHECK (position_type IN ('long', 'short')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'partial')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market data performance indexes
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_date ON market_data(trade_date DESC);
CREATE INDEX idx_market_data_symbol_date ON market_data(symbol, trade_date DESC);

-- Portfolio indexes for P&L queries
CREATE INDEX idx_portfolio_user_id ON portfolio_positions(user_id);
CREATE INDEX idx_portfolio_symbol ON portfolio_positions(symbol);
CREATE INDEX idx_portfolio_dates ON portfolio_positions(entry_date, exit_date);
CREATE INDEX idx_portfolio_user_symbol ON portfolio_positions(user_id, symbol);

-- Trigger to update market_data updated_at
CREATE TRIGGER update_market_data_updated_at BEFORE UPDATE ON market_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update portfolio_positions updated_at
CREATE TRIGGER update_portfolio_positions_updated_at BEFORE UPDATE ON portfolio_positions
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

-- View for easy P&L calculations
CREATE VIEW portfolio_pnl AS
SELECT
    pp.id,
    pp.user_id,
    pp.symbol,
    pp.entry_date,
    pp.exit_date,
    pp.entry_price,
    pp.exit_price,
    pp.quantity,
    pp.position_type,
    pp.status,
    -- Current market price for open positions
    COALESCE(pp.exit_price, md_current.close_price) as current_price,
    -- P&L calculations
    CASE
        WHEN pp.position_type = 'long' THEN
            (COALESCE(pp.exit_price, md_current.close_price) - pp.entry_price) * pp.quantity
        WHEN pp.position_type = 'short' THEN
            (pp.entry_price - COALESCE(pp.exit_price, md_current.close_price)) * pp.quantity
    END as pnl_amount,
    -- P&L percentage
    CASE
        WHEN pp.position_type = 'long' THEN
            ((COALESCE(pp.exit_price, md_current.close_price) - pp.entry_price) / pp.entry_price) * 100
        WHEN pp.position_type = 'short' THEN
            ((pp.entry_price - COALESCE(pp.exit_price, md_current.close_price)) / pp.entry_price) * 100
    END as pnl_percentage
FROM portfolio_positions pp
LEFT JOIN LATERAL (
    SELECT close_price
    FROM market_data md
    WHERE md.symbol = pp.symbol
    ORDER BY md.trade_date DESC
    LIMIT 1
) md_current ON true;