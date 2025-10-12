# Compatible Data Sources

The TimeSeriesLoader works with any CSV file that has a date column and numeric time series data. Here are some popular sources and how to use them:

## 📈 Yahoo Finance

### Manual Download
1. Go to [finance.yahoo.com](https://finance.yahoo.com)
2. Search for any stock (e.g., AAPL)
3. Click "Historical Data"
4. Set date range and download CSV
5. Use with: `loader.load_csv("AAPL.csv", date_column="Date")`

### Programmatic Download
```python
# Install: pip install yfinance
import yfinance as yf

# Download data
ticker = yf.Ticker("AAPL")
data = ticker.history(period="2y")
data.to_csv("AAPL_2y.csv")

# Load with TimeSeriesLoader
loader = TimeSeriesLoader()
df = loader.load_csv("AAPL_2y.csv", date_column="Date")
```

**Format**: `Date,Open,High,Low,Close,Adj Close,Volume`

## 📊 Alpha Vantage

### API Download
```python
# Install: pip install alpha_vantage
from alpha_vantage.timeseries import TimeSeries

ts = TimeSeries(key='YOUR_API_KEY', output_format='pandas')
data, meta_data = ts.get_daily('AAPL', outputsize='full')
data.to_csv("AAPL_alphavantage.csv")

# Load with TimeSeriesLoader
loader.load_csv("AAPL_alphavantage.csv", date_column="date")
```

**Format**: `timestamp,open,high,low,close,volume`

## 🏦 Federal Reserve Economic Data (FRED)

### Using pandas_datareader
```python
# Install: pip install pandas-datareader
import pandas_datareader as pdr

# Download economic indicators
data = pdr.get_data_fred(['GDP', 'UNRATE'], start='2020-01-01')
data.to_csv("economic_indicators.csv")

# Load with TimeSeriesLoader
loader.load_csv("economic_indicators.csv", value_columns=['GDP', 'UNRATE'])
```

## 🪙 Cryptocurrency Data

### CoinGecko API
```python
# Manual download from coingecko.com or use API
import requests
import pandas as pd

# Example API call
url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
params = {"vs_currency": "usd", "days": "365"}
response = requests.get(url, params=params)
data = response.json()

# Convert to DataFrame
prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
prices['date'] = pd.to_datetime(prices['timestamp'], unit='ms')
prices.to_csv("bitcoin_prices.csv", index=False)

# Load with TimeSeriesLoader
loader.load_csv("bitcoin_prices.csv", date_column="date", value_columns=["price"])
```

## 🌾 Commodity Prices

### Quandl/NASDAQ Data Link
```python
# Install: pip install quandl
import quandl

quandl.ApiConfig.api_key = "YOUR_API_KEY"
data = quandl.get("CHRIS/CME_CL1")  # Crude oil futures
data.to_csv("crude_oil.csv")

# Load with TimeSeriesLoader
loader.load_csv("crude_oil.csv", value_columns=["Last", "Volume"])
```

## 📈 Multi-Asset Portfolio Data

### Creating Combined Dataset
```python
import yfinance as yf

symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
all_data = []

for symbol in symbols:
    data = yf.Ticker(symbol).history(period="1y")
    data['Symbol'] = symbol
    data = data.reset_index()
    all_data.append(data)

portfolio_data = pd.concat(all_data, ignore_index=True)
portfolio_data.to_csv("portfolio_data.csv", index=False)

# Load with symbol grouping
loader = TimeSeriesLoader()
df = loader.load_csv(
    "portfolio_data.csv",
    date_column="Date",
    symbol_column="Symbol",
    value_columns=["Close", "Volume"]
)

segments = loader.create_segments(
    df,
    window_size=30,
    stride=5,
    symbol_column="Symbol"
)
```

## 🏭 Custom Data Formats

The loader is flexible and works with any format. Just specify the column names:

```python
# Example: Custom IoT sensor data
# Format: timestamp,sensor_1,sensor_2,device_id
loader.load_csv(
    "sensor_data.csv",
    date_column="timestamp",
    value_columns=["sensor_1", "sensor_2"],
    symbol_column="device_id"  # Group by device
)

# Example: Weather data
# Format: date,temperature,humidity,pressure
loader.load_csv(
    "weather.csv",
    date_column="date",
    value_columns=["temperature", "humidity", "pressure"]
)
```

## 📝 Data Quality Tips

1. **Date Formats**: The loader auto-detects most date formats (ISO, US, EU)
2. **Missing Data**: Segments with >10% missing values are automatically filtered
3. **Frequency**: Works with any frequency (daily, hourly, minute-level)
4. **Symbols**: Use symbol column for multi-asset or multi-device data
5. **Scaling**: No need to normalize - the FeatureEncoder handles this

## 🚀 Getting Started

1. Download any CSV from the sources above
2. Use `TimeSeriesLoader.load_csv()` with appropriate column names
3. Create segments with `create_segments()`
4. Feed to `FeatureEncoder` for embedding generation

The system is designed to work out-of-the-box with minimal configuration!