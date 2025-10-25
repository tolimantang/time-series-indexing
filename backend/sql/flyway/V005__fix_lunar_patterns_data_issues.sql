-- Migration: Fix lunar patterns data issues
-- Created: 2025-10-25
-- Version: V005

-- This migration addresses data quality issues in the existing lunar_patterns table
-- before we can apply the clean schema (V004)

-- Step 1: Create a properly typed backup table
CREATE TABLE IF NOT EXISTS lunar_patterns_temp_backup AS
SELECT
    id,
    pattern_name,
    pattern_type,

    -- Clean up prediction field (convert bearish/bullish to down/up)
    CASE
        WHEN LOWER(prediction) IN ('bearish', 'bear', 'down', 'sell') THEN 'down'
        WHEN LOWER(prediction) IN ('bullish', 'bull', 'up', 'buy') THEN 'up'
        ELSE 'unknown'
    END as clean_prediction,

    -- Clean up accuracy_rate field (handle text values)
    CASE
        WHEN accuracy_rate ~ '^[0-9]*\.?[0-9]+$' THEN accuracy_rate::DECIMAL(5,3)
        WHEN LOWER(accuracy_rate) LIKE '%high%' THEN 0.800
        WHEN LOWER(accuracy_rate) LIKE '%medium%' THEN 0.650
        WHEN LOWER(accuracy_rate) LIKE '%low%' THEN 0.550
        ELSE 0.500
    END as clean_accuracy_rate,

    -- Ensure integer fields are properly typed
    COALESCE(total_occurrences, 0) as clean_total_occurrences,
    COALESCE(up_count, 0) as clean_up_count,
    COALESCE(down_count, 0) as clean_down_count,

    -- Ensure decimal fields are properly typed
    COALESCE(avg_up_move, 0) as clean_avg_up_move,
    COALESCE(avg_down_move, 0) as clean_avg_down_move,
    COALESCE(expected_return, 0) as clean_expected_return,

    -- Keep other fields as-is
    aspect_type,
    moon_sign,
    target_planet,
    target_sign,
    COALESCE(minimum_orb, 3.0) as clean_minimum_orb,
    market_symbol,
    analysis_period_start,
    analysis_period_end,
    created_at

FROM lunar_patterns
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lunar_patterns');

-- Step 2: Show data cleaning summary
DO $$
DECLARE
    original_count INTEGER;
    cleaned_count INTEGER;
    bad_predictions INTEGER;
    bad_accuracy_rates INTEGER;
BEGIN
    -- Count original records
    SELECT COUNT(*) INTO original_count FROM lunar_patterns WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lunar_patterns');

    -- Count cleaned records
    SELECT COUNT(*) INTO cleaned_count FROM lunar_patterns_temp_backup;

    -- Count records that needed prediction cleaning
    SELECT COUNT(*) INTO bad_predictions
    FROM lunar_patterns
    WHERE LOWER(prediction) NOT IN ('up', 'down')
    AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lunar_patterns');

    -- Count records that needed accuracy rate cleaning
    SELECT COUNT(*) INTO bad_accuracy_rates
    FROM lunar_patterns
    WHERE accuracy_rate !~ '^[0-9]*\.?[0-9]+$'
    AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lunar_patterns');

    RAISE NOTICE 'Data cleaning summary:';
    RAISE NOTICE '  - Original records: %', COALESCE(original_count, 0);
    RAISE NOTICE '  - Cleaned records: %', COALESCE(cleaned_count, 0);
    RAISE NOTICE '  - Fixed bad predictions: %', COALESCE(bad_predictions, 0);
    RAISE NOTICE '  - Fixed bad accuracy rates: %', COALESCE(bad_accuracy_rates, 0);
END $$;

-- Step 3: Replace the original table with cleaned data
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lunar_patterns') THEN
        DROP TABLE lunar_patterns;
        RAISE NOTICE 'Dropped original lunar_patterns table with dirty data';
    END IF;

    -- Rename backup to original name
    ALTER TABLE lunar_patterns_temp_backup RENAME TO lunar_patterns_backup_clean;
    RAISE NOTICE 'Created clean backup table: lunar_patterns_backup_clean';
END $$;