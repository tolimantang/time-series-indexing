-- =====================================================================================
-- Enhanced Astrological Analysis Schema
-- =====================================================================================
-- This migration creates a comprehensive normalized schema for astrological analysis
-- with support for planetary positions, aspects, patterns, and harmonic analysis.
--
-- Tables Created:
-- 1. daily_astrological_conditions (modified)
-- 2. daily_planetary_positions (new)
-- 3. daily_planetary_aspects (new)
-- 4. daily_harmonic_analysis (new)
-- 5. daily_astrological_patterns (new)
-- 6. planets (reference table)
-- 7. aspect_types (reference table)
-- =====================================================================================

BEGIN;

-- =====================================================================================
-- REFERENCE TABLES
-- =====================================================================================

-- Planets reference table
CREATE TABLE IF NOT EXISTS planets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL,
    symbol VARCHAR(10),
    planet_type VARCHAR(20) NOT NULL,  -- 'inner', 'outer', 'luminaries'
    astrological_significance TEXT,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert standard planets
INSERT INTO planets (name, symbol, planet_type, display_order, astrological_significance) VALUES
('Sun', '☉', 'luminaries', 1, 'Ego, vitality, core identity'),
('Moon', '☽', 'luminaries', 2, 'Emotions, instincts, subconscious'),
('Mercury', '☿', 'inner', 3, 'Communication, thinking, commerce'),
('Venus', '♀', 'inner', 4, 'Love, beauty, values, money'),
('Mars', '♂', 'inner', 5, 'Action, energy, conflict, desire'),
('Jupiter', '♃', 'outer', 6, 'Expansion, optimism, philosophy, luck'),
('Saturn', '♄', 'outer', 7, 'Structure, discipline, limitation, responsibility'),
('Uranus', '♅', 'outer', 8, 'Innovation, rebellion, sudden change'),
('Neptune', '♆', 'outer', 9, 'Spirituality, illusion, imagination'),
('Pluto', '♇', 'outer', 10, 'Transformation, power, regeneration')
ON CONFLICT (name) DO NOTHING;

-- Aspect types reference table
CREATE TABLE IF NOT EXISTS aspect_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL,
    angle DOUBLE PRECISION NOT NULL,
    default_orb DOUBLE PRECISION NOT NULL,
    harmony_type VARCHAR(20) NOT NULL, -- 'harmonious', 'challenging', 'neutral'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO aspect_types (name, angle, default_orb, harmony_type, description) VALUES
('conjunction', 0, 8, 'neutral', 'Planets in the same position - intense, focused energy'),
('sextile', 60, 4, 'harmonious', 'Opportunity, ease, cooperative energy'),
('square', 90, 6, 'challenging', 'Tension, conflict, dynamic action required'),
('trine', 120, 6, 'harmonious', 'Flow, natural talent, ease of expression'),
('opposition', 180, 8, 'challenging', 'Polarity, awareness, need for balance')
ON CONFLICT (name) DO NOTHING;

-- =====================================================================================
-- CORE TABLES
-- =====================================================================================

-- Modify existing daily_astrological_conditions table
-- Remove major_aspects JSONB column as it will be normalized
ALTER TABLE daily_astrological_conditions
DROP COLUMN IF EXISTS major_aspects;

-- Add any missing columns
ALTER TABLE daily_astrological_conditions
ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY;

-- Ensure we have proper indexes
CREATE INDEX IF NOT EXISTS idx_conditions_date ON daily_astrological_conditions(trade_date);

-- =====================================================================================
-- NORMALIZED PLANETARY POSITIONS
-- =====================================================================================

CREATE TABLE IF NOT EXISTS daily_planetary_positions (
    id SERIAL PRIMARY KEY,
    conditions_id INTEGER NOT NULL REFERENCES daily_astrological_conditions(id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,  -- Denormalized for fast queries without JOIN

    -- Planet identification
    planet VARCHAR(20) NOT NULL REFERENCES planets(name),

    -- Position data
    longitude DOUBLE PRECISION NOT NULL,           -- 0-360 degrees
    latitude DOUBLE PRECISION DEFAULT 0,           -- Usually small for planets
    zodiac_sign VARCHAR(15) NOT NULL,              -- 'Aries', 'Taurus', etc.
    degree_in_sign DOUBLE PRECISION NOT NULL,      -- 0-30 degrees within sign

    -- Movement data
    is_retrograde BOOLEAN DEFAULT FALSE,
    daily_motion DOUBLE PRECISION,                 -- degrees per day (future enhancement)

    -- House positions (future enhancement)
    house_number INTEGER,                          -- 1-12 houses

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_planet_date UNIQUE (trade_date, planet),
    CONSTRAINT valid_longitude CHECK (longitude >= 0 AND longitude < 360),
    CONSTRAINT valid_degree_in_sign CHECK (degree_in_sign >= 0 AND degree_in_sign < 30),
    CONSTRAINT valid_zodiac_sign CHECK (zodiac_sign IN (
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ))
);

-- Indexes for planetary positions
CREATE INDEX idx_positions_planet_date ON daily_planetary_positions(planet, trade_date);
CREATE INDEX idx_positions_sign_date ON daily_planetary_positions(zodiac_sign, trade_date);
CREATE INDEX idx_positions_planet_sign ON daily_planetary_positions(planet, zodiac_sign);
CREATE INDEX idx_positions_date ON daily_planetary_positions(trade_date);
CREATE INDEX idx_positions_retrograde ON daily_planetary_positions(planet, trade_date)
    WHERE is_retrograde = true;

-- Specialized indexes for important planets
CREATE INDEX idx_positions_jupiter ON daily_planetary_positions(zodiac_sign, trade_date)
    WHERE planet = 'Jupiter';
CREATE INDEX idx_positions_saturn ON daily_planetary_positions(zodiac_sign, trade_date)
    WHERE planet = 'Saturn';
CREATE INDEX idx_positions_mars ON daily_planetary_positions(zodiac_sign, trade_date)
    WHERE planet = 'Mars';

-- =====================================================================================
-- NORMALIZED PLANETARY ASPECTS
-- =====================================================================================

CREATE TABLE IF NOT EXISTS daily_planetary_aspects (
    id SERIAL PRIMARY KEY,
    conditions_id INTEGER NOT NULL REFERENCES daily_astrological_conditions(id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,  -- Denormalized for fast queries without JOIN

    -- Planet information (alphabetically ordered to avoid duplicates)
    planet1 VARCHAR(20) NOT NULL REFERENCES planets(name),
    planet2 VARCHAR(20) NOT NULL REFERENCES planets(name),

    -- Aspect details
    aspect_type VARCHAR(20) NOT NULL REFERENCES aspect_types(name),
    orb DOUBLE PRECISION NOT NULL,                 -- Deviation from exact aspect
    separating_angle DOUBLE PRECISION NOT NULL,    -- Actual angular separation

    -- Aspect quality indicators
    is_exact BOOLEAN DEFAULT FALSE,                -- orb < 1 degree
    is_tight BOOLEAN DEFAULT FALSE,                -- orb < 3 degrees
    is_applying BOOLEAN,                           -- Aspect getting tighter (future enhancement)

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_aspect_per_date UNIQUE (trade_date, planet1, planet2, aspect_type),
    CONSTRAINT planet_order_check CHECK (planet1 < planet2),  -- Alphabetical ordering
    CONSTRAINT valid_orb CHECK (orb >= 0 AND orb <= 15),
    CONSTRAINT valid_separating_angle CHECK (separating_angle >= 0 AND separating_angle <= 180)
);

-- Indexes for aspects
CREATE INDEX idx_aspects_planets_type ON daily_planetary_aspects(planet1, planet2, aspect_type);
CREATE INDEX idx_aspects_type_date ON daily_planetary_aspects(aspect_type, trade_date);
CREATE INDEX idx_aspects_planet1_date ON daily_planetary_aspects(planet1, trade_date);
CREATE INDEX idx_aspects_planet2_date ON daily_planetary_aspects(planet2, trade_date);
CREATE INDEX idx_aspects_date ON daily_planetary_aspects(trade_date);

-- Quality-based indexes
CREATE INDEX idx_aspects_exact ON daily_planetary_aspects(trade_date) WHERE is_exact = true;
CREATE INDEX idx_aspects_tight ON daily_planetary_aspects(trade_date) WHERE is_tight = true;
CREATE INDEX idx_aspects_orb ON daily_planetary_aspects(orb, trade_date);

-- Planet-specific indexes for common queries
CREATE INDEX idx_aspects_jupiter_type_date ON daily_planetary_aspects(aspect_type, trade_date)
    WHERE planet1 = 'Jupiter' OR planet2 = 'Jupiter';
CREATE INDEX idx_aspects_mars_type_date ON daily_planetary_aspects(aspect_type, trade_date)
    WHERE planet1 = 'Mars' OR planet2 = 'Mars';
CREATE INDEX idx_aspects_saturn_type_date ON daily_planetary_aspects(aspect_type, trade_date)
    WHERE planet1 = 'Saturn' OR planet2 = 'Saturn';

-- =====================================================================================
-- HARMONIC ANALYSIS TABLE
-- =====================================================================================

CREATE TABLE IF NOT EXISTS daily_harmonic_analysis (
    id SERIAL PRIMARY KEY,
    conditions_id INTEGER NOT NULL REFERENCES daily_astrological_conditions(id) ON DELETE CASCADE,
    trade_date DATE NOT NULL UNIQUE,

    -- Overall aspect metrics
    total_aspects INTEGER NOT NULL DEFAULT 0,
    harmonious_aspects INTEGER NOT NULL DEFAULT 0,      -- trines, sextiles
    challenging_aspects INTEGER NOT NULL DEFAULT 0,     -- squares, oppositions
    neutral_aspects INTEGER NOT NULL DEFAULT 0,         -- conjunctions

    -- Calculated ratios (0.0 to 1.0)
    harmony_ratio DOUBLE PRECISION DEFAULT 0,           -- harmonious / total
    tension_ratio DOUBLE PRECISION DEFAULT 0,           -- challenging / total
    overall_harmony_score INTEGER DEFAULT 50,           -- 1-100 composite score

    -- Elemental distribution (planets in each element)
    fire_planets INTEGER DEFAULT 0,          -- Aries, Leo, Sagittarius
    earth_planets INTEGER DEFAULT 0,         -- Taurus, Virgo, Capricorn
    air_planets INTEGER DEFAULT 0,           -- Gemini, Libra, Aquarius
    water_planets INTEGER DEFAULT 0,         -- Cancer, Scorpio, Pisces
    elemental_balance_score DOUBLE PRECISION DEFAULT 0, -- How balanced the elements are (0-1)

    -- Modal distribution (cardinal, fixed, mutable)
    cardinal_planets INTEGER DEFAULT 0,      -- Aries, Cancer, Libra, Capricorn
    fixed_planets INTEGER DEFAULT 0,         -- Taurus, Leo, Scorpio, Aquarius
    mutable_planets INTEGER DEFAULT 0,       -- Gemini, Virgo, Sagittarius, Pisces
    modal_balance_score DOUBLE PRECISION DEFAULT 0,

    -- Pattern indicators (boolean flags for quick filtering)
    has_grand_trine BOOLEAN DEFAULT FALSE,
    has_t_square BOOLEAN DEFAULT FALSE,
    has_grand_cross BOOLEAN DEFAULT FALSE,
    has_stellium BOOLEAN DEFAULT FALSE,
    has_yod BOOLEAN DEFAULT FALSE,

    -- Planetary emphasis
    outer_planet_aspects INTEGER DEFAULT 0,   -- Aspects involving Jupiter, Saturn, Uranus, Neptune, Pluto
    inner_planet_aspects INTEGER DEFAULT 0,   -- Aspects involving Sun, Moon, Mercury, Venus, Mars
    generational_emphasis_score DOUBLE PRECISION DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_harmony_score CHECK (overall_harmony_score >= 0 AND overall_harmony_score <= 100),
    CONSTRAINT valid_ratios CHECK (
        harmony_ratio >= 0 AND harmony_ratio <= 1 AND
        tension_ratio >= 0 AND tension_ratio <= 1 AND
        elemental_balance_score >= 0 AND elemental_balance_score <= 1 AND
        modal_balance_score >= 0 AND modal_balance_score <= 1
    )
);

-- Indexes for harmonic analysis
CREATE INDEX idx_harmonic_date ON daily_harmonic_analysis(trade_date);
CREATE INDEX idx_harmonic_harmony_score ON daily_harmonic_analysis(overall_harmony_score DESC, trade_date);
CREATE INDEX idx_harmonic_balance ON daily_harmonic_analysis(elemental_balance_score DESC, trade_date);
CREATE INDEX idx_harmonic_patterns ON daily_harmonic_analysis(trade_date)
    WHERE has_grand_trine = true OR has_t_square = true OR has_grand_cross = true;

-- =====================================================================================
-- ASTROLOGICAL PATTERNS TABLE
-- =====================================================================================

CREATE TABLE IF NOT EXISTS daily_astrological_patterns (
    id SERIAL PRIMARY KEY,
    conditions_id INTEGER NOT NULL REFERENCES daily_astrological_conditions(id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,

    -- Pattern identification
    pattern_type VARCHAR(30) NOT NULL,  -- 'grand_trine', 't_square', 'grand_cross', 'stellium', 'yod'
    pattern_subtype VARCHAR(50),        -- 'fire_grand_trine', 'cardinal_t_square', 'outer_planet_stellium'

    -- Involved planets (stored as arrays for easy querying)
    primary_planets TEXT[] NOT NULL,    -- Core planets forming the pattern
    supporting_planets TEXT[],          -- Additional planets strengthening pattern

    -- Pattern strength and quality
    orb_tightness DOUBLE PRECISION,     -- Average orb of aspects in pattern
    pattern_strength INTEGER CHECK (pattern_strength >= 1 AND pattern_strength <= 10), -- 1-10 strength rating
    is_exact BOOLEAN DEFAULT FALSE,     -- All aspects < 2° orb
    geometric_precision DOUBLE PRECISION, -- How close to perfect geometry (0-1)

    -- Astrological classification
    element VARCHAR(10),                -- 'fire', 'earth', 'air', 'water' for elemental patterns
    modality VARCHAR(10),               -- 'cardinal', 'fixed', 'mutable'
    pattern_quality VARCHAR(20),        -- 'harmonious', 'challenging', 'mixed', 'transformative'

    -- Interpretive information
    pattern_meaning TEXT,               -- Brief astrological interpretation
    market_significance TEXT,           -- Potential trading/market implications

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_element CHECK (element IS NULL OR element IN ('fire', 'earth', 'air', 'water')),
    CONSTRAINT valid_modality CHECK (modality IS NULL OR modality IN ('cardinal', 'fixed', 'mutable')),
    CONSTRAINT valid_pattern_type CHECK (pattern_type IN (
        'grand_trine', 't_square', 'grand_cross', 'stellium', 'yod', 'grand_sextile',
        'mystic_rectangle', 'kite', 'cradle', 'locomotive'
    ))
);

-- Indexes for patterns
CREATE INDEX idx_patterns_type_date ON daily_astrological_patterns(pattern_type, trade_date);
CREATE INDEX idx_patterns_element_date ON daily_astrological_patterns(element, trade_date);
CREATE INDEX idx_patterns_modality_date ON daily_astrological_patterns(modality, trade_date);
CREATE INDEX idx_patterns_strength ON daily_astrological_patterns(pattern_strength DESC, trade_date);
CREATE INDEX idx_patterns_planets ON daily_astrological_patterns USING GIN (primary_planets);

-- =====================================================================================
-- UTILITY FUNCTIONS
-- =====================================================================================

-- Function to calculate elemental balance score
CREATE OR REPLACE FUNCTION calculate_elemental_balance(
    fire_count INTEGER,
    earth_count INTEGER,
    air_count INTEGER,
    water_count INTEGER
) RETURNS DOUBLE PRECISION AS $$
DECLARE
    total_planets INTEGER;
    expected_per_element DOUBLE PRECISION;
    variance DOUBLE PRECISION;
    max_variance DOUBLE PRECISION;
BEGIN
    total_planets := fire_count + earth_count + air_count + water_count;

    IF total_planets = 0 THEN
        RETURN 0.0;
    END IF;

    expected_per_element := total_planets / 4.0;

    -- Calculate variance from perfect balance
    variance := (
        POWER(fire_count - expected_per_element, 2) +
        POWER(earth_count - expected_per_element, 2) +
        POWER(air_count - expected_per_element, 2) +
        POWER(water_count - expected_per_element, 2)
    ) / 4.0;

    -- Maximum possible variance (all planets in one element)
    max_variance := POWER(total_planets - expected_per_element, 2) / 4.0 * 3 + POWER(expected_per_element, 2) / 4.0;

    -- Return balance score (1.0 = perfect balance, 0.0 = maximum imbalance)
    RETURN 1.0 - (variance / max_variance);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to get element for zodiac sign
CREATE OR REPLACE FUNCTION get_zodiac_element(sign VARCHAR(15))
RETURNS VARCHAR(10) AS $$
BEGIN
    RETURN CASE sign
        WHEN 'Aries' THEN 'fire'
        WHEN 'Leo' THEN 'fire'
        WHEN 'Sagittarius' THEN 'fire'
        WHEN 'Taurus' THEN 'earth'
        WHEN 'Virgo' THEN 'earth'
        WHEN 'Capricorn' THEN 'earth'
        WHEN 'Gemini' THEN 'air'
        WHEN 'Libra' THEN 'air'
        WHEN 'Aquarius' THEN 'air'
        WHEN 'Cancer' THEN 'water'
        WHEN 'Scorpio' THEN 'water'
        WHEN 'Pisces' THEN 'water'
        ELSE NULL
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to get modality for zodiac sign
CREATE OR REPLACE FUNCTION get_zodiac_modality(sign VARCHAR(15))
RETURNS VARCHAR(10) AS $$
BEGIN
    RETURN CASE sign
        WHEN 'Aries' THEN 'cardinal'
        WHEN 'Cancer' THEN 'cardinal'
        WHEN 'Libra' THEN 'cardinal'
        WHEN 'Capricorn' THEN 'cardinal'
        WHEN 'Taurus' THEN 'fixed'
        WHEN 'Leo' THEN 'fixed'
        WHEN 'Scorpio' THEN 'fixed'
        WHEN 'Aquarius' THEN 'fixed'
        WHEN 'Gemini' THEN 'mutable'
        WHEN 'Virgo' THEN 'mutable'
        WHEN 'Sagittarius' THEN 'mutable'
        WHEN 'Pisces' THEN 'mutable'
        ELSE NULL
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMIT;

-- =====================================================================================
-- VERIFICATION QUERIES
-- =====================================================================================

-- Verify table creation
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE tablename IN (
    'planets',
    'aspect_types',
    'daily_astrological_conditions',
    'daily_planetary_positions',
    'daily_planetary_aspects',
    'daily_harmonic_analysis',
    'daily_astrological_patterns'
)
ORDER BY tablename;

-- Verify reference data
SELECT 'Planets' as table_name, COUNT(*) as record_count FROM planets
UNION ALL
SELECT 'Aspect Types' as table_name, COUNT(*) as record_count FROM aspect_types;