-- Ground Truth Schema Definition
-- This file represents the CURRENT desired state of all tables
-- Use this as reference when creating migrations

-- Market Data Tables
-- ===================

CREATE TABLE market_data_intraday (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    interval_type VARCHAR(10) NOT NULL,
    open_price DECIMAL(12,6),
    high_price DECIMAL(12,6),
    low_price DECIMAL(12,6),
    close_price DECIMAL(12,6) NOT NULL,
    volume INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT market_data_intraday_unique UNIQUE(symbol, datetime, interval_type)
);

-- Astrological Data Tables
-- ========================

CREATE TABLE daily_planetary_positions (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    planet VARCHAR(20) NOT NULL,
    longitude DECIMAL(8,5) NOT NULL,
    latitude DECIMAL(8,5),
    distance DECIMAL(12,8),
    speed DECIMAL(8,5),
    zodiac_sign VARCHAR(20) NOT NULL,
    degree_in_sign DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT daily_planetary_positions_unique UNIQUE(trade_date, planet)
);

CREATE TABLE daily_planetary_aspects (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    planet1 VARCHAR(20) NOT NULL,
    planet2 VARCHAR(20) NOT NULL,
    aspect_type VARCHAR(20) NOT NULL,
    orb DECIMAL(5,2) NOT NULL,
    exactness DECIMAL(5,4),
    separating_angle DECIMAL(8,5),
    applying_separating VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT daily_planetary_aspects_unique UNIQUE(trade_date, planet1, planet2, aspect_type)
);

-- Lunar Pattern Analysis Tables
-- =============================

CREATE TABLE lunar_patterns (
    id SERIAL PRIMARY KEY,

    -- Core pattern identification
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL DEFAULT 'lunar_transit',
    timing_type VARCHAR(20) NOT NULL,

    -- Prediction and accuracy
    prediction VARCHAR(10) NOT NULL,
    accuracy_rate DECIMAL(5,3) NOT NULL,

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
    CONSTRAINT lunar_patterns_timing_type_check CHECK (timing_type IN ('same_day', 'next_day')),
    CONSTRAINT lunar_patterns_prediction_check CHECK (prediction IN ('up', 'down')),
    CONSTRAINT lunar_patterns_accuracy_rate_check CHECK (accuracy_rate >= 0 AND accuracy_rate <= 1),
    CONSTRAINT lunar_patterns_count_consistency_check CHECK (up_count + down_count = total_occurrences),
    CONSTRAINT lunar_patterns_unique_pattern UNIQUE(pattern_name, market_symbol, timing_type)
);

-- Insights and Recommendations Tables
-- ===================================

CREATE TABLE astrological_insights (
    id SERIAL PRIMARY KEY,
    insight_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    confidence_score DOUBLE PRECISION,
    success_rate DOUBLE PRECISION,
    avg_profit DOUBLE PRECISION,
    trade_count INTEGER,
    evidence JSONB,
    claude_analysis TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE daily_astrological_conditions (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,
    planetary_positions JSONB NOT NULL,
    major_aspects JSONB,
    lunar_phase_name VARCHAR(50),
    lunar_phase_angle DOUBLE PRECISION,
    significant_events TEXT[],
    daily_score DOUBLE PRECISION,
    market_outlook TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE daily_trading_recommendations (
    id SERIAL PRIMARY KEY,
    recommendation_date DATE NOT NULL,
    symbol VARCHAR(25) NOT NULL,
    recommendation_type VARCHAR(20) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    astrological_reasoning TEXT,
    supporting_insights INTEGER[],
    target_price DOUBLE PRECISION,
    stop_loss DOUBLE PRECISION,
    holding_period_days INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT daily_trading_recommendations_unique UNIQUE(recommendation_date, symbol, recommendation_type)
);

-- System Tables
-- =============

-- Flyway schema history (managed by Flyway, shown for reference)
-- CREATE TABLE flyway_schema_history (
--     installed_rank INTEGER NOT NULL,
--     version VARCHAR(50),
--     description VARCHAR(200) NOT NULL,
--     type VARCHAR(20) NOT NULL,
--     script VARCHAR(1000) NOT NULL,
--     checksum INTEGER,
--     installed_by VARCHAR(100) NOT NULL,
--     installed_on TIMESTAMP DEFAULT NOW(),
--     execution_time INTEGER NOT NULL,
--     success BOOLEAN NOT NULL,
--     CONSTRAINT flyway_schema_history_pk PRIMARY KEY (installed_rank)
-- );