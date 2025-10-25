-- Ground Truth Index Definitions
-- This file represents the CURRENT desired state of all indexes

-- Market Data Indexes
-- ===================

CREATE INDEX idx_market_data_intraday_symbol_datetime
    ON market_data_intraday(symbol, datetime);

CREATE INDEX idx_market_data_intraday_datetime
    ON market_data_intraday(datetime);

-- Astrological Data Indexes
-- =========================

CREATE INDEX idx_daily_planetary_positions_date_planet
    ON daily_planetary_positions(trade_date, planet);

CREATE INDEX idx_daily_planetary_positions_planet_sign
    ON daily_planetary_positions(planet, zodiac_sign);

CREATE INDEX idx_daily_planetary_aspects_date
    ON daily_planetary_aspects(trade_date);

CREATE INDEX idx_daily_planetary_aspects_planets
    ON daily_planetary_aspects(planet1, planet2);

CREATE INDEX idx_daily_planetary_aspects_type
    ON daily_planetary_aspects(aspect_type);

-- Lunar Pattern Indexes
-- =====================

CREATE INDEX idx_lunar_patterns_market_timing
    ON lunar_patterns(market_symbol, timing_type);

CREATE INDEX idx_lunar_patterns_accuracy
    ON lunar_patterns(accuracy_rate DESC);

CREATE INDEX idx_lunar_patterns_expected_return
    ON lunar_patterns(expected_return DESC);

CREATE INDEX idx_lunar_patterns_pattern_name
    ON lunar_patterns(pattern_name);

-- Insights and Recommendations Indexes
-- ====================================

CREATE INDEX idx_astrological_insights_category
    ON astrological_insights(category);

CREATE INDEX idx_astrological_insights_pattern
    ON astrological_insights(pattern_name);

CREATE INDEX idx_daily_astrological_conditions_date
    ON daily_astrological_conditions(trade_date);

CREATE INDEX idx_daily_trading_recommendations_date_symbol
    ON daily_trading_recommendations(recommendation_date, symbol);