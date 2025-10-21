# Comprehensive Astrological Trading Analysis

This system correlates actual planetary positions with profitable trading opportunities using Swiss Ephemeris calculations and Claude AI analysis.

## Overview

The comprehensive astrological trading analysis:

1. **Retrieves Trading Opportunities**: Gets profitable trades from the `trading_opportunities` table
2. **Calculates Actual Planetary Positions**: Uses Swiss Ephemeris to compute real astronomical data for entry/exit dates
3. **Analyzes Patterns**: Uses Claude AI to identify astrological patterns in profitable trades
4. **Generates Insights**: Provides actionable trading guidance based on astrological correlations

## Key Features

### Swiss Ephemeris Integration
- Calculates precise planetary positions for any date
- Computes major aspects (conjunctions, oppositions, trines, squares, sextiles)
- Determines lunar phases and sign positions
- Identifies significant astrological events

### Claude AI Analysis
- Automatically analyzes patterns in astrological data
- Correlates planetary positions with trading profitability
- Generates specific trading recommendations
- Identifies optimal entry/exit timing based on astrological conditions

### Comprehensive Data Output
- Actual planetary longitude, latitude, and speed data
- Natural language descriptions of astrological conditions
- Detailed aspect calculations with exactness ratings
- Market-focused astrological interpretations

## Files and Components

### Kubernetes Job
- `deploy/k8s/shared/comprehensive-astro-trading-job.yaml` - Main analysis job

### Core Python Scripts
- `scripts/astro/trading_astro_correlation.py` - Full analysis using existing encoder system
- `scripts/astro/test_comprehensive_analysis.py` - Local testing script

### Astro Encoder System
- `src/astro_encoder/core/encoder.py` - Swiss Ephemeris calculations
- `src/astro_encoder/core/verbalizer.py` - Natural language descriptions
- `src/astro_encoder/core/data_access.py` - PostgreSQL storage
- `src/astro_encoder/models/data_models.py` - Data structures

## Required Dependencies

### Python Packages
```bash
pip install pyswisseph anthropic psycopg2-binary pandas numpy
```

### Environment Variables
```bash
# Database connection
DB_HOST=your-postgres-host
DB_PORT=5432
DB_NAME=your-database-name
DB_USER=your-username
DB_PASSWORD=your-password

# Claude API (optional)
ANTHROPIC_API_KEY=your-claude-api-key
```

## Usage

### 1. Test Components Locally
```bash
cd backend
python3 scripts/astro/test_comprehensive_analysis.py
```

### 2. Run Full Analysis Locally
```bash
cd backend
python3 scripts/astro/trading_astro_correlation.py --limit 30
```

### 3. Deploy to Kubernetes
```bash
kubectl apply -f deploy/k8s/shared/comprehensive-astro-trading-job.yaml
```

### 4. Monitor Job Progress
```bash
kubectl logs -f job/comprehensive-astro-trading-analysis -n time-series-indexing
```

## Sample Output

### Astrological Analysis for a Trade
```
Trade: CRUDE_OIL_WTI LONG - 12.5% profit in 7 days
Entry (2024-01-15): Sun in late Capricorn; Moon in Waxing phase; Mars-Jupiter trine
Exit (2024-01-22): Sun in early Aquarius; Moon in Full phase; Venus-Mercury conjunction
```

### Claude AI Pattern Analysis
The system automatically generates insights like:
- "Mars-Jupiter trines appear in 68% of profitable long positions"
- "Full Moon phases correlate with optimal exit timing for oil futures"
- "Mercury retrograde periods show reduced trading success rates"

## Database Schema

### Required Tables
- `trading_opportunities` - Profitable trades to analyze
- `astrological_data` - Cached planetary calculations (optional)
- `daily_planetary_positions` - Quick lookup table (optional)

### Data Flow
1. Read trading opportunities from database
2. Calculate astrological data for entry/exit dates
3. Generate natural language descriptions
4. Analyze patterns with Claude AI
5. Save comprehensive results to `/tmp/comprehensive_astro_analysis_*.json`

## Advanced Configuration

### Custom Analysis Parameters
- Modify the job to analyze specific symbols only
- Adjust the number of top trades to analyze
- Configure different aspect orb tolerances
- Choose specific planetary combinations

### Integration with Existing Systems
- Results can be imported into trading decision algorithms
- Astrological data can be stored for future backtesting
- Pattern insights can inform automated trading strategies

## Troubleshooting

### Common Issues
1. **Swiss Ephemeris Errors**: Ensure ephemeris data files are accessible
2. **Database Connection**: Verify all environment variables are set
3. **Claude API Limits**: Check API key and rate limits
4. **Memory Issues**: Large date ranges may require more memory allocation

### Debug Mode
Set logging level to DEBUG for detailed calculation output:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Results Interpretation

The analysis provides:
- **Entry Patterns**: Astrological conditions favoring trade initiation
- **Exit Patterns**: Planetary positions indicating optimal closing
- **Timing Insights**: Lunar phases and planetary transits affecting profitability
- **Risk Indicators**: Astrological configurations suggesting volatility

Use these insights to:
- Time market entries based on favorable planetary aspects
- Set exit targets aligned with lunar cycles
- Avoid trading during challenging astrological periods
- Incorporate cosmic timing into risk management strategies