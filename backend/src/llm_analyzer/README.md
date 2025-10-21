# LLM Analyzer for Astrological Trading Insights

This module provides comprehensive analysis of oil futures trading opportunities using astrological data and Claude AI.

## Overview

The LLM Analyzer takes all trading opportunities with astrological data from the database and generates comprehensive prompts for Claude AI to identify profitable astrological patterns in oil futures trading.

## Key Features

- **Data Retrieval**: Automatically fetches all trading opportunities with astrological analysis
- **Intelligent Prompts**: Generates specialized prompts for different types of analysis
- **Claude Integration**: Uses Claude AI for pattern recognition and insight generation
- **Multiple Analysis Types**: Comprehensive, lunar phases, planetary aspects, trading calendar
- **Actionable Insights**: Produces specific trading rules and recommendations

## Directory Structure

```
llm_analyzer/
├── __init__.py
├── README.md
├── core/
│   ├── __init__.py
│   ├── analyzer.py          # Main orchestrator
│   ├── claude_analyzer.py   # Claude API integration
│   └── data_retriever.py    # Database data retrieval
├── models/
│   ├── __init__.py
│   └── trading_data.py      # Data models
└── prompts/
    ├── __init__.py
    └── oil_trading_prompts.py # Specialized prompts
```

## Usage

### 1. Local Testing (No Claude API required)

```bash
cd backend
python3 scripts/llm_analysis/test_local_analysis.py
```

This tests data retrieval and prompt generation without requiring Claude API.

### 2. Run Specific Analysis Types

```bash
# Quick insights
python3 scripts/llm_analysis/run_oil_astro_analysis.py --analysis-type quick

# Lunar phase analysis
python3 scripts/llm_analysis/run_oil_astro_analysis.py --analysis-type lunar

# Planetary aspects analysis
python3 scripts/llm_analysis/run_oil_astro_analysis.py --analysis-type aspects

# Trading calendar
python3 scripts/llm_analysis/run_oil_astro_analysis.py --analysis-type calendar

# Full comprehensive report
python3 scripts/llm_analysis/run_oil_astro_analysis.py --analysis-type full-report
```

### 3. Kubernetes Deployment

```bash
# Ensure Claude API key is in secrets
kubectl patch secret market-encoder-secrets -n time-series-indexing \
  --patch='{"data":{"anthropic-api-key":"'$(echo -n "YOUR_API_KEY" | base64)'"}}'

# Run comprehensive analysis
kubectl apply -f deploy/k8s/shared/claude-oil-analysis-job.yaml
kubectl logs -f job/claude-oil-astro-analysis -n time-series-indexing
```

## Analysis Types

### 1. Comprehensive Analysis
- Analyzes all profitable trades with complete astrological data
- Identifies top astrological indicators for oil trading
- Generates practical trading rules
- Creates risk management guidelines

### 2. Lunar Phase Analysis
- Focuses specifically on lunar cycle correlations
- Identifies optimal phases for long vs. short positions
- Analyzes holding period patterns based on lunar cycles

### 3. Planetary Aspects Analysis
- Examines specific planetary aspect patterns
- Correlates Mars, Jupiter, Saturn aspects with oil price movements
- Identifies aspect combinations that signal profitable trades

### 4. Trading Calendar
- Creates month-by-month astrological trading guidance
- Identifies seasonal patterns in oil price movements
- Provides daily reference for astrological timing

### 5. Quick Insights
- Rapid analysis of top-scoring trades
- Immediate actionable recommendations
- Concise trading rules for quick reference

## Configuration

### Environment Variables

```bash
# Database connection
DB_HOST=your-postgres-host
DB_PORT=5432
DB_NAME=your-database
DB_USER=your-username
DB_PASSWORD=your-password

# Claude API
ANTHROPIC_API_KEY=your-claude-api-key
```

### Command Line Options

```bash
--analysis-type      # Type of analysis (comprehensive, quick, lunar, aspects, calendar, full-report)
--min-astro-score    # Minimum astrological score to include (0-100)
--output-dir         # Output directory for results
--claude-api-key     # Claude API key (optional if env var set)
--verbose            # Enable verbose logging
```

## Sample Output

The system generates comprehensive analyses like:

### Top Astrological Indicators
1. **Mars-Jupiter Trines**: 85% success rate in oil trades
2. **Full Moon Phases**: 15% higher average profits
3. **Sun in Fire Signs**: Favors oil price increases
4. **Saturn Aspects**: Signal market restrictions

### Practical Trading Rules
- Enter long oil positions during Waxing Moon with Mars in fire signs
- Exit profitable trades when lunar phase changes from Full to Waning
- Avoid trading during Mercury retrograde in earth signs
- Increase position size when Jupiter aspects are exact

### Risk Management
- High volatility expected during Mars-Saturn squares
- Trend reversals likely when Sun changes signs during Full Moon
- Reduce exposure during eclipse periods

## Integration with Existing System

The LLM Analyzer seamlessly integrates with:
- **Trading Opportunities Database**: Uses existing astrological analysis data
- **Swiss Ephemeris System**: Leverages planetary position calculations
- **Market Encoder**: Works with oil futures data structure
- **Kubernetes Infrastructure**: Deploys as standard jobs

## Error Handling

- Graceful fallback when Claude API is unavailable
- Comprehensive logging for debugging
- Validation of data integrity before analysis
- Retry logic for API failures

## Future Enhancements

- Additional LLM providers (GPT-4, Gemini)
- Real-time analysis integration
- Portfolio-level astrological analysis
- Integration with trading execution systems
- Machine learning pattern validation