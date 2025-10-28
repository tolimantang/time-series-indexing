-- Add ingress support to planetary_patterns table
-- Migration: V008
-- Date: 2025-10-28
-- Description: Extend planetary_patterns table to support planetary ingress backtesting

-- Add new columns for ingress functionality
ALTER TABLE planetary_patterns
ADD COLUMN IF NOT EXISTS ingress_date DATE,
ADD COLUMN IF NOT EXISTS zodiac_sign VARCHAR(20);

-- Make planet2 nullable to support single-planet ingress patterns
ALTER TABLE planetary_patterns
ALTER COLUMN planet2 DROP NOT NULL;

-- Drop the existing unique constraint
ALTER TABLE planetary_patterns
DROP CONSTRAINT IF EXISTS planetary_patterns_market_symbol_planet1_planet2_aspect_type_phase_key;

-- Add new unique constraint that handles both aspect and ingress patterns
-- For aspects: (market_symbol, planet1, planet2, aspect_type, phase, orb_size, start_date, end_date)
-- For ingress: (market_symbol, planet1, zodiac_sign, start_date, end_date) where planet2=NULL, aspect_type='ingress'
ALTER TABLE planetary_patterns
ADD CONSTRAINT planetary_patterns_unique_key UNIQUE NULLS NOT DISTINCT (
    market_symbol,
    planet1,
    planet2,
    aspect_type,
    phase,
    zodiac_sign,
    orb_size,
    start_date,
    end_date
);

-- Create additional indexes for ingress queries
CREATE INDEX IF NOT EXISTS idx_planetary_patterns_ingress_lookup
    ON planetary_patterns(market_symbol, planet1, zodiac_sign, ingress_date)
    WHERE aspect_type = 'ingress';

CREATE INDEX IF NOT EXISTS idx_planetary_patterns_zodiac_performance
    ON planetary_patterns(zodiac_sign, avg_return_pct DESC)
    WHERE aspect_type = 'ingress';

-- Add comments for the new columns
COMMENT ON COLUMN planetary_patterns.ingress_date IS 'Date when planet ingresses into zodiac_sign (for ingress backtests only)';
COMMENT ON COLUMN planetary_patterns.zodiac_sign IS 'Zodiac sign for ingress backtests (e.g., cancer, leo, virgo)';
COMMENT ON COLUMN planetary_patterns.planet2 IS 'Second planet for aspect backtests, NULL for ingress backtests';

-- Update table comment
COMMENT ON TABLE planetary_patterns IS 'Pre-computed planetary aspect and ingress backtesting results for trading recommendations';