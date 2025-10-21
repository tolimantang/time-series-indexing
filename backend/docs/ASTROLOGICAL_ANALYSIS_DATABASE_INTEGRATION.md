# Astrological Analysis Database Integration

## Overview

The astrological trading analysis system has been updated to store results directly in the PostgreSQL database instead of temporary JSON files, and the profit threshold has been lowered to 5% to find more trading opportunities.

## Key Changes Made

### 1. Database Schema Updates

**New Columns Added to `trading_opportunities` Table:**
```sql
-- Astrological analysis columns
entry_astro_description TEXT              -- Natural language description of entry conditions
exit_astro_description TEXT               -- Natural language description of exit conditions
entry_planetary_data JSONB               -- Complete planetary position data at entry
exit_planetary_data JSONB                -- Complete planetary position data at exit
astro_analysis_summary TEXT              -- Concise summary of astrological patterns
claude_analysis TEXT                     -- Claude AI analysis results
astrological_score DOUBLE PRECISION     -- Composite astrological favorability score (0-100)
astro_analyzed_at TIMESTAMP WITH TIME ZONE  -- When analysis was performed
```

**Migration Script:** `scripts/migrations/add_astro_columns_to_trading_opportunities.sql`

### 2. Trading Opportunity Threshold Updated

**Previous:** Only profitable trades (>0%)
**Updated:** Minimum 5% profit threshold to classify as trading opportunity

**Configuration Changes:**
- `config/trading_config.yaml` - Added `min_profit_percent: 5.0`
- `src/trading_analyzer/core/opportunity_detector.py` - Updated validation logic

### 3. Comprehensive Astro Job Enhanced

**Previous Behavior:**
- Saved results to `/tmp/*.json` files (lost when pod terminates)
- Generated manual prompts for Claude analysis

**New Behavior:**
- Stores all astrological data directly in `trading_opportunities` table
- Automatically queries Claude API for pattern analysis
- Calculates astrological scores (0-100) based on planetary favorability
- Creates searchable summaries for each trade

**Updated File:** `deploy/k8s/shared/comprehensive-astro-trading-job.yaml`

## New Features

### Astrological Scoring System
The system now calculates a composite astrological score (0-100) for each trade based on:
- **Favorable Aspects:** Trines and sextiles increase score
- **Challenging Aspects:** Squares and oppositions decrease score
- **Lunar Phases:** New/Waxing moons favor growth (long positions)
- **Aspect Exactness:** More exact aspects have stronger influence

### Database Storage Functions
- `store_astrological_analysis_in_db()` - Stores complete analysis in database
- `ensure_astro_columns_exist()` - Auto-creates columns if needed
- `calculate_astrological_score()` - Generates 0-100 favorability score
- `create_analysis_summary()` - Creates concise trade summaries

## Data Access Examples

### Query All Astrological Analysis Results
```sql
SELECT symbol, position_type, profit_percent, entry_date, exit_date,
       entry_astro_description, exit_astro_description, astrological_score
FROM trading_opportunities
WHERE astro_analyzed_at IS NOT NULL
ORDER BY astrological_score DESC;
```

### Find Specific Astrological Patterns
```sql
-- Find trades with Mars-Jupiter aspects
SELECT * FROM trading_opportunities
WHERE entry_astro_description ILIKE '%mars%jupiter%'
  AND profit_percent > 10
ORDER BY astrological_score DESC;

-- Find trades during specific lunar phases
SELECT * FROM trading_opportunities
WHERE entry_astro_description ILIKE '%full moon%'
  AND position_type = 'long'
ORDER BY profit_percent DESC;

-- Top astrologically favorable trades
SELECT symbol, profit_percent, holding_days, astrological_score,
       astro_analysis_summary
FROM trading_opportunities
WHERE astrological_score > 70
ORDER BY astrological_score DESC;
```

### Analyze Claude's Pattern Insights
```sql
-- View Claude's analysis for high-profit trades
SELECT profit_percent, claude_analysis
FROM trading_opportunities
WHERE claude_analysis IS NOT NULL
  AND profit_percent > 15
ORDER BY profit_percent DESC;
```

## Deployment Process

### 1. Run Database Migration (Optional)
```bash
# Apply migration if columns don't exist
kubectl exec -it postgres-pod -- psql -d your_database -f /path/to/migration.sql
```

### 2. Regenerate Trading Opportunities with 5% Threshold
```bash
# Generate more opportunities with 5% minimum profit
kubectl apply -f deploy/k8s/shared/regenerate-trading-opportunities-job.yaml
kubectl logs -f job/regenerate-trading-opportunities-5pct -n time-series-indexing
```

### 3. Run Comprehensive Astrological Analysis
```bash
# Analyze opportunities and store in database
kubectl apply -f deploy/k8s/shared/comprehensive-astro-trading-job.yaml
kubectl logs -f job/comprehensive-astro-trading-analysis -n time-series-indexing
```

## Sample Results

After running the analysis, you'll have data like:

**Entry Astrological Description:**
```
"Astrological conditions for 2024-01-15: Sun in late Capricorn; Moon in Waxing phase; Mars-Jupiter trine"
```

**Exit Astrological Description:**
```
"Astrological conditions for 2024-01-22: Sun in early Aquarius; Moon in Full phase; Venus-Mercury conjunction"
```

**Analysis Summary:**
```
"CRUDE_OIL_WTI LONG trade: 12.5% profit in 7 days | Entry during Waxing Moon | Key aspect: mars-jupiter trine | Exit during Full Moon"
```

**Claude Analysis:**
```
"This analysis reveals that Mars-Jupiter trines appear in 68% of profitable long positions,
particularly when combined with Waxing Moon phases. Full Moon exits show 15% higher average
profits compared to other lunar phases..."
```

## Benefits

1. **Persistent Storage:** All analysis results saved permanently in database
2. **Searchable Patterns:** Find specific astrological configurations
3. **Automated Analysis:** Claude API provides insights automatically
4. **Quantified Scoring:** Numerical scores for ranking astrological favorability
5. **More Opportunities:** 5% threshold generates significantly more tradeable opportunities
6. **Integrated Workflow:** Everything stored in single database table

## Troubleshooting

**If astrological columns don't exist:**
- The job automatically creates them, or run the migration manually

**If no opportunities found:**
- Check if trading data exists in `market_data` table
- Verify 5% threshold isn't too restrictive for your market conditions

**If Claude analysis is empty:**
- Ensure `ANTHROPIC_API_KEY` is set in Kubernetes secrets
- Job will still work without Claude, just without AI analysis

## Next Steps

1. **Monitor Results:** Check database for astrological analysis completion
2. **Query Patterns:** Use SQL to identify profitable astrological configurations
3. **Refine Scoring:** Adjust astrological scoring algorithm based on results
4. **Automate Trading:** Integrate astrological insights into trading decisions