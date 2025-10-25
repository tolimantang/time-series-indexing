-- Initial schema for time-series-indexing database
-- This represents the current state of the database before Flyway management

-- Market data tables
CREATE TABLE IF NOT EXISTS market_data_intraday (
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
    UNIQUE(symbol, datetime, interval_type)
);

CREATE INDEX IF NOT EXISTS idx_market_data_intraday_symbol_datetime ON market_data_intraday(symbol, datetime);
CREATE INDEX IF NOT EXISTS idx_market_data_intraday_datetime ON market_data_intraday(datetime);

-- Astrological data tables
CREATE TABLE IF NOT EXISTS daily_planetary_positions (
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
    UNIQUE(trade_date, planet)
);

CREATE INDEX IF NOT EXISTS idx_daily_planetary_positions_date_planet ON daily_planetary_positions(trade_date, planet);
CREATE INDEX IF NOT EXISTS idx_daily_planetary_positions_planet_sign ON daily_planetary_positions(planet, zodiac_sign);

CREATE TABLE IF NOT EXISTS daily_planetary_aspects (
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
    UNIQUE(trade_date, planet1, planet2, aspect_type)
);

CREATE INDEX IF NOT EXISTS idx_daily_planetary_aspects_date ON daily_planetary_aspects(trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_planetary_aspects_planets ON daily_planetary_aspects(planet1, planet2);
CREATE INDEX IF NOT EXISTS idx_daily_planetary_aspects_type ON daily_planetary_aspects(aspect_type);

-- Insights and recommendations tables
CREATE TABLE IF NOT EXISTS astrological_insights (
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

CREATE INDEX IF NOT EXISTS idx_astrological_insights_category ON astrological_insights(category);
CREATE INDEX IF NOT EXISTS idx_astrological_insights_pattern ON astrological_insights(pattern_name);

CREATE TABLE IF NOT EXISTS daily_astrological_conditions (
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

CREATE INDEX IF NOT EXISTS idx_daily_astrological_conditions_date ON daily_astrological_conditions(trade_date);

CREATE TABLE IF NOT EXISTS daily_trading_recommendations (
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
    UNIQUE(recommendation_date, symbol, recommendation_type)
);

CREATE INDEX IF NOT EXISTS idx_daily_trading_recommendations_date_symbol ON daily_trading_recommendations(recommendation_date, symbol);

-- Note: lunar_patterns table will be handled in V004 migration