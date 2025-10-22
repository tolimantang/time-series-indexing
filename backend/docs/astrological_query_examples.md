# Astrological Analysis Query Examples

This document provides comprehensive SQL query examples for the enhanced astrological analysis schema.

## Table of Contents

1. [Basic Position Queries](#basic-position-queries)
2. [Aspect Analysis Queries](#aspect-analysis-queries)
3. [Harmonic Analysis Queries](#harmonic-analysis-queries)
4. [Pattern Detection Queries](#pattern-detection-queries)
5. [Trading Correlation Queries](#trading-correlation-queries)
6. [Statistical Analysis Queries](#statistical-analysis-queries)
7. [Complex Multi-Table Queries](#complex-multi-table-queries)

---

## Basic Position Queries

### 1. Find dates when Jupiter was in Capricorn

```sql
SELECT trade_date, degree_in_sign, is_retrograde
FROM daily_planetary_positions
WHERE planet = 'Jupiter'
  AND zodiac_sign = 'Capricorn'
ORDER BY trade_date;
```

### 2. Get all planet positions for a specific date

```sql
SELECT p.display_order, dpp.planet, dpp.zodiac_sign,
       dpp.degree_in_sign, dpp.is_retrograde,
       CONCAT(ROUND(dpp.degree_in_sign, 1), '° ', dpp.zodiac_sign) as position
FROM daily_planetary_positions dpp
JOIN planets p ON dpp.planet = p.name
WHERE dpp.trade_date = '2024-01-15'
ORDER BY p.display_order;
```

### 3. Find Mercury retrograde periods

```sql
SELECT MIN(trade_date) as retrograde_start,
       MAX(trade_date) as retrograde_end,
       COUNT(*) as days_count
FROM daily_planetary_positions
WHERE planet = 'Mercury'
  AND is_retrograde = true
  AND trade_date >= '2024-01-01'
GROUP BY trade_date - ROW_NUMBER() OVER (ORDER BY trade_date)::integer
ORDER BY retrograde_start;
```

### 4. Count planets in each element by date

```sql
SELECT dpp.trade_date,
       COUNT(*) FILTER (WHERE get_zodiac_element(dpp.zodiac_sign) = 'fire') as fire_count,
       COUNT(*) FILTER (WHERE get_zodiac_element(dpp.zodiac_sign) = 'earth') as earth_count,
       COUNT(*) FILTER (WHERE get_zodiac_element(dpp.zodiac_sign) = 'air') as air_count,
       COUNT(*) FILTER (WHERE get_zodiac_element(dpp.zodiac_sign) = 'water') as water_count
FROM daily_planetary_positions dpp
WHERE dpp.trade_date BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY dpp.trade_date
ORDER BY dpp.trade_date;
```

---

## Aspect Analysis Queries

### 5. Find Jupiter-Mercury sextiles with trading correlation

```sql
SELECT dpa.trade_date,
       dpa.orb,
       dpa.is_exact,
       dac.daily_score,
       dac.market_outlook
FROM daily_planetary_aspects dpa
JOIN daily_astrological_conditions dac ON dpa.trade_date = dac.trade_date
WHERE dpa.planet1 = 'Jupiter'
  AND dpa.planet2 = 'Mercury'
  AND dpa.aspect_type = 'sextile'
ORDER BY dpa.trade_date;
```

### 6. Find all exact aspects (orb < 1°) on high-scoring days

```sql
SELECT dac.trade_date,
       dac.daily_score,
       STRING_AGG(
           CONCAT(dpa.planet1, ' ', dpa.aspect_type, ' ', dpa.planet2, ' (', ROUND(dpa.orb, 1), '°)'),
           ', '
       ) as exact_aspects
FROM daily_planetary_aspects dpa
JOIN daily_astrological_conditions dac ON dpa.trade_date = dac.trade_date
WHERE dpa.is_exact = true
  AND dac.daily_score > 75
GROUP BY dac.trade_date, dac.daily_score
ORDER BY dac.daily_score DESC;
```

### 7. Count Mars aspects by type and harmony

```sql
SELECT at.name as aspect_type,
       at.harmony_type,
       COUNT(*) as count,
       AVG(dpa.orb) as avg_orb,
       COUNT(*) FILTER (WHERE dpa.is_exact) as exact_count
FROM daily_planetary_aspects dpa
JOIN aspect_types at ON dpa.aspect_type = at.name
WHERE dpa.planet1 = 'Mars' OR dpa.planet2 = 'Mars'
GROUP BY at.name, at.harmony_type
ORDER BY count DESC;
```

### 8. Find days with multiple harmonious aspects

```sql
SELECT dpa.trade_date,
       COUNT(*) as harmonious_count,
       STRING_AGG(
           CONCAT(dpa.planet1, ' ', dpa.aspect_type, ' ', dpa.planet2),
           ', '
       ) as aspects
FROM daily_planetary_aspects dpa
JOIN aspect_types at ON dpa.aspect_type = at.name
WHERE at.harmony_type = 'harmonious'
GROUP BY dpa.trade_date
HAVING COUNT(*) >= 3
ORDER BY harmonious_count DESC, dpa.trade_date;
```

---

## Harmonic Analysis Queries

### 9. Find most harmonious days

```sql
SELECT dha.trade_date,
       dha.overall_harmony_score,
       dha.harmony_ratio,
       dha.tension_ratio,
       dha.elemental_balance_score,
       dac.market_outlook,
       dha.has_grand_trine,
       dha.has_t_square
FROM daily_harmonic_analysis dha
JOIN daily_astrological_conditions dac ON dha.trade_date = dac.trade_date
WHERE dha.overall_harmony_score > 80
ORDER BY dha.overall_harmony_score DESC, dha.trade_date;
```

### 10. Analyze harmony vs market outlook correlation

```sql
SELECT dac.market_outlook,
       COUNT(*) as day_count,
       AVG(dha.overall_harmony_score) as avg_harmony,
       AVG(dha.harmony_ratio) as avg_harmony_ratio,
       AVG(dha.elemental_balance_score) as avg_elemental_balance,
       COUNT(*) FILTER (WHERE dha.has_grand_trine) as grand_trine_days
FROM daily_harmonic_analysis dha
JOIN daily_astrological_conditions dac ON dha.trade_date = dac.trade_date
GROUP BY dac.market_outlook
ORDER BY avg_harmony DESC;
```

### 11. Find elemental imbalances

```sql
SELECT dha.trade_date,
       dha.elemental_balance_score,
       dha.fire_planets,
       dha.earth_planets,
       dha.air_planets,
       dha.water_planets,
       CASE
           WHEN dha.fire_planets >= 6 THEN 'Fire Dominant'
           WHEN dha.earth_planets >= 6 THEN 'Earth Dominant'
           WHEN dha.air_planets >= 6 THEN 'Air Dominant'
           WHEN dha.water_planets >= 6 THEN 'Water Dominant'
           ELSE 'Balanced'
       END as dominance_type
FROM daily_harmonic_analysis dha
WHERE dha.elemental_balance_score < 0.3  -- Highly imbalanced
ORDER BY dha.elemental_balance_score ASC;
```

### 12. Pattern frequency analysis

```sql
SELECT 'Grand Trine' as pattern,
       COUNT(*) FILTER (WHERE has_grand_trine) as occurrences,
       ROUND(COUNT(*) FILTER (WHERE has_grand_trine) * 100.0 / COUNT(*), 1) as percentage
FROM daily_harmonic_analysis
WHERE trade_date >= '2024-01-01'

UNION ALL

SELECT 'T-Square' as pattern,
       COUNT(*) FILTER (WHERE has_t_square),
       ROUND(COUNT(*) FILTER (WHERE has_t_square) * 100.0 / COUNT(*), 1)
FROM daily_harmonic_analysis
WHERE trade_date >= '2024-01-01'

UNION ALL

SELECT 'Grand Cross' as pattern,
       COUNT(*) FILTER (WHERE has_grand_cross),
       ROUND(COUNT(*) FILTER (WHERE has_grand_cross) * 100.0 / COUNT(*), 1)
FROM daily_harmonic_analysis
WHERE trade_date >= '2024-01-01';
```

---

## Pattern Detection Queries

### 13. Find all Grand Trines

```sql
SELECT dap.trade_date,
       dap.pattern_subtype,
       dap.primary_planets,
       dap.element,
       dap.pattern_strength,
       dap.orb_tightness,
       dac.daily_score,
       dac.market_outlook
FROM daily_astrological_patterns dap
JOIN daily_astrological_conditions dac ON dap.trade_date = dac.trade_date
WHERE dap.pattern_type = 'grand_trine'
ORDER BY dap.pattern_strength DESC, dap.trade_date;
```

### 14. Find days with multiple major patterns

```sql
SELECT dap.trade_date,
       COUNT(*) as pattern_count,
       STRING_AGG(dap.pattern_type, ', ') as patterns,
       STRING_AGG(
           CONCAT(dap.pattern_type, ' (', dap.pattern_strength, '/10)'),
           ', '
       ) as pattern_details,
       MAX(dac.daily_score) as daily_score
FROM daily_astrological_patterns dap
JOIN daily_astrological_conditions dac ON dap.trade_date = dac.trade_date
WHERE dap.pattern_type IN ('grand_trine', 't_square', 'grand_cross', 'yod')
GROUP BY dap.trade_date
HAVING COUNT(*) > 1
ORDER BY pattern_count DESC, dap.trade_date;
```

### 15. Fire element patterns during high market scores

```sql
SELECT dap.trade_date,
       dap.pattern_type,
       dap.pattern_subtype,
       dap.primary_planets,
       dap.pattern_strength,
       dac.daily_score,
       dac.market_outlook
FROM daily_astrological_patterns dap
JOIN daily_astrological_conditions dac ON dap.trade_date = dac.trade_date
WHERE dap.element = 'fire'
  AND dac.daily_score > 70
ORDER BY dac.daily_score DESC, dap.pattern_strength DESC;
```

---

## Trading Correlation Queries

### 16. Jupiter aspects vs oil trading performance

```sql
-- This query would join with your trading_opportunities table
SELECT dpa.aspect_type,
       at.harmony_type,
       COUNT(*) as aspect_occurrences,
       AVG(CASE WHEN to.symbol LIKE '%oil%' OR to.symbol LIKE '%crude%'
                THEN to.profit_percent END) as avg_oil_profit,
       COUNT(*) FILTER (WHERE (to.symbol LIKE '%oil%' OR to.symbol LIKE '%crude%')
                           AND to.profit_percent > 0) as profitable_oil_trades,
       COUNT(*) FILTER (WHERE to.symbol LIKE '%oil%' OR to.symbol LIKE '%crude%') as total_oil_trades
FROM daily_planetary_aspects dpa
JOIN aspect_types at ON dpa.aspect_type = at.name
LEFT JOIN trading_opportunities to ON dpa.trade_date = to.entry_date
WHERE (dpa.planet1 = 'Jupiter' OR dpa.planet2 = 'Jupiter')
  AND dpa.trade_date >= '2023-01-01'
GROUP BY dpa.aspect_type, at.harmony_type
ORDER BY avg_oil_profit DESC NULLS LAST;
```

### 17. New Moon vs Full Moon trading performance

```sql
SELECT dac.lunar_phase_name,
       COUNT(*) as total_days,
       AVG(dac.daily_score) as avg_daily_score,
       COUNT(*) FILTER (WHERE dac.market_outlook = 'bullish') as bullish_days,
       COUNT(*) FILTER (WHERE dac.market_outlook = 'bearish') as bearish_days,
       ROUND(
           COUNT(*) FILTER (WHERE dac.market_outlook = 'bullish') * 100.0 / COUNT(*),
           1
       ) as bullish_percentage
FROM daily_astrological_conditions dac
WHERE dac.lunar_phase_name IN ('New Moon', 'Full Moon')
  AND dac.trade_date >= '2023-01-01'
GROUP BY dac.lunar_phase_name
ORDER BY bullish_percentage DESC;
```

### 18. Mars retrograde vs market volatility

```sql
SELECT dpp.is_retrograde as mars_retrograde,
       COUNT(*) as day_count,
       AVG(dac.daily_score) as avg_score,
       COUNT(*) FILTER (WHERE dac.market_outlook = 'volatile') as volatile_days,
       ROUND(
           COUNT(*) FILTER (WHERE dac.market_outlook = 'volatile') * 100.0 / COUNT(*),
           1
       ) as volatility_percentage,
       AVG(dha.challenging_aspects) as avg_challenging_aspects
FROM daily_planetary_positions dpp
JOIN daily_astrological_conditions dac ON dpp.trade_date = dac.trade_date
JOIN daily_harmonic_analysis dha ON dpp.trade_date = dha.trade_date
WHERE dpp.planet = 'Mars'
  AND dpp.trade_date >= '2023-01-01'
GROUP BY dpp.is_retrograde
ORDER BY volatility_percentage DESC;
```

---

## Statistical Analysis Queries

### 19. Aspect frequency by planet combination

```sql
SELECT dpa.planet1,
       dpa.planet2,
       dpa.aspect_type,
       COUNT(*) as frequency,
       AVG(dpa.orb) as avg_orb,
       MIN(dpa.orb) as min_orb,
       MAX(dpa.orb) as max_orb,
       COUNT(*) FILTER (WHERE dpa.is_exact) as exact_count
FROM daily_planetary_aspects dpa
WHERE dpa.trade_date >= '2023-01-01'
GROUP BY dpa.planet1, dpa.planet2, dpa.aspect_type
HAVING COUNT(*) >= 5  -- Only frequent aspects
ORDER BY frequency DESC;
```

### 20. Seasonal harmony patterns

```sql
SELECT EXTRACT(MONTH FROM dha.trade_date) as month,
       TO_CHAR(DATE_TRUNC('month', dha.trade_date), 'Month') as month_name,
       COUNT(*) as day_count,
       AVG(dha.overall_harmony_score) as avg_harmony,
       AVG(dha.elemental_balance_score) as avg_elemental_balance,
       COUNT(*) FILTER (WHERE dha.has_grand_trine) as grand_trine_count,
       COUNT(*) FILTER (WHERE dha.has_t_square) as t_square_count
FROM daily_harmonic_analysis dha
WHERE dha.trade_date >= '2023-01-01'
GROUP BY EXTRACT(MONTH FROM dha.trade_date),
         TO_CHAR(DATE_TRUNC('month', dha.trade_date), 'Month')
ORDER BY EXTRACT(MONTH FROM dha.trade_date);
```

### 21. Outer planet aspect impact

```sql
SELECT CASE
           WHEN (dpa.planet1 IN ('Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto')
                 OR dpa.planet2 IN ('Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'))
           THEN 'Outer Planet Aspect'
           ELSE 'Inner Planet Aspect'
       END as aspect_category,
       dpa.aspect_type,
       COUNT(*) as count,
       AVG(dac.daily_score) as avg_daily_score,
       COUNT(*) FILTER (WHERE dac.market_outlook = 'volatile') as volatile_days
FROM daily_planetary_aspects dpa
JOIN daily_astrological_conditions dac ON dpa.trade_date = dac.trade_date
WHERE dpa.trade_date >= '2023-01-01'
GROUP BY CASE
             WHEN (dpa.planet1 IN ('Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto')
                   OR dpa.planet2 IN ('Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'))
             THEN 'Outer Planet Aspect'
             ELSE 'Inner Planet Aspect'
         END, dpa.aspect_type
ORDER BY aspect_category, avg_daily_score DESC;
```

---

## Complex Multi-Table Queries

### 22. Comprehensive daily astrological summary

```sql
SELECT dac.trade_date,
       dac.daily_score,
       dac.market_outlook,
       dac.lunar_phase_name,

       -- Harmony metrics
       dha.overall_harmony_score,
       dha.harmony_ratio,
       dha.elemental_balance_score,

       -- Element distribution
       CONCAT(dha.fire_planets, 'F/', dha.earth_planets, 'E/',
              dha.air_planets, 'A/', dha.water_planets, 'W') as element_distribution,

       -- Pattern flags
       CASE WHEN dha.has_grand_trine THEN 'GT ' ELSE '' END ||
       CASE WHEN dha.has_t_square THEN 'TS ' ELSE '' END ||
       CASE WHEN dha.has_grand_cross THEN 'GC ' ELSE '' END ||
       CASE WHEN dha.has_stellium THEN 'ST ' ELSE '' END ||
       CASE WHEN dha.has_yod THEN 'YOD ' ELSE '' END as patterns,

       -- Aspect summary
       CONCAT(dha.harmonious_aspects, 'H/', dha.challenging_aspects, 'C/',
              dha.neutral_aspects, 'N') as aspect_summary,

       -- Retrograde planets
       STRING_AGG(
           CASE WHEN dpp.is_retrograde THEN dpp.planet ELSE NULL END,
           ', '
       ) as retrograde_planets

FROM daily_astrological_conditions dac
JOIN daily_harmonic_analysis dha ON dac.trade_date = dha.trade_date
LEFT JOIN daily_planetary_positions dpp ON dac.trade_date = dpp.trade_date
WHERE dac.trade_date >= '2024-01-01'
GROUP BY dac.trade_date, dac.daily_score, dac.market_outlook, dac.lunar_phase_name,
         dha.overall_harmony_score, dha.harmony_ratio, dha.elemental_balance_score,
         dha.fire_planets, dha.earth_planets, dha.air_planets, dha.water_planets,
         dha.has_grand_trine, dha.has_t_square, dha.has_grand_cross,
         dha.has_stellium, dha.has_yod, dha.harmonious_aspects,
         dha.challenging_aspects, dha.neutral_aspects
ORDER BY dac.trade_date;
```

### 23. Pattern correlation with trading outcomes

```sql
-- Comprehensive pattern vs trading performance analysis
WITH pattern_days AS (
    SELECT DISTINCT dap.trade_date,
           dap.pattern_type,
           dap.element,
           dac.daily_score,
           dac.market_outlook
    FROM daily_astrological_patterns dap
    JOIN daily_astrological_conditions dac ON dap.trade_date = dac.trade_date
    WHERE dap.pattern_type IN ('grand_trine', 't_square', 'grand_cross')
),
trading_performance AS (
    SELECT pd.pattern_type,
           pd.element,
           COUNT(*) as pattern_occurrences,
           AVG(pd.daily_score) as avg_daily_score,

           -- Market outlook distribution
           COUNT(*) FILTER (WHERE pd.market_outlook = 'bullish') as bullish_days,
           COUNT(*) FILTER (WHERE pd.market_outlook = 'bearish') as bearish_days,
           COUNT(*) FILTER (WHERE pd.market_outlook = 'volatile') as volatile_days,
           COUNT(*) FILTER (WHERE pd.market_outlook = 'neutral') as neutral_days,

           -- Would join with trading_opportunities for actual performance
           -- This is a placeholder for trading correlation
           ROUND(AVG(pd.daily_score), 1) as trading_favorability_score

    FROM pattern_days pd
    GROUP BY pd.pattern_type, pd.element
)
SELECT tp.pattern_type,
       tp.element,
       tp.pattern_occurrences,
       tp.avg_daily_score,
       tp.trading_favorability_score,
       ROUND(tp.bullish_days * 100.0 / tp.pattern_occurrences, 1) as bullish_percentage,
       ROUND(tp.volatile_days * 100.0 / tp.pattern_occurrences, 1) as volatile_percentage
FROM trading_performance tp
ORDER BY tp.trading_favorability_score DESC;
```

---

## Query Performance Tips

### Indexes Usage

Most queries will benefit from these key indexes:
- `idx_positions_planet_date` for planet-specific position queries
- `idx_aspects_type_date` for aspect type filtering
- `idx_harmonic_harmony_score` for harmony-based sorting
- `idx_patterns_type_date` for pattern filtering

### Query Optimization

1. **Use date ranges** to limit result sets
2. **Filter early** with WHERE clauses before JOINs
3. **Use EXISTS** instead of IN for subqueries when possible
4. **Leverage partial indexes** for boolean flag queries
5. **Consider EXPLAIN ANALYZE** for complex queries

### Best Practices

1. Always include date ranges for time-series queries
2. Use the denormalized `trade_date` columns to avoid unnecessary JOINs
3. Filter on indexed columns first (planet, aspect_type, pattern_type)
4. Use aggregation functions efficiently with proper GROUP BY
5. Consider materialized views for frequently-run complex queries