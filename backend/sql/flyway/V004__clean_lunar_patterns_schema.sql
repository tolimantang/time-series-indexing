-- Migration: Clean up lunar_patterns table schema
-- Purpose: Standardize lunar pattern storage with clean timing separation
-- Date: 2025-10-25

-- First, backup existing data and drop the messy table
-- (We'll recreate it with a clean schema)

-- Create backup table
CREATE TABLE IF NOT EXISTS lunar_patterns_backup AS
SELECT * FROM lunar_patterns;

-- Drop existing table with all the inconsistent columns
DROP TABLE IF EXISTS lunar_patterns;

-- Create new clean lunar_patterns table
CREATE TABLE lunar_patterns (
    id SERIAL PRIMARY KEY,

    -- Core pattern identification
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL DEFAULT 'lunar_transit',
    timing_type VARCHAR(20) NOT NULL CHECK (timing_type IN ('same_day', 'next_day')),

    -- Prediction and accuracy
    prediction VARCHAR(10) NOT NULL CHECK (prediction IN ('up', 'down')),
    accuracy_rate DECIMAL(5,3) NOT NULL CHECK (accuracy_rate >= 0 AND accuracy_rate <= 1),

    -- Occurrence statistics
    total_occurrences INTEGER NOT NULL DEFAULT 0,
    up_count INTEGER NOT NULL DEFAULT 0,
    down_count INTEGER NOT NULL DEFAULT 0,

    -- Price movement statistics
    avg_up_move DECIMAL(8,4) DEFAULT 0,
    avg_down_move DECIMAL(8,4) DEFAULT 0,
    expected_return DECIMAL(8,4) DEFAULT 0,

    -- Astrological context
    aspect_type VARCHAR(50),
    moon_sign VARCHAR(20),
    target_planet VARCHAR(20),
    target_sign VARCHAR(20),
    minimum_orb DECIMAL(4,2) DEFAULT 3.0,

    -- Market and analysis context
    market_symbol VARCHAR(50) NOT NULL,
    analysis_period_start DATE,
    analysis_period_end DATE,

    -- Quality metrics
    accuracy_rank INTEGER,
    return_rank INTEGER,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(pattern_name, market_symbol, timing_type),
    CHECK (up_count + down_count = total_occurrences)
);

-- Create indexes for common queries
CREATE INDEX idx_lunar_patterns_market_timing ON lunar_patterns(market_symbol, timing_type);
CREATE INDEX idx_lunar_patterns_accuracy ON lunar_patterns(accuracy_rate DESC);
CREATE INDEX idx_lunar_patterns_expected_return ON lunar_patterns(expected_return DESC);
CREATE INDEX idx_lunar_patterns_pattern_name ON lunar_patterns(pattern_name);
CREATE INDEX idx_lunar_patterns_aspect_planet ON lunar_patterns(aspect_type, target_planet, target_sign);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_lunar_patterns_updated_at
    BEFORE UPDATE ON lunar_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Migrate clean data from backup (only the good patterns)
INSERT INTO lunar_patterns (
    pattern_name,
    pattern_type,
    timing_type,
    prediction,
    accuracy_rate,
    total_occurrences,
    up_count,
    down_count,
    avg_up_move,
    avg_down_move,
    expected_return,
    aspect_type,
    moon_sign,
    target_planet,
    target_sign,
    minimum_orb,
    market_symbol,
    analysis_period_start,
    analysis_period_end,
    created_at
)
SELECT
    pattern_name,
    'lunar_transit' as pattern_type,
    CASE
        WHEN pattern_type LIKE '%same_day%' THEN 'same_day'
        ELSE 'next_day'
    END as timing_type,
    LOWER(prediction) as prediction,
    accuracy_rate,
    total_occurrences,
    up_count,
    down_count,
    COALESCE(avg_up_move, 0) as avg_up_move,
    COALESCE(avg_down_move, 0) as avg_down_move,
    COALESCE(expected_return, 0) as expected_return,
    aspect_type,
    moon_sign,
    target_planet,
    target_sign,
    COALESCE(minimum_orb, 3.0) as minimum_orb,
    market_symbol,
    analysis_period_start,
    analysis_period_end,
    created_at
FROM lunar_patterns_backup
WHERE
    -- Only migrate clean data with proper values
    pattern_name IS NOT NULL
    AND prediction IS NOT NULL
    AND accuracy_rate IS NOT NULL
    AND total_occurrences > 0
    AND market_symbol IS NOT NULL
    -- Filter out obviously broken records
    AND accuracy_rate <= 1.0
    AND total_occurrences >= up_count + down_count;

-- Create a view for easy querying of best patterns
CREATE OR REPLACE VIEW best_lunar_patterns AS
SELECT
    pattern_name,
    timing_type,
    prediction,
    accuracy_rate,
    expected_return,
    total_occurrences,
    market_symbol,
    aspect_type,
    moon_sign,
    target_planet,
    target_sign,
    ROW_NUMBER() OVER (
        PARTITION BY market_symbol, timing_type
        ORDER BY accuracy_rate DESC, expected_return DESC
    ) as rank
FROM lunar_patterns
WHERE accuracy_rate >= 0.65  -- Only show patterns with >= 65% accuracy
ORDER BY market_symbol, timing_type, accuracy_rate DESC;

-- Add comments for documentation
COMMENT ON TABLE lunar_patterns IS 'Stores lunar astrological patterns and their market predictions';
COMMENT ON COLUMN lunar_patterns.timing_type IS 'Whether pattern predicts same_day (open to close) or next_day (close to next close) movement';
COMMENT ON COLUMN lunar_patterns.expected_return IS 'Expected return percentage based on accuracy * average move';
COMMENT ON VIEW best_lunar_patterns IS 'Shows only high-accuracy patterns ranked by performance';

-- Clean up backup table (optional - keep for safety)
-- DROP TABLE lunar_patterns_backup;

-- Show migration summary
DO $$
DECLARE
    migrated_count INTEGER;
    backup_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO migrated_count FROM lunar_patterns;
    SELECT COUNT(*) INTO backup_count FROM lunar_patterns_backup;

    RAISE NOTICE 'Migration completed:';
    RAISE NOTICE '  - Backup table rows: %', backup_count;
    RAISE NOTICE '  - Migrated clean rows: %', migrated_count;
    RAISE NOTICE '  - Filtered out rows: %', backup_count - migrated_count;
END $$;