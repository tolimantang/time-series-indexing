-- Migration 003: Extend symbol column length for commodities and longer symbols
-- This increases symbol VARCHAR length from 10 to 25 characters to support:
-- - Oil futures: CRUDE_OIL_WTI, CRUDE_OIL_BRENT
-- - Other commodities: GOLD, SILVER, etc.
-- - Future longer symbol names

-- Extend symbol column in market_data table
ALTER TABLE market_data ALTER COLUMN symbol TYPE VARCHAR(25);

-- Update the function parameter to match new length
CREATE OR REPLACE FUNCTION calculate_daily_return(
    p_symbol VARCHAR(25),  -- Updated from VARCHAR(10)
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

-- Add comment for documentation
COMMENT ON COLUMN market_data.symbol IS 'Symbol identifier, supports up to 25 characters for commodities and longer symbols';