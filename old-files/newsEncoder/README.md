# NewsEncoder

A Python package for collecting and encoding financial news, economic events, and macro data for correlation analysis with astronomical patterns.

## Features

- Collect financial news from multiple APIs (NewsAPI, Alpha Vantage, etc.)
- Parse economic calendar events with automatic categorization
- Generate market summaries with indices, currencies, commodities
- Create semantic-searchable text summaries for each day
- Support for batch processing of historical dates
- Easy integration with ChromaDB for similarity search
- Designed to work seamlessly with astroEncoder package

## Installation

1. **Prerequisites:** Python 3.8+ and requests library

2. **Navigate to the project directory:**
```bash
cd /Users/yetang/Development/time-series-indexing
```

3. **Install dependencies:**
```bash
pip install requests
# Optional for testing:
pip install pytest pytest-cov
```

4. **Verify installation:**
```bash
python -c "from newsEncoder import NewsEncoder; print('✓ Package imports successfully')"
```

## Quick Start

### Basic Usage (Works Without API Keys)

```python
from newsEncoder import NewsEncoder
from datetime import datetime, timezone

# Create encoder instance (uses sample data without API keys)
encoder = NewsEncoder()

# Get current financial news
current_news = encoder.get_current_news()

# Print summary
print(f"Date: {current_news.date}")
print(f"Daily Summary: {current_news.daily_summary}")
print(f"Fed Events: {len(current_news.fed_events)}")
print(f"Economic Data: {len(current_news.economic_data)}")

# Get combined summary for search/embedding
search_text = current_news.get_combined_summary()
print(f"Search text: {search_text}")
```

### With API Keys (Real Data)

```python
# Configure with real API keys
config = {
    'newsapi_key': 'your_newsapi_key',
    'alpha_vantage_key': 'your_alpha_vantage_key'
}

encoder = NewsEncoder(config)
current_news = encoder.get_current_news()
```

### Analyze Specific Date

```python
# Analyze January 15, 2024
target_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
news_data = encoder.encode_date(target_date, include_market_data=True)

print(f"Market Regime: {news_data.market_regime}")
print(f"Quality Score: {news_data.quality_score:.1f}/1.0")

# Show market performance
if news_data.market_summary:
    for symbol, change in news_data.market_summary.major_indices.items():
        print(f"{symbol}: {change:+.1f}%")
```

## Running the Code

### 1. Run Basic Examples

```bash
# From project root directory
python newsEncoder/examples/basic_usage.py
```

### 2. Interactive Testing

```bash
python -c "
from newsEncoder import NewsEncoder
encoder = NewsEncoder()
news = encoder.get_current_news()
print('Current News Summary:')
print(news.get_combined_summary())
"
```

### 3. Batch Processing

```bash
python -c "
from newsEncoder import NewsEncoder
from datetime import datetime, timezone, timedelta

encoder = NewsEncoder()
# Get last 3 days
dates = [datetime.now(timezone.utc) - timedelta(days=i) for i in range(3)]
results = encoder.batch_encode_dates(dates)

for news in results:
    print(f'{news.date.strftime(\"%Y-%m-%d\")}: {news.get_combined_summary()}')
"
```

## Running Tests

### Run All Tests
```bash
python -m pytest newsEncoder/tests/ -v
```

### Run Specific Test Files
```bash
# Test the main encoder
python -m pytest newsEncoder/tests/test_encoder.py -v

# Test data models
python -m pytest newsEncoder/tests/test_data_models.py -v
```

### Quick Verification
```bash
# Test basic functionality
python -c "
from newsEncoder import NewsEncoder
encoder = NewsEncoder()
news = encoder.get_current_news()
print(f'✓ NewsEncoder working: {news.quality_score:.1f} quality score')
print(f'✓ Combined summary: {len(news.get_combined_summary())} characters')
"
```

## API Keys Setup

### NewsAPI (Recommended)
1. Sign up at [NewsAPI.org](https://newsapi.org/)
2. Get free API key (30 days historical data)
3. Use in config: `'newsapi_key': 'your_key_here'`

### Alpha Vantage (For Market Data)
1. Sign up at [Alpha Vantage](https://www.alphavantage.co/)
2. Get free API key
3. Use in config: `'alpha_vantage_key': 'your_key_here'`

### Trading Economics (Optional)
1. Sign up at [Trading Economics](https://tradingeconomics.com/api/)
2. Get API key for economic calendar
3. Use in config: `'tradingeconomics_key': 'your_key_here'`

## Data Structure

### Sample Output
```python
{
    "date": "2024-01-15T12:00:00+00:00",
    "daily_summary": "Fed: 1 events | Markets: up 1.2% | Economic data: 2 releases",
    "fed_summary": "Fed holds rates steady at 5.25%",
    "market_regime": "normal_volatility",
    "combined_summary": "Fed: Fed holds rates steady | Markets: SPY +1.2%, QQQ +0.8% | Data: CPI: 3.2%, Retail Sales: 0.6%",
    "quality_score": 0.8,
    "fed_events": [...],
    "economic_data": [...],
    "market_summary": {
        "major_indices": {"SPY": 1.2, "QQQ": 0.8},
        "currencies": {"EUR/USD": -0.3},
        "volatility": {"VIX": 15.2}
    }
}
```

## Integration with ChromaDB

Perfect for similarity search:

```python
import chromadb

# Create collection
client = chromadb.Client()
collection = client.create_collection("financial_news")

# Add daily summaries
encoder = NewsEncoder()
dates = [...]  # List of dates
results = encoder.batch_encode_dates(dates)

for news in results:
    collection.add(
        documents=[news.get_combined_summary()],
        metadatas=[{
            'date': news.date.isoformat(),
            'market_regime': news.market_regime,
            'fed_events': len(news.fed_events)
        }],
        ids=[f"news_{news.date.strftime('%Y%m%d')}"]
    )

# Search for similar market conditions
results = collection.query(
    query_texts=["Fed hiking cycle with market volatility"],
    n_results=5
)
```

## Use Cases

### 1. Astro-Financial Correlation
```python
# Find market conditions during Saturn-Neptune conjunctions
astro_dates = [...]  # Dates from astroEncoder
news_data = encoder.batch_encode_dates(astro_dates)

# Analyze common patterns
for news in news_data:
    if news.market_regime == 'high_volatility':
        print(f"Volatility spike on {news.date}: {news.get_combined_summary()}")
```

### 2. Historical Pattern Search
```python
# Find periods similar to 2008 financial crisis
crisis_query = "banking crisis credit concerns market crash high volatility"
# Use ChromaDB to find similar periods
```

### 3. Fed Cycle Analysis
```python
# Track Fed policy changes
encoder = NewsEncoder()
results = encoder.batch_encode_dates(historical_dates)

fed_periods = [r for r in results if r.fed_events]
for period in fed_periods:
    print(f"{period.date}: {period.fed_summary}")
```

## Example Output

When you run the examples, you should see:

```
CURRENT FINANCIAL NEWS
============================================================
Date: 2025-10-13 23:45:12.345678+00:00
Quality Score: 0.8/1.0

DAILY SUMMARY:
------------------------------
Fed: 1 events | Markets: up 1.2% | Economic data: 2 releases

FED EVENTS:
--------------------
• Fed Officials Signal Cautious Approach to Rate Changes
  Federal Reserve officials indicated a measured approach to monetary policy adjustments.

MARKET SUMMARY:
-------------------------
Indices:
  SPY: +1.2%
  QQQ: +0.8%
  DIA: +0.5%
Currencies:
  EUR/USD: -0.3%
  GBP/USD: +0.1%
Volatility:
  VIX: 15.2

COMBINED SUMMARY (for embedding/search):
---------------------------------------------
Fed: Fed Officials Signal Cautious Approach to Rate Changes | Markets: SPY +1.2%, QQQ +0.8%, DIA +0.5%, VIX 15.2 | Data: Consumer Price Index: 3.2%, Retail Sales: 0.6%
```

## Next Steps

1. **Get API keys** for real financial data
2. **Integrate with ChromaDB** for similarity search
3. **Combine with astroEncoder** for astro-financial correlations
4. **Build historical database** of 50 years of data
5. **Create prediction system** based on pattern matching

The package is designed to work seamlessly with your astroEncoder for complete astro-financial correlation analysis!