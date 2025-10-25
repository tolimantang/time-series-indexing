-- Ground Truth View Definitions
-- This file represents the CURRENT desired state of all views

-- Best Lunar Patterns View
-- ========================

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

COMMENT ON VIEW best_lunar_patterns IS 'Shows only high-accuracy patterns ranked by performance';

-- Daily Market Overview View
-- ==========================

CREATE OR REPLACE VIEW daily_market_overview AS
SELECT
    c.trade_date,
    c.lunar_phase_name,
    c.daily_score,
    c.market_outlook,
    COUNT(r.id) as total_recommendations,
    COUNT(CASE WHEN r.recommendation_type = 'BUY' THEN 1 END) as buy_recommendations,
    COUNT(CASE WHEN r.recommendation_type = 'SELL' THEN 1 END) as sell_recommendations,
    AVG(r.confidence) as avg_confidence
FROM daily_astrological_conditions c
LEFT JOIN daily_trading_recommendations r ON c.trade_date = r.recommendation_date
GROUP BY c.trade_date, c.lunar_phase_name, c.daily_score, c.market_outlook
ORDER BY c.trade_date DESC;

COMMENT ON VIEW daily_market_overview IS 'Daily overview combining astrological conditions and trading recommendations';

-- Pattern Performance Summary View
-- ================================

CREATE OR REPLACE VIEW pattern_performance_summary AS
SELECT
    pattern_type,
    timing_type,
    COUNT(*) as pattern_count,
    AVG(accuracy_rate) as avg_accuracy,
    AVG(expected_return) as avg_expected_return,
    AVG(total_occurrences) as avg_occurrences,
    MIN(accuracy_rate) as min_accuracy,
    MAX(accuracy_rate) as max_accuracy
FROM lunar_patterns
GROUP BY pattern_type, timing_type
ORDER BY avg_accuracy DESC, avg_expected_return DESC;

COMMENT ON VIEW pattern_performance_summary IS 'Summary statistics for different pattern types and timing combinations';