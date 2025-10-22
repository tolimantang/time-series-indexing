# Astrological Analysis Data Model

## Overview

This document describes the comprehensive normalized database schema for astrological analysis, designed to support efficient querying of planetary positions, aspects, patterns, and harmonic analysis for trading insights.

## Architecture

The schema follows a **normalized approach** with **denormalized date fields** for query performance. It consists of:

1. **Core Tables**: Store daily astrological conditions and references
2. **Normalized Tables**: Planetary positions and aspects broken down for efficient querying
3. **Analysis Tables**: Pre-calculated harmonic analysis and pattern detection
4. **Reference Tables**: Standardized planet and aspect type data

## Table Structure

### 1. Reference Tables

#### `planets`
Standardizes planet names and metadata.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `name` | VARCHAR(20) | Planet name (e.g., 'Jupiter', 'Mars') |
| `symbol` | VARCHAR(10) | Unicode symbol (e.g., '♃', '♂') |
| `planet_type` | VARCHAR(20) | 'inner', 'outer', 'luminaries' |
| `astrological_significance` | TEXT | Brief meaning description |
| `display_order` | INTEGER | Order for UI display |

#### `aspect_types`
Defines astrological aspects and their properties.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `name` | VARCHAR(20) | Aspect name (e.g., 'trine', 'square') |
| `angle` | DOUBLE PRECISION | Exact angle in degrees |
| `default_orb` | DOUBLE PRECISION | Standard orb allowance |
| `harmony_type` | VARCHAR(20) | 'harmonious', 'challenging', 'neutral' |
| `description` | TEXT | Astrological meaning |

### 2. Core Tables

#### `daily_astrological_conditions`
Main table linking all daily astrological data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `trade_date` | DATE | Business date (UNIQUE) |
| `planetary_positions` | JSONB | Complete position data (backup) |
| `lunar_phase_name` | VARCHAR(50) | Moon phase description |
| `lunar_phase_angle` | DOUBLE PRECISION | Phase angle in degrees |
| `significant_events` | TEXT[] | Notable astrological events |
| `daily_score` | DOUBLE PRECISION | Overall favorability (0-100) |
| `market_outlook` | TEXT | 'bullish', 'bearish', 'neutral', 'volatile' |

### 3. Normalized Position Tables

#### `daily_planetary_positions`
Individual planet positions for each day.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `conditions_id` | INTEGER | FK to daily_astrological_conditions |
| `trade_date` | DATE | Denormalized for fast queries |
| `planet` | VARCHAR(20) | Planet name (FK to planets.name) |
| `longitude` | DOUBLE PRECISION | Ecliptic longitude (0-360°) |
| `latitude` | DOUBLE PRECISION | Ecliptic latitude |
| `zodiac_sign` | VARCHAR(15) | Sign name (e.g., 'Aries', 'Taurus') |
| `degree_in_sign` | DOUBLE PRECISION | Position within sign (0-30°) |
| `is_retrograde` | BOOLEAN | Retrograde motion indicator |
| `daily_motion` | DOUBLE PRECISION | Movement per day (future) |
| `house_number` | INTEGER | Astrological house (future) |

**Unique Constraint**: `(trade_date, planet)`

#### `daily_planetary_aspects`
Planetary aspect relationships for each day.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `conditions_id` | INTEGER | FK to daily_astrological_conditions |
| `trade_date` | DATE | Denormalized for fast queries |
| `planet1` | VARCHAR(20) | First planet (alphabetically ordered) |
| `planet2` | VARCHAR(20) | Second planet (alphabetically ordered) |
| `aspect_type` | VARCHAR(20) | FK to aspect_types.name |
| `orb` | DOUBLE PRECISION | Deviation from exact aspect |
| `separating_angle` | DOUBLE PRECISION | Actual angular separation |
| `is_exact` | BOOLEAN | Orb < 1 degree |
| `is_tight` | BOOLEAN | Orb < 3 degrees |
| `is_applying` | BOOLEAN | Aspect getting tighter (future) |

**Unique Constraint**: `(trade_date, planet1, planet2, aspect_type)`
**Check Constraint**: `planet1 < planet2` (alphabetical ordering)

### 4. Analysis Tables

#### `daily_harmonic_analysis`
Pre-calculated harmonic metrics for each day.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `conditions_id` | INTEGER | FK to daily_astrological_conditions |
| `trade_date` | DATE | UNIQUE date |
| `total_aspects` | INTEGER | Total number of aspects |
| `harmonious_aspects` | INTEGER | Trines + sextiles count |
| `challenging_aspects` | INTEGER | Squares + oppositions count |
| `neutral_aspects` | INTEGER | Conjunctions count |
| `harmony_ratio` | DOUBLE PRECISION | harmonious / total (0-1) |
| `tension_ratio` | DOUBLE PRECISION | challenging / total (0-1) |
| `overall_harmony_score` | INTEGER | Composite score (1-100) |
| **Elemental Distribution** | | |
| `fire_planets` | INTEGER | Planets in fire signs |
| `earth_planets` | INTEGER | Planets in earth signs |
| `air_planets` | INTEGER | Planets in air signs |
| `water_planets` | INTEGER | Planets in water signs |
| `elemental_balance_score` | DOUBLE PRECISION | Balance metric (0-1) |
| **Modal Distribution** | | |
| `cardinal_planets` | INTEGER | Planets in cardinal signs |
| `fixed_planets` | INTEGER | Planets in fixed signs |
| `mutable_planets` | INTEGER | Planets in mutable signs |
| `modal_balance_score` | DOUBLE PRECISION | Balance metric (0-1) |
| **Pattern Flags** | | |
| `has_grand_trine` | BOOLEAN | Grand trine present |
| `has_t_square` | BOOLEAN | T-square present |
| `has_grand_cross` | BOOLEAN | Grand cross present |
| `has_stellium` | BOOLEAN | Stellium present |
| `has_yod` | BOOLEAN | Yod present |
| **Planetary Emphasis** | | |
| `outer_planet_aspects` | INTEGER | Outer planet aspect count |
| `inner_planet_aspects` | INTEGER | Inner planet aspect count |
| `generational_emphasis_score` | DOUBLE PRECISION | Outer planet emphasis |

#### `daily_astrological_patterns`
Detected complex astrological patterns.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `conditions_id` | INTEGER | FK to daily_astrological_conditions |
| `trade_date` | DATE | Pattern date |
| `pattern_type` | VARCHAR(30) | Pattern category |
| `pattern_subtype` | VARCHAR(50) | Specific pattern variant |
| `primary_planets` | TEXT[] | Core planets in pattern |
| `supporting_planets` | TEXT[] | Supporting planets |
| `orb_tightness` | DOUBLE PRECISION | Average orb of pattern aspects |
| `pattern_strength` | INTEGER | Strength rating (1-10) |
| `is_exact` | BOOLEAN | All aspects < 2° orb |
| `geometric_precision` | DOUBLE PRECISION | Geometry accuracy (0-1) |
| `element` | VARCHAR(10) | Primary element if applicable |
| `modality` | VARCHAR(10) | Primary modality if applicable |
| `pattern_quality` | VARCHAR(20) | 'harmonious', 'challenging', etc. |
| `pattern_meaning` | TEXT | Astrological interpretation |
| `market_significance` | TEXT | Trading implications |

## Key Relationships

```
daily_astrological_conditions (1)
├── daily_planetary_positions (10) -- One per planet
├── daily_planetary_aspects (0-45) -- Variable aspect count
├── daily_harmonic_analysis (1) -- One summary per day
└── daily_astrological_patterns (0-N) -- Variable pattern count

planets (10) ←→ daily_planetary_positions (many)
aspect_types (5) ←→ daily_planetary_aspects (many)
```

## Performance Features

### Indexing Strategy

1. **Primary Queries**: Date-based lookups
2. **Planet Filters**: Specific planet aspects/positions
3. **Pattern Matching**: Aspect type and pattern combinations
4. **Quality Filters**: Exact/tight aspects, high harmony scores

### Denormalization

- `trade_date` duplicated in child tables for JOIN-free queries
- Pre-calculated ratios and scores in `daily_harmonic_analysis`
- Boolean pattern flags for fast filtering

### Query Optimization

- Alphabetical planet ordering prevents aspect duplicates
- GIN indexes on planet arrays for pattern searches
- Partial indexes on boolean flags (retrograde, exact aspects)
- Composite indexes for common query patterns

## Data Validation

### Check Constraints

- Longitude: 0 ≤ longitude < 360
- Degree in sign: 0 ≤ degree < 30
- Orb: 0 ≤ orb ≤ 15
- Scores: 0 ≤ score ≤ 100 or 0 ≤ ratio ≤ 1

### Business Rules

- Planet ordering: `planet1 < planet2` alphabetically
- Unique aspects per day: One aspect type per planet pair per date
- Referential integrity: All planets and aspect types must exist

## Utility Functions

### `calculate_elemental_balance(fire, earth, air, water)`
Calculates how balanced the elemental distribution is.
- Returns: 0.0 (all planets in one element) to 1.0 (perfectly balanced)

### `get_zodiac_element(sign)`
Returns the element for a zodiac sign.
- Returns: 'fire', 'earth', 'air', 'water'

### `get_zodiac_modality(sign)`
Returns the modality for a zodiac sign.
- Returns: 'cardinal', 'fixed', 'mutable'

## Usage Patterns

### Common Query Types

1. **Position Queries**: "Jupiter in Capricorn dates"
2. **Aspect Queries**: "Jupiter-Mars squares"
3. **Pattern Queries**: "Grand trines in fire signs"
4. **Harmony Queries**: "High harmony score days"
5. **Correlation Queries**: "Patterns vs. market performance"

### Data Flow

1. **Daily Calculation**: Swiss Ephemeris → positions + aspects
2. **Normalization**: Split into individual position/aspect records
3. **Analysis**: Calculate harmonic metrics and detect patterns
4. **Storage**: All data stored in normalized schema
5. **Querying**: Fast retrieval using optimized indexes